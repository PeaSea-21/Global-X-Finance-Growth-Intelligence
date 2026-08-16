from __future__ import annotations

from pathlib import Path

import pytest

from global_x_finance.db import apply_migrations, connect, register_market_packs
from global_x_finance.market_pack import load_and_validate_market_pack
from global_x_finance.source_registry import import_registry, validate_registry


ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "codex_mvp_inputs"
SCHEMA = ROOT / "schemas" / "market-pack.schema.json"


@pytest.fixture()
def database(tmp_path):
    database_path = tmp_path / "synthetic-test.db"
    connection = connect(database_path)
    apply_migrations(connection, ROOT / "migrations")
    packs = [
        load_and_validate_market_pack(INPUTS / "taiwan.market-pack.yaml", SCHEMA),
        load_and_validate_market_pack(INPUTS / "us.market-pack.template.yaml", SCHEMA),
    ]
    register_market_packs(connection, packs)
    import_registry(connection, validate_registry(INPUTS / "verified_source_registry.csv"))
    yield connection
    connection.close()


@pytest.fixture()
def database_path(database):
    row = database.execute("PRAGMA database_list").fetchone()
    return Path(row["file"])


@pytest.fixture()
def root():
    return ROOT
