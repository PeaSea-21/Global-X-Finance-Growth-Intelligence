from __future__ import annotations

import json

from global_x_finance.webapp import create_app


def _payload(title: str, *, version: int) -> dict:
    briefs = []
    for index, (channel_id, channel_name, channel_type) in enumerate((
        ("ch-05-tw-capital-radar", "資金雷達", "SIGNAL_HEAVY"),
        ("ch-01-tw-stock-microscope", "個股顯微鏡", "EVENT_HEAVY"),
        ("ch-03-tw-industry-lens", "產業透視鏡", "CROSS_ENTITY"),
    )):
        item = {
            "candidate_id": f"candidate-{version}-{index}", "candidate_type": "MARKET_SIGNAL" if index < 2 else "CROSS_ENTITY",
            "candidate_rank": 1, "candidate_tier": "PRIMARY", "editorial_status": "NEEDS_RESEARCH",
            "title": f"{title}-{channel_name}", "why_now": ["今日收盤異動"], "why_channel": ["符合頻道"],
            "ranking_reasons": ["規則排序"], "facts": ["收盤100"], "unknowns": ["催化劑未確認"],
            "evidence": [{"url": "https://example.test/evidence", "evidence_class": "OFFICIAL_EOD", "source_id": "TW-A01", "trade_date": "2026-08-17"}],
            "opinion_evidence": [], "security_ids": ["TWSE:2330"], "industry_keys": [], "risk_flags": ["NOT_INVESTMENT_ADVICE"],
            "stock_details": [{"name": "台積電", "security_id": "TWSE:2330", "close": 100, "change_pct": 1.2, "current_volume": 3000000, "median_volume_20d": 1000000, "volume_ratio": 3, "matched_rules": ["VOLUME_SPIKE"]}],
        }
        briefs.append({
            "channel_id": channel_id, "channel_name": channel_name, "channel_type": channel_type,
            "summary": "測試摘要", "fixed_boundary": "測試邊界", "target_count": 5,
            "qualified_count": 1, "displayed_count": 1, "status": "HONEST_SHORTAGE",
            "shortage_reasons": ["QUALIFIED_CANDIDATES_BELOW_TARGET"], "assignments": [item],
        })
    return {
        "artifact_version": "p06b-v0.1", "market_session_date": "2026-08-17", "data_as_of": "2026-08-17T15:05:00+08:00",
        "scheduled_for": "2026-08-17T15:05:00+08:00", "session_state": "DEGRADED", "coverage_status": "OPTIONAL_SOURCE_GAPS",
        "ranking_method": "RULE_BASED_FALLBACK", "briefs": briefs,
        "source_readiness": [{"source": "TWSE_EOD", "status": "READY"}],
    }


def _insert_run(database, payload: dict, *, run_id: str, fingerprint: str, created_at: str):
    database.execute(
        """INSERT INTO ben_channel_brief_runs (
               id, market, market_session_date, session_state, scheduled_for, generated_at,
               data_as_of, replay_mode, source_readiness_json, coverage_status, ranking_method,
               ranking_detail_json, config_version, input_fingerprint, payload_json, created_at
           ) VALUES (?, 'TW', '2026-08-17', 'DEGRADED', ?, ?, ?, 1, '[]',
                     'OPTIONAL_SOURCE_GAPS', 'RULE_BASED_FALLBACK', '{}', 'test', ?, ?, ?)""",
        (
            run_id, payload["scheduled_for"], payload["scheduled_for"], payload["data_as_of"],
            fingerprint, json.dumps(payload, ensure_ascii=False), created_at,
        ),
    )
    database.commit()


def test_channel_radar_empty_state(database_path, root):
    app = create_app(database_path, root / "config" / "twse_openapi.datasets.json")
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/channel-radar")
    assert response.status_code == 200
    assert "尚無可用的頻道收盤簡報" in response.get_data(as_text=True)


def test_channel_radar_uses_latest_version_and_renders_three_switches(database, database_path, root):
    _insert_run(database, _payload("舊版", version=1), run_id="run-v1", fingerprint="1" * 64, created_at="2026-08-17 15:05:00")
    _insert_run(database, _payload("新版", version=2), run_id="run-v2", fingerprint="2" * 64, created_at="2026-08-17 15:06:00")
    app = create_app(database_path, root / "config" / "twse_openapi.datasets.json")
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/channel-radar?date=2026-08-17")
        invalid = client.get("/channel-radar?date=not-a-date")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert invalid.status_code == 400
    assert "新版-資金雷達" in html
    assert "舊版-資金雷達" not in html
    assert html.count('role="tab"') == 3
    assert "RULE_BASED_FALLBACK" in html
    assert "頁面不宣稱 AI 已排序" in html
