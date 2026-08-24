from datetime import datetime, timezone

from global_x_finance.ben_radar import (
    NEWS_SOURCES,
    cluster_news,
    format_trade_value,
    format_volume_lots,
    parse_rss,
)
from global_x_finance.webapp import create_app


def test_finance_numbers_are_human_readable():
    assert format_volume_lots(54_418_832) == "5.44萬張"
    assert format_volume_lots(8_500_000) == "8,500張"
    assert format_trade_value(54_418_832_121) == "新台幣544.19億元"


def test_rss_requires_real_title_time_and_link():
    payload = b"""<?xml version='1.0'?><rss><channel>
      <item><title>SYNTHETIC_TEST_DATA market update</title>
      <link>https://example.test/news/1</link>
      <pubDate>Sun, 16 Aug 2026 06:00:00 GMT</pubDate>
      <description>Evidence summary</description></item>
      <item><title>Missing link is invalid</title></item>
    </channel></rss>"""

    items = parse_rss(payload)

    assert len(items) == 1
    assert items[0]["url"] == "https://example.test/news/1"
    assert items[0]["published_at"].startswith("2026-08-16T06:00:00")


def test_news_pool_has_multiple_independent_taiwan_publishers():
    taiwan_publishers = {
        row["publisher_group"] for row in NEWS_SOURCES if row["market"] == "TW"
    }

    assert {
        "yahoo", "cna", "moneydj", "udn_money", "ettoday", "technews"
    }.issubset(taiwan_publishers)
    assert len({row["source_id"] for row in NEWS_SOURCES}) == len(NEWS_SOURCES)


def test_similar_reprints_cluster_once():
    published = datetime(2026, 8, 16, 6, tzinfo=timezone.utc).isoformat()
    rows = [
        {"original_title": "Nvidia AI chip demand rises sharply", "published_at": published},
        {"original_title": "Nvidia AI chip demand rises", "published_at": published},
        {"original_title": "Federal Reserve rate outlook", "published_at": published},
    ]

    clusters = cluster_news(rows)

    assert len(clusters) == 2
    assert sorted(len(cluster["items"]) for cluster in clusters) == [1, 2]


def test_ai_radar_navigation_and_empty_states(database_path, root):
    app = create_app(database_path, root / "config" / "twse_openapi.datasets.json")
    app.config["TESTING"] = True

    with app.test_client() as client:
        home = client.get("/")
        taiwan = client.get("/ai-radar")
        stock_alias = client.get("/stock-radar?window=6&category=ai&sort=discussion")
        source_health = client.get("/radar")

    assert home.status_code == 200
    assert "BEN 財經熱點雷達" in home.get_data(as_text=True)
    assert taiwan.status_code == 200
    html = taiwan.get_data(as_text=True)
    assert "ben-stock-workbench.v0.1" in html
    assert "market-anomaly-grid" in html
    assert "ben-stock-radar.topic-queue.v1" in html
    assert "Yahoo Finance 兩個實際入口" not in html
    assert stock_alias.status_code == 200
    assert "ben-stock-workbench.v0.1" in stock_alias.get_data(as_text=True)
    assert source_health.status_code == 200
    assert "BEN Radar 新聞來源" in source_health.get_data(as_text=True)


def test_cluster_diagnostics_and_ben_test_mode(database_path, root):
    app = create_app(database_path, root / "config" / "twse_openapi.datasets.json")
    app.config["TESTING"] = True
    with app.test_client() as client:
        diagnostics = client.get("/stock-radar/cluster-diagnostics")
        ben_test = client.get("/stock-radar?test=ben")
    assert diagnostics.status_code == 200
    assert "事件聚類診斷" in diagnostics.get_data(as_text=True)
    html = ben_test.get_data(as_text=True)
    assert "ben-stock-radar.ben-test.v1" in html
    assert "test_start" in html
    assert "evidence_open" in html
    assert "topic_saved" in html
