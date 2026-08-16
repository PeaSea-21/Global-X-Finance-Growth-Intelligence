from __future__ import annotations

import csv
from pathlib import Path

import pytest

from global_x_finance.errors import ValidationError
from global_x_finance.source_registry import validate_registry

from conftest import INPUTS


def _write_registry(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_verified_registry_audit_counts():
    report = validate_registry(INPUTS / "verified_source_registry.csv")
    assert len(report.rows) == 17
    assert report.active_count == 17
    assert report.api_verified_count == 1
    assert "TW-B03" in report.blocked_source_ids


def test_active_source_without_evidence_url_fails(tmp_path):
    source = INPUTS / "verified_source_registry.csv"
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    rows[0]["evidence_url"] = ""
    registry = tmp_path / "synthetic_registry.csv"
    _write_registry(registry, rows, fields)

    with pytest.raises(ValidationError, match="ACTIVE source missing evidence_url"):
        validate_registry(registry)


def test_active_does_not_imply_collection_permission(database):
    row = database.execute(
        "SELECT registry_status, collection_status FROM sources WHERE source_id = 'TW-B03'"
    ).fetchone()
    assert row["registry_status"] == "ACTIVE"
    assert row["collection_status"] == "BLOCKED_ROBOTS_OR_NEEDS_PERMISSION"

    api_rows = database.execute(
        "SELECT source_id FROM sources WHERE collection_status = 'API_VERIFIED'"
    ).fetchall()
    assert [row["source_id"] for row in api_rows] == ["TW-A02"]

