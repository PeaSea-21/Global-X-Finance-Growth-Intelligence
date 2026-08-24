from __future__ import annotations

from global_x_finance.security import scan_credentials


def test_suspected_token_fails_security_scan(tmp_path):
    prefix = "gh" + "p_"
    token = prefix + ("A" * 36)
    (tmp_path / "synthetic_leak.txt").write_text(token, encoding="utf-8")

    findings = scan_credentials(tmp_path)
    assert findings
    assert findings[0].kind == "GitHub token"


def test_placeholder_is_not_reported(tmp_path):
    key_name = "api_" + "key"
    (tmp_path / ".env.example").write_text(
        f'{key_name}="placeholder_value"', encoding="utf-8"
    )
    assert scan_credentials(tmp_path) == []


def test_url_slug_is_not_reported_as_openai_key(tmp_path):
    (tmp_path / "source.json").write_text(
        "https://www.cnbc.com/2026/08/20/sk-hynixs-south-korean-shares-surge-stock-buyback-.html",
        encoding="utf-8",
    )
    assert scan_credentials(tmp_path) == []
