from datetime import datetime
import sqlite3

from global_x_finance.close_talk_fact_pack import (
    TAIPEI,
    _market_activity_leaders,
    _source_diverse,
    _within_window,
)


def test_fact_pack_window_rejects_future_and_old_evidence():
    start = datetime.fromisoformat("2026-08-18T14:00:00+08:00")
    end = datetime.fromisoformat("2026-08-20T14:00:00+08:00")

    assert _within_window("2026-08-19T06:00:00+00:00", start=start, end=end)
    assert not _within_window("2026-08-18T05:59:59+00:00", start=start, end=end)
    assert not _within_window("2026-08-20T06:00:01+00:00", start=start, end=end)


def test_source_diversity_caps_one_publisher_without_reordering():
    rows = [
        {"id": 1, "source": "a"},
        {"id": 2, "source": "a"},
        {"id": 3, "source": "b"},
        {"id": 4, "source": "a"},
        {"id": 5, "source": "c"},
    ]

    selected = _source_diverse(rows, limit=4, group_field="source", per_group=2)

    assert [row["id"] for row in selected] == [1, 2, 3, 5]


def test_market_activity_leaders_are_ranked_and_traceable():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE official_securities (
            id TEXT PRIMARY KEY, company_name TEXT NOT NULL
        );
        CREATE TABLE official_market_data_daily (
            security_id TEXT, exchange_code TEXT, ticker TEXT, trade_date TEXT,
            opening_price TEXT, highest_price TEXT, lowest_price TEXT,
            closing_price TEXT, price_change TEXT, trade_volume INTEGER,
            trade_value INTEGER, transaction_count INTEGER, source_id TEXT,
            data_status TEXT
        );
        INSERT INTO official_securities VALUES
            ('TWSE:2408', '南亞科'), ('TWSE:2344', '華邦電');
        INSERT INTO official_market_data_daily VALUES
            ('TWSE:2344','TWSE','2344','2026-08-20','170','180','169','176.5','8.5',100,200,10,'TW-A02','EOD'),
            ('TWSE:2408','TWSE','2408','2026-08-20','490','523','488','517','36',200,400,20,'TW-A02','EOD');
        """
    )

    rows = _market_activity_leaders(connection, trade_date="2026-08-20", limit=2)

    assert [row["security_id"] for row in rows] == ["TWSE:2408", "TWSE:2344"]
    assert rows[0]["change_pct"] == 7.48
    assert rows[0]["evidence_id"] == "OFFICIAL_EOD:TWSE:2408:2026-08-20"
    assert rows[0]["source_url"].startswith("https://www.twse.com.tw/")
