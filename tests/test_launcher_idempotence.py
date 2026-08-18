from global_x_finance.db import apply_migrations
from global_x_finance.source_registry import import_registry, validate_registry


def test_launcher_initialization_steps_are_idempotent(database, root):
    assert apply_migrations(database, root / "migrations") == []
    report = validate_registry(root / "codex_mvp_inputs" / "verified_source_registry.csv")
    expected_count = len(report.rows)
    assert import_registry(database, report) == expected_count
    assert import_registry(database, report) == expected_count
    assert database.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == expected_count
    expected_migrations = len(list((root / "migrations").glob("*.sql")))
    assert database.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == expected_migrations


def test_windows_launcher_files_have_required_steps(root):
    batch_path = root / "启动台湾Demo.bat"
    batch_bytes = batch_path.read_bytes()
    batch = batch_bytes.decode("ascii")
    powershell = (root / "scripts" / "start_demo.ps1").read_text(encoding="utf-8")
    assert "start_demo.ps1" in batch
    assert 'cd /d "%~dp0"' in batch
    assert '-File "%~dp0scripts\\start_demo.ps1"' in batch
    assert "pause" in batch
    assert "-m venv" in powershell
    assert "global_x_finance.cli db init" in powershell
    assert "global_x_finance.cli sources import" in powershell
    assert "global_x_finance.cli radar registry-import" in powershell
    assert "global_x_finance.cli normalize twse" in powershell
    assert "global_x_finance.webapp" in powershell
    assert "Test-CurrentRadar" in powershell
    assert "ben-stock-radar.topic-queue.v1" in powershell
    assert "8765, 8766, 8767" in powershell
    assert "--port $launchPort --open-browser" in powershell
