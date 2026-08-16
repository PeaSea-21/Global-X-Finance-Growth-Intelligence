from __future__ import annotations

import json

from global_x_finance.twse_collector import HttpResponse, TwseOpenApiCollector
from global_x_finance.webapp import create_app


def _transport(url: str, timeout: float) -> HttpResponse:
    if url.endswith("MI_INDEX"):
        payload = [{"日期": "1150814", "指數": "SYNTHETIC_TEST_DATA", "收盤指數": "0"}]
    elif url.endswith("MI_QFIIS_cat"):
        payload = [{"IndustryCat": "SYNTHETIC_TEST_DATA", "Percentage": "0"}]
    else:
        payload = [{"Date": "1150814", "Code": "SYNTHETIC_TEST_DATA", "Name": "測試"}]
    return HttpResponse(200, json.dumps(payload, ensure_ascii=False).encode("utf-8"))


def test_demo_pages_sync_and_evidence_detail(database_path, root):
    def factory(connection, config):
        return TwseOpenApiCollector(
            connection, config, transport=_transport, test_mode=True
        )

    app = create_app(
        database_path,
        root / "config" / "twse_openapi.datasets.json",
        collector_factory=factory,
    )
    app.testing = True
    client = app.test_client()

    assert client.get("/health").get_json() == {"market": "TW", "status": "ok"}
    assert "同步台灣官方資料" in client.get("/").get_data(as_text=True)
    assert "API_VERIFIED" in client.get("/sources").get_data(as_text=True)

    response = client.post("/sync", follow_redirects=True)
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "同步結果：SUCCESS" in page
    assert "新增 3 筆" in page
    assert "SYNTHETIC_TEST_DATA" in client.get("/evidence").get_data(as_text=True)

    from global_x_finance.db import connect

    db = connect(database_path)
    try:
        item_id = db.execute("SELECT id FROM raw_items LIMIT 1").fetchone()[0]
    finally:
        db.close()
    detail = client.get(f"/evidence/{item_id}").get_data(as_text=True)
    assert "開啟官方 Evidence URL" in detail
    assert "TW-A02" in detail
    assert "SYNTHETIC_TEST_DATA" in detail
    assert "本頁面只展示官方原始資料，不構成投資建議。" in detail
    assert "https://openapi.twse.com.tw/v1/" in detail


def test_unknown_evidence_returns_404(database_path, root):
    app = create_app(database_path, root / "config" / "twse_openapi.datasets.json")
    app.testing = True
    assert app.test_client().get("/evidence/does-not-exist").status_code == 404
