from __future__ import annotations

import sqlite3
import json

import pytest

from global_x_finance.content_studio import (
    WEIGHT_SECURITIES,
    archive_workbench_channels,
    build_content_studio_payload,
    build_weight_topics,
    ensure_topic_contract,
    write_content_studio_payload,
)


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE official_securities (
            id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL
        );
        CREATE TABLE official_market_data_daily (
            security_id TEXT NOT NULL,
            trade_date TEXT NOT NULL,
            closing_price TEXT,
            price_change TEXT,
            trade_volume INTEGER,
            trade_value INTEGER,
            data_status TEXT NOT NULL,
            source_id TEXT NOT NULL
        );
        """
    )
    for index, security_id in enumerate(WEIGHT_SECURITIES, start=1):
        connection.execute(
            "INSERT INTO official_securities (id, company_name) VALUES (?, ?)",
            (security_id, f"公司{index}"),
        )
        connection.execute(
            """INSERT INTO official_market_data_daily
               (security_id, trade_date, closing_price, price_change,
                trade_volume, trade_value, data_status, source_id)
               VALUES (?, '2026-08-20', ?, ?, ?, ?, 'EOD', 'TWSE')""",
            (
                security_id,
                str(100 + index),
                "+1.00" if index % 2 else "-1.00",
                index * 1_000,
                index * 100_000_000,
            ),
        )
    connection.commit()
    return connection


def test_weight_topics_are_complete_and_ranked_by_trade_value() -> None:
    connection = _connection()
    topics = build_weight_topics(connection, "2026-08-20")

    assert len(topics) == 5
    assert [topic["candidate_rank"] for topic in topics] == [1, 2, 3, 4, 5]
    assert topics[0]["security_ids"] == [WEIGHT_SECURITIES[-1]]
    assert topics[0]["evidence"][0]["evidence_class"] == "OFFICIAL_EOD"
    assert all("不等同完整指數貢獻排名" in topic["why_channel"][0] for topic in topics)


def test_weight_topics_fail_closed_when_one_eod_row_is_missing() -> None:
    connection = _connection()
    connection.execute(
        "DELETE FROM official_market_data_daily WHERE security_id=?",
        (WEIGHT_SECURITIES[0],),
    )

    with pytest.raises(ValueError, match="missing 2026-08-20 EOD rows"):
        build_weight_topics(connection, "2026-08-20")


def test_content_studio_payload_rejects_replay() -> None:
    connection = _connection()
    brief = {
        "market_session_date": "2026-08-20",
        "replay_mode": True,
        "session_state": "READY",
        "ranking_method": "RULE_BASED_FALLBACK",
    }

    with pytest.raises(ValueError, match="replay_mode=false"):
        build_content_studio_payload(connection, brief)


def test_daily_write_preserves_dated_channel_workbenches(tmp_path) -> None:
    database_path = tmp_path / "studio.db"
    source = _connection()
    destination = sqlite3.connect(database_path)
    source.backup(destination)
    destination.close()
    source.close()

    brief_path = tmp_path / "brief.json"
    brief_path.write_text(
        json.dumps(
            {
                "market_session_date": "2026-08-20",
                "replay_mode": False,
                "session_state": "READY",
                "ranking_method": "RULE_BASED_FALLBACK",
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "data.json"
    output_path.write_text(
        json.dumps(
            {
                "first_ten_workbench": {
                    "source_snapshot_date": "2026-08-23",
                    "channel_count": 10,
                },
                "channel_workbench": {
                    "source_snapshot_date": "2026-08-23",
                    "channel_count": 20,
                }
            }
        ),
        encoding="utf-8",
    )

    payload = write_content_studio_payload(
        database_path=database_path,
        brief_path=brief_path,
        output_path=output_path,
    )

    assert payload["first_ten_workbench"]["source_snapshot_date"] == "2026-08-23"
    assert payload["first_ten_workbench"]["channel_count"] == 10
    assert payload["channel_workbench"]["source_snapshot_date"] == "2026-08-23"
    assert payload["channel_workbench"]["channel_count"] == 20


def _close_talk_editorial(script_length: int = 3000) -> dict:
    return {
        "status": "DRAFT_FOR_HUMAN_REVIEW",
        "market_session_date": "2026-08-20",
        "angles": [
            {
                "rank": rank,
                "title_options": [f"標題{rank}A", f"標題{rank}B"],
                "why_today": f"今日理由{rank}",
                "why_this_channel": "符合收盤夜話定位",
                "confirmed_facts": [{"text": f"事實{rank}"}],
                "unknowns": ["未知資料"],
                "source_cards": [],
                "script": {
                    "full_text": "稿" * script_length,
                    "character_count": script_length,
                },
            }
            for rank in range(1, 6)
        ],
    }


def test_daily_write_replaces_visible_close_talk_with_current_five_scripts(tmp_path) -> None:
    database_path = tmp_path / "studio.db"
    source = _connection()
    destination = sqlite3.connect(database_path)
    source.backup(destination)
    destination.close()
    source.close()

    brief_path = tmp_path / "brief.json"
    brief_path.write_text(
        json.dumps(
            {
                "market_session_date": "2026-08-20",
                "replay_mode": False,
                "session_state": "READY",
                "ranking_method": "RULE_BASED_FALLBACK",
            }
        ),
        encoding="utf-8",
    )
    editorial_path = tmp_path / "editorial.json"
    editorial_path.write_text(
        json.dumps(_close_talk_editorial(), ensure_ascii=False),
        encoding="utf-8",
    )
    output_path = tmp_path / "data.json"
    output_path.write_text(
        json.dumps(
            {
                "channel_workbench": {
                    "source_snapshot_date": "2026-08-23",
                    "last_market_session_date": "2026-08-19",
                    "channel_count": 20,
                    "channels": [
                        {
                            "channel_name": "收盤夜話",
                            "content_date": "2026-08-19",
                            "topics": [{"title": "舊稿"}],
                        }
                    ],
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = write_content_studio_payload(
        database_path=database_path,
        brief_path=brief_path,
        output_path=output_path,
        close_talk_editorial_path=editorial_path,
    )

    workbench = payload["channel_workbench"]
    channel = workbench["channels"][0]
    assert workbench["last_market_session_date"] == "2026-08-20"
    assert channel["content_date"] == "2026-08-20"
    assert len(channel["topics"]) == 5
    assert all(topic["script_character_count"] >= 3000 for topic in channel["topics"])
    assert all(topic["script_meets_target"] is True for topic in channel["topics"])
    assert all(topic["manuscript_alignment"]["status"] == "PASS" for topic in channel["topics"])
    assert all(topic["script_text"].endswith("稿" * 3000) for topic in channel["topics"])


def test_daily_write_rejects_short_close_talk_manuscript(tmp_path) -> None:
    database_path = tmp_path / "studio.db"
    source = _connection()
    destination = sqlite3.connect(database_path)
    source.backup(destination)
    destination.close()
    source.close()

    brief_path = tmp_path / "brief.json"
    brief_path.write_text(
        json.dumps(
            {
                "market_session_date": "2026-08-20",
                "replay_mode": False,
                "session_state": "READY",
                "ranking_method": "RULE_BASED_FALLBACK",
            }
        ),
        encoding="utf-8",
    )
    editorial_path = tmp_path / "editorial.json"
    editorial_path.write_text(
        json.dumps(_close_talk_editorial(2999), ensure_ascii=False),
        encoding="utf-8",
    )
    output_path = tmp_path / "data.json"
    output_path.write_text(
        json.dumps(
            {
                "channel_workbench": {
                    "source_snapshot_date": "2026-08-23",
                    "channel_count": 20,
                    "channels": [{"channel_name": "收盤夜話", "topics": []}],
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="3000 required"):
        write_content_studio_payload(
            database_path=database_path,
            brief_path=brief_path,
            output_path=output_path,
            close_talk_editorial_path=editorial_path,
        )


def _history_workbench(script_text: str = "測試標題選題理由事實一") -> dict:
    topic = {
        "candidate_id": "history-topic-1",
        "title": "測試標題",
        "title_options": ["測試標題", "測試標題備選"],
        "why_now": ["今天出現一項具體新變化"],
        "why_channel": ["這個頻道能用固定資料維度驗證"],
        "facts": ["事實一"],
        "unknowns": ["後續結果尚未取得"],
        "evidence": [
            {
                "source_id": "OFFICIAL",
                "human_verification_url": "https://example.com/evidence",
            }
        ],
        "script_text": script_text,
    }
    ensure_topic_contract("收盤夜話", topic)
    return {
        "channels": [
            {
                "channel_id": "ch-02-tw-close-night-talk",
                "channel_name": "收盤夜話",
                "content_date": "2026-08-21",
                "topics": [topic],
            }
        ]
    }


def test_channel_history_is_append_only_and_idempotent(tmp_path) -> None:
    first = archive_workbench_channels(_history_workbench(), tmp_path)
    second = archive_workbench_channels(first, tmp_path)

    assert first["history_entry_count"] == 1
    assert second["history_entry_count"] == 1
    history_path = tmp_path / first["channel_history_index"][0]["path"]
    assert history_path.is_file()
    artifact = json.loads(history_path.read_text(encoding="utf-8"))
    assert artifact["channel"]["topics"][0]["script_text"] == "測試標題選題理由事實一"
    assert artifact["channel"]["topics"][0]["outcome_review"]["status"] == "PENDING_DATA"


def test_same_date_changed_channel_creates_a_new_history_version(tmp_path) -> None:
    first = archive_workbench_channels(_history_workbench(), tmp_path)
    changed = _history_workbench("測試標題選題理由事實一第二版")
    changed["channel_history_index"] = first["channel_history_index"]
    second = archive_workbench_channels(changed, tmp_path)

    assert second["history_entry_count"] == 2
    assert len({row["path"] for row in second["channel_history_index"]}) == 2
