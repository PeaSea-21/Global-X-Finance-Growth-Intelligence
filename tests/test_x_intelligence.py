from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from global_x_finance.webapp import create_app
from global_x_finance import x_intelligence
from global_x_finance.x_intelligence import (
    HttpResult,
    account_counts,
    build_unified_events,
    cluster_quality_report,
    collect_x_accounts_once,
    filter_time_window,
    fetch_x_page,
    load_x_accounts,
    publisher_group_for_handle,
)


NOW = datetime(2026, 8, 16, 8, 0, tzinfo=timezone.utc)


def _x_row(post_id: str, *, group: str, text: str, created_at: str, repost: bool = False, url: str = "https://example.test/evidence") -> dict:
    return {
        "post_id": post_id,
        "author_handle": f"synthetic_{post_id}",
        "author_name": "SYNTHETIC_TEST_DATA",
        "publisher_group": group,
        "account_role": "官方公司",
        "account_priority": "CORE",
        "original_text": text,
        "original_language": "en",
        "created_at": created_at,
        "original_url": f"https://x.com/synthetic/status/{post_id}",
        "likes": 10,
        "reposts": 2,
        "quotes": 1,
        "replies": 1,
        "views": 100,
        "follower_count": 10_000,
        "external_urls_json": json.dumps([url]),
        "is_repost": int(repost),
    }


def test_real_csv_has_exact_expected_account_counts(root):
    accounts = load_x_accounts(root / "config" / "x_accounts.csv")
    assert account_counts(accounts) == {"total": 67, "core": 19, "watch": 40, "low_confidence": 8}
    assert {account.handle for account in accounts} >= {"nvidia", "mingchikuo", "ChatGPT"}
    assert "ChatGPTapp" not in {account.handle for account in accounts}


def test_x_since_checkpoint_is_sent_as_milliseconds(monkeypatch, root):
    account = load_x_accounts(root / "config" / "x_accounts.csv")[0]
    captured = {}

    def fake_http_get(url, timeout=35):
        captured["url"] = url
        return HttpResult(204, b"", {}, url)

    monkeypatch.setattr(x_intelligence, "_http_get", fake_http_get)
    fetch_x_page(account, 1_700_000_000)
    assert "since=1700000000000" in captured["url"]


def test_x_collection_paginates_until_it_crosses_the_24h_window(database, root):
    account = load_x_accounts(root / "config" / "x_accounts.csv")[0]
    recent = {
        "id": "recent-page-1",
        "text": "SYNTHETIC_TEST_DATA recent NVIDIA AI update",
        "created_at": (NOW - timedelta(minutes=10)).isoformat(),
        "author": {"screen_name": account.handle, "name": account.display_name},
    }
    old = {
        "id": "old-page-2",
        "text": "SYNTHETIC_TEST_DATA old NVIDIA AI update",
        "created_at": (NOW - timedelta(hours=25)).isoformat(),
        "author": {"screen_name": account.handle, "name": account.display_name},
    }
    cursor_calls = []

    def fetcher(_account, _since):
        return HttpResult(
            200,
            json.dumps({"results": [recent], "cursor": {"bottom": "next"}}).encode(),
            {},
            "https://api.fxtwitter.com/test",
        )

    def cursor_fetcher(_account, cursor):
        cursor_calls.append(cursor)
        return HttpResult(
            200,
            json.dumps({"results": [old], "cursor": {}}).encode(),
            {},
            "https://api.fxtwitter.com/test?cursor=next",
        )

    results = collect_x_accounts_once(
        database,
        [account],
        now=NOW,
        force=True,
        cursor_fetcher=cursor_fetcher,
        fetcher=fetcher,
        sleeper=lambda _seconds: None,
    )
    assert cursor_calls == ["next"]
    assert results[0].status == "SUCCESS"
    assert results[0].fetched_count == 2
    assert results[0].kept_count == 1
    assert results[0].new_count == 1


def test_2h_and_24h_boundaries_use_original_timestamp():
    rows = [
        {"id": "2h-edge", "published_at": (NOW - timedelta(hours=2)).isoformat()},
        {"id": "2h-old", "published_at": (NOW - timedelta(hours=2, seconds=1)).isoformat()},
        {"id": "24h-edge", "published_at": (NOW - timedelta(hours=24)).isoformat()},
        {"id": "24h-old", "published_at": (NOW - timedelta(hours=24, seconds=1)).isoformat()},
        {"id": "missing", "published_at": None, "fetched_at": NOW.isoformat()},
        {"id": "future", "published_at": (NOW + timedelta(minutes=1)).isoformat()},
    ]
    two = {row["id"] for row in filter_time_window(rows, now=NOW, hours=2, field="published_at")}
    day = {row["id"] for row in filter_time_window(rows, now=NOW, hours=24, field="published_at")}
    assert two == {"2h-edge"}
    assert day == {"2h-edge", "2h-old", "24h-edge"}
    assert two <= day


def test_x_post_id_is_idempotent_and_only_updates_snapshot(database, root):
    account = load_x_accounts(root / "config" / "x_accounts.csv")[0]
    item = {
        "id": "synthetic-post-001",
        "text": "SYNTHETIC_TEST_DATA TSMC announces AI chip partnership",
        "created_at": (NOW - timedelta(minutes=20)).isoformat(),
        "url": "https://x.com/synthetic/status/synthetic-post-001",
        "lang": "en",
        "likes": 4,
        "reposts": 1,
        "quotes": 0,
        "replies": 1,
        "author": {"screen_name": account.handle, "name": account.display_name, "followers": 1000},
    }

    def fetcher(_account, _since):
        return HttpResult(200, json.dumps({"results": [item]}).encode(), {}, "https://api.fxtwitter.com/test")

    first = collect_x_accounts_once(database, [account], now=NOW, force=True, fetcher=fetcher, sleeper=lambda _seconds: None)
    second = collect_x_accounts_once(database, [account], now=NOW + timedelta(minutes=1), force=True, fetcher=fetcher, sleeper=lambda _seconds: None)
    assert first[0].new_count == 1
    assert second[0].new_count == 0
    assert second[0].duplicate_count == 1
    assert database.execute("SELECT COUNT(*) FROM ben_x_posts WHERE post_id='synthetic-post-001'").fetchone()[0] == 1
    assert database.execute("SELECT COUNT(*) FROM ben_x_engagement_snapshots WHERE post_id='synthetic-post-001'").fetchone()[0] == 2


def test_distinct_x_posts_with_identical_text_keep_distinct_raw_evidence(database, root):
    account = load_x_accounts(root / "config" / "x_accounts.csv")[0]
    shared_text = "SYNTHETIC_TEST_DATA identical syndicated headline"

    def item(post_id: str) -> dict:
        return {
            "id": post_id,
            "text": shared_text,
            "created_at": (NOW - timedelta(minutes=20)).isoformat(),
            "url": f"https://x.com/synthetic/status/{post_id}",
            "lang": "en",
            "likes": 4,
            "reposts": 1,
            "quotes": 0,
            "replies": 1,
            "author": {
                "screen_name": account.handle,
                "name": account.display_name,
                "followers": 1000,
            },
        }

    first_item = item("same-text-post-1")
    second_item = item("same-text-post-2")

    first = collect_x_accounts_once(
        database,
        [account],
        now=NOW,
        force=True,
        fetcher=lambda _account, _since: HttpResult(
            200, json.dumps({"results": [first_item]}).encode(), {}, "https://api.fxtwitter.com/test"
        ),
        sleeper=lambda _seconds: None,
    )
    second = collect_x_accounts_once(
        database,
        [account],
        now=NOW + timedelta(minutes=1),
        force=True,
        fetcher=lambda _account, _since: HttpResult(
            200, json.dumps({"results": [second_item]}).encode(), {}, "https://api.fxtwitter.com/test"
        ),
        sleeper=lambda _seconds: None,
    )

    assert first[0].new_count == second[0].new_count == 1
    rows = database.execute(
        "SELECT post_id, raw_item_id FROM ben_x_posts WHERE post_id LIKE 'same-text-post-%'"
    ).fetchall()
    assert len(rows) == 2
    assert len({row["raw_item_id"] for row in rows}) == 2


def test_repost_does_not_add_independent_publisher():
    created = (NOW - timedelta(minutes=30)).isoformat()
    rows = [
        _x_row("1", group="nvidia", text="NVIDIA announces AI chip launch", created_at=created),
        _x_row("2", group="observer", text="Repost NVIDIA announces AI chip launch", created_at=created, repost=True),
    ]
    events = build_unified_events([], rows, now=NOW)
    assert len(events) == 1
    assert events[0]["independent_count"] == 1
    assert events[0]["x_count"] == 1


def test_publisher_group_required_mappings():
    assert publisher_group_for_handle("nvidia") == publisher_group_for_handle("NVIDIAAI") == "nvidia"
    assert publisher_group_for_handle("OpenAINewsroom") == publisher_group_for_handle("OpenAIDevs") == "openai"
    assert publisher_group_for_handle("AnthropicAI") == publisher_group_for_handle("claudeai") == publisher_group_for_handle("DarioAmodei") == "anthropic"


def test_news_and_x_cluster_only_when_event_evidence_matches():
    created = (NOW - timedelta(minutes=45)).isoformat()
    news = [{
        "id": "news-1", "source_key": "cnbc", "source_name": "CNBC",
        "original_title": "TSMC announces AI chip partnership", "published_at": created,
        "original_url": "https://example.test/evidence", "market": "US", "language": "en",
    }]
    x_rows = [_x_row("3", group="openai", text="TSMC announces AI chip partnership", created_at=created)]
    events = build_unified_events(news, x_rows, now=NOW)
    assert len(events) == 1
    assert events[0]["type"] == "NEWS_X"
    assert events[0]["score"] <= 100
    assert events[0]["news_count"] == 1
    assert events[0]["x_count"] == 1
    assert events[0]["display_title_zh"] == "台積電：產品或技術發布出現新進展"
    assert events[0]["translation_status"] == "TRANSLATION_UNAVAILABLE"
    assert events[0]["evidence_score"] == 25
    assert events[0]["event_id"].startswith("evt_")


def test_semantic_cluster_is_stable_and_does_not_merge_unrelated_company_events():
    created = (NOW - timedelta(minutes=45)).isoformat()
    news = [
        {"id": "n1", "source_key": "investing", "source_name": "Investing.com", "original_title": "Nvidia weighs $3 billion investment in SB Energy AI data center", "published_at": created, "original_url": "https://example.test/n1", "market": "US", "language": "en"},
        {"id": "n2", "source_key": "cnbc", "source_name": "CNBC", "original_title": "Nvidia in talks to invest $3 billion in SB Energy data center", "published_at": created, "original_url": "https://example.test/n2", "market": "US", "language": "en"},
        {"id": "n3", "source_key": "cnbc", "source_name": "CNBC", "original_title": "Nvidia earnings guidance lifts chip shares", "published_at": created, "original_url": "https://example.test/n3", "market": "US", "language": "en"},
    ]
    first = build_unified_events(news, [], now=NOW)
    second = build_unified_events(list(reversed(news)), [], now=NOW)
    assert sorted(len(event["items"]) for event in first) == [1, 2]
    assert {event["event_id"] for event in first} == {event["event_id"] for event in second}
    quality = cluster_quality_report(first, raw_news_count=3, raw_x_count=0)
    assert quality["compression_rate"] == 0.3333
    assert quality["multi_item_events"] == 1
    assert quality["multi_publisher_events"] == 1


def test_english_fallback_never_promotes_original_text_as_homepage_title():
    created = (NOW - timedelta(minutes=20)).isoformat()
    rows = [_x_row("fallback", group="observer", text="Company announces a contract", created_at=created)]
    events = build_unified_events([], rows, now=NOW)
    assert events[0]["display_title_zh"] != rows[0]["original_text"]
    assert events[0]["title_method"] in {"規則中文摘要", "待人工補充"}
    assert "中文摘要生成中" not in events[0]["display_title_zh"]
    assert any("\u4e00" <= character <= "\u9fff" for character in events[0]["summary_zh"])


def test_macro_relationship_is_explicit_without_inventing_tickers():
    created = (NOW - timedelta(minutes=20)).isoformat()
    rows = [_x_row(
        "macro-link", group="observer",
        text="NVIDIA and Apple react to Federal Reserve interest rate outlook",
        created_at=created,
    )]
    event = build_unified_events([], rows, now=NOW)[0]
    relationships = {row["ticker"]: row["relationship"] for row in event["related_stocks"]}
    assert relationships == {"AAPL": "MACRO", "NVDA": "DIRECT"}


def test_traditional_and_simplified_ui_switch(database_path, root):
    app = create_app(database_path, root / "config" / "twse_openapi.datasets.json")
    app.config["TESTING"] = True
    with app.test_client() as client:
        traditional = client.get("/ai-radar?lang=zh-tw")
        simplified = client.get("/ai-radar?lang=zh-cn")
    assert traditional.status_code == simplified.status_code == 200
    assert "資料源狀態" in traditional.get_data(as_text=True)
    assert "数据源状态" in simplified.get_data(as_text=True)
    assert "繁體中文" in traditional.get_data(as_text=True)
    assert "简体中文" in simplified.get_data(as_text=True)
