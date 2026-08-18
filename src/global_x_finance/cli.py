from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .db import apply_migrations, connect, register_market_packs
from .errors import ValidationError
from .market_pack import load_and_validate_market_pack
from .normalization import TwseNormalizationService
from .official_data import (
    OfficialDataService,
    load_official_data_config,
    official_data_status,
    recent_disclosures,
    volume_history,
)
from .policy import XAdsPolicySnapshotService, load_policy_registry, load_policy_rules
from .realtime_radar import (
    RealtimeRadar,
    import_realtime_registry,
    load_realtime_registry,
    make_xhot_fetcher,
    radar_summary,
)
from .security import scan_credentials
from .source_registry import import_registry, validate_registry
from .twse_collector import load_twse_config
from .ben_radar import sync_ben_radar
from .x_intelligence import (
    account_counts,
    collect_x_accounts_once,
    diagnose_yahoo_finance,
    import_x_accounts,
    load_x_accounts,
)


def _pack_validate(args: argparse.Namespace) -> None:
    for path in args.market_pack:
        pack = load_and_validate_market_pack(path, args.schema)
        print(f"VALID {pack['country_code']} {pack['pack_id']} ({path})")


def _db_init(args: argparse.Namespace) -> None:
    packs = [
        load_and_validate_market_pack(path, args.schema)
        for path in args.market_pack
    ]
    connection = connect(args.db)
    try:
        migrations = apply_migrations(connection, args.migrations)
        register_market_packs(connection, packs)
    finally:
        connection.close()
    print(f"Database initialized: {args.db}")
    print(f"Migrations: {', '.join(migrations)}")
    print("Markets: " + ", ".join(pack["country_code"] for pack in packs))


def _sources_validate(args: argparse.Namespace) -> None:
    report = validate_registry(args.registry)
    print(
        f"VALID rows={len(report.rows)} active={report.active_count} "
        f"api_verified={report.api_verified_count} blocked_or_review={len(report.blocked_source_ids)}"
    )


def _sources_import(args: argparse.Namespace) -> None:
    report = validate_registry(args.registry)
    connection = connect(args.db)
    try:
        count = import_registry(connection, report)
    finally:
        connection.close()
    print(
        f"Validated and imported {count} sources: active={report.active_count}, "
        f"api_verified={report.api_verified_count}"
    )


def _security_scan(args: argparse.Namespace) -> None:
    findings = scan_credentials(args.root)
    if findings:
        for finding in findings:
            print(f"SECRET {finding.path}:{finding.line} {finding.kind}", file=sys.stderr)
        raise ValidationError(f"Credential scan failed with {len(findings)} finding(s)")
    print(f"Credential scan passed: {Path(args.root).resolve()}")


def _normalize_twse(args: argparse.Namespace) -> None:
    config = load_twse_config(args.dataset_config)
    connection = connect(args.db)
    try:
        result = TwseNormalizationService(connection, config).normalize_all(config["source_id"])
    finally:
        connection.close()
    print(
        "TWSE normalization complete: "
        f"new={result.normalized_new_count}, existing={result.normalized_existing_count}, "
        f"entities_new={result.entity_new_count}, signals_new={result.signal_new_count}, "
        f"signals_existing={result.signal_existing_count}, "
        f"total_normalized={result.total_normalized_count}, "
        f"total_signals={result.total_signal_count}"
    )


def _official_data_sync(args: argparse.Namespace) -> None:
    config = load_official_data_config(args.config)
    connection = connect(args.db)
    try:
        result = OfficialDataService(connection, config).sync_all()
    finally:
        connection.close()
    print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))


def _official_data_status(args: argparse.Namespace) -> None:
    connection = connect(args.db)
    try:
        result = official_data_status(connection)
    finally:
        connection.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _official_data_history(args: argparse.Namespace) -> None:
    connection = connect(args.db)
    try:
        rows = volume_history(connection, args.security_id, limit=args.limit)
    finally:
        connection.close()
    print(json.dumps(rows, ensure_ascii=False, indent=2))


def _official_data_disclosures(args: argparse.Namespace) -> None:
    connection = connect(args.db)
    try:
        rows = recent_disclosures(connection, args.security_id, limit=args.limit)
    finally:
        connection.close()
    print(json.dumps(rows, ensure_ascii=False, indent=2))


def _policies_snapshot(args: argparse.Namespace) -> None:
    page_registry = load_policy_registry(args.pages)
    rule_registry = load_policy_rules(
        args.rules, {page["policy_key"] for page in page_registry["pages"]}
    )
    connection = connect(args.db)
    try:
        result = XAdsPolicySnapshotService(
            connection, page_registry, rule_registry
        ).snapshot_all()
    finally:
        connection.close()
    print(
        "X Ads policy snapshot complete: "
        f"snapshots_new={result.snapshot_new_count}, "
        f"snapshots_existing={result.snapshot_existing_count}, "
        f"rules_new={result.rule_new_count}, rules_existing={result.rule_existing_count}, "
        f"checklists_new={result.checklist_new_count}, "
        f"total_snapshots={result.total_snapshot_count}, "
        f"total_rules={result.total_rule_count}"
    )


def _radar_registry_validate(args: argparse.Namespace) -> None:
    rows = load_realtime_registry(args.registry)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["monitoring_status"]] = counts.get(row["monitoring_status"], 0) + 1
    print(
        f"VALID rows={len(rows)} "
        + " ".join(f"{key.lower()}={value}" for key, value in sorted(counts.items()))
    )


def _radar_registry_import(args: argparse.Namespace) -> None:
    rows = load_realtime_registry(args.registry)
    connection = connect(args.db)
    try:
        count = import_realtime_registry(connection, rows)
        summary = radar_summary(connection)
    finally:
        connection.close()
    print(
        f"Realtime registry imported: rows={count}, active={summary['active']}, "
        f"independent_active_groups={summary['independent_active_groups']}"
    )


def _radar_cycle(args: argparse.Namespace) -> None:
    x_fetcher = make_xhot_fetcher(args.xhot_root) if args.xhot_root else None
    connection = connect(args.db)
    try:
        result = RealtimeRadar(connection, x_fetcher=x_fetcher).run_cycle(force=args.force)
    finally:
        connection.close()
    print(
        f"Radar cycle {result.cycle_id}: sources={len(result.sources)} "
        f"started={result.started_at} finished={result.finished_at}"
    )
    for source in result.sources:
        print(
            f"{source.source_id} {source.status} fetched={source.fetched_count} "
            f"new={source.new_count} duplicate={source.duplicate_count} "
            f"request_seconds={source.latency_seconds}"
            + (f" error={source.error}" if source.error else "")
        )


def _radar_status(args: argparse.Namespace) -> None:
    connection = connect(args.db)
    try:
        summary = radar_summary(connection)
    finally:
        connection.close()
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


def _ben_radar_sync(args: argparse.Namespace) -> None:
    connection = connect(args.db)
    try:
        result = sync_ben_radar(connection)
    finally:
        connection.close()
    print(json.dumps({
        "news_sources": list(result.news_results),
        "pool_count": result.pool_count,
        "history_valid_count": result.history_valid_count,
        "history_failed": list(result.history_failed),
    }, ensure_ascii=False, indent=2))


def _ben_x_import(args: argparse.Namespace) -> None:
    accounts = load_x_accounts(args.accounts)
    connection = connect(args.db)
    try:
        imported = import_x_accounts(connection, accounts)
    finally:
        connection.close()
    print(json.dumps({"imported": imported, **account_counts(accounts)}, ensure_ascii=False))


def _ben_x_sync(args: argparse.Namespace) -> None:
    accounts = load_x_accounts(args.accounts)
    connection = connect(args.db)
    try:
        results = collect_x_accounts_once(
            connection,
            accounts,
            force=args.force,
            include_low_confidence=args.include_low_confidence,
        )
    finally:
        connection.close()
    print(json.dumps({
        "accounts": account_counts(accounts),
        "results": [result.__dict__ for result in results],
    }, ensure_ascii=False, indent=2))


def _ben_yahoo_diagnose(args: argparse.Namespace) -> None:
    connection = connect(args.db)
    try:
        results = diagnose_yahoo_finance(connection)
    finally:
        connection.close()
    print(json.dumps(results, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gxf",
        description="Global X Finance traceable official-data foundation (no publishing)",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    pack = commands.add_parser("pack", help="Market Pack commands")
    pack_commands = pack.add_subparsers(dest="pack_command", required=True)
    pack_validate = pack_commands.add_parser("validate")
    pack_validate.add_argument("--schema", required=True)
    pack_validate.add_argument("--market-pack", action="append", required=True)
    pack_validate.set_defaults(handler=_pack_validate)

    database = commands.add_parser("db", help="Database commands")
    db_commands = database.add_subparsers(dest="db_command", required=True)
    db_init = db_commands.add_parser("init")
    db_init.add_argument("--db", required=True)
    db_init.add_argument("--migrations", default="migrations")
    db_init.add_argument("--schema", default="schemas/market-pack.schema.json")
    db_init.add_argument("--market-pack", action="append", required=True)
    db_init.set_defaults(handler=_db_init)

    sources = commands.add_parser("sources", help="Verified source registry commands")
    source_commands = sources.add_subparsers(dest="sources_command", required=True)
    source_validate = source_commands.add_parser("validate")
    source_validate.add_argument("--registry", required=True)
    source_validate.set_defaults(handler=_sources_validate)
    source_import = source_commands.add_parser("import")
    source_import.add_argument("--db", required=True)
    source_import.add_argument("--registry", required=True)
    source_import.set_defaults(handler=_sources_import)

    normalize = commands.add_parser("normalize", help="Official Evidence normalization commands")
    normalize_commands = normalize.add_subparsers(dest="normalize_command", required=True)
    normalize_twse = normalize_commands.add_parser("twse")
    normalize_twse.add_argument("--db", required=True)
    normalize_twse.add_argument(
        "--dataset-config", default="config/twse_openapi.datasets.json"
    )
    normalize_twse.set_defaults(handler=_normalize_twse)

    official = commands.add_parser("official-data", help="TWSE/TPEx/MOPS official data")
    official_commands = official.add_subparsers(dest="official_command", required=True)
    official_sync = official_commands.add_parser("sync")
    official_sync.add_argument("--db", required=True)
    official_sync.add_argument("--config", default="config/official_data.sources.json")
    official_sync.set_defaults(handler=_official_data_sync)
    official_status = official_commands.add_parser("status")
    official_status.add_argument("--db", required=True)
    official_status.set_defaults(handler=_official_data_status)
    official_history = official_commands.add_parser("history")
    official_history.add_argument("--db", required=True)
    official_history.add_argument("--security-id", required=True)
    official_history.add_argument("--limit", type=int, default=30)
    official_history.set_defaults(handler=_official_data_history)
    official_disclosures = official_commands.add_parser("disclosures")
    official_disclosures.add_argument("--db", required=True)
    official_disclosures.add_argument("--security-id", required=True)
    official_disclosures.add_argument("--limit", type=int, default=20)
    official_disclosures.set_defaults(handler=_official_data_disclosures)

    policies = commands.add_parser("policies", help="Official X Ads policy commands")
    policy_commands = policies.add_subparsers(dest="policy_command", required=True)
    policy_snapshot = policy_commands.add_parser("snapshot")
    policy_snapshot.add_argument("--db", required=True)
    policy_snapshot.add_argument("--pages", default="config/x_ads_policy.pages.json")
    policy_snapshot.add_argument("--rules", default="config/x_ads_policy.rules.json")
    policy_snapshot.set_defaults(handler=_policies_snapshot)

    radar = commands.add_parser("radar", help="Taiwan realtime source radar commands")
    radar_commands = radar.add_subparsers(dest="radar_command", required=True)
    radar_validate = radar_commands.add_parser("registry-validate")
    radar_validate.add_argument("--registry", default="config/taiwan_realtime_sources.csv")
    radar_validate.set_defaults(handler=_radar_registry_validate)
    radar_import = radar_commands.add_parser("registry-import")
    radar_import.add_argument("--db", required=True)
    radar_import.add_argument("--registry", default="config/taiwan_realtime_sources.csv")
    radar_import.set_defaults(handler=_radar_registry_import)
    radar_cycle = radar_commands.add_parser("cycle")
    radar_cycle.add_argument("--db", required=True)
    radar_cycle.add_argument("--xhot-root")
    radar_cycle.add_argument("--force", action="store_true")
    radar_cycle.set_defaults(handler=_radar_cycle)
    radar_status = radar_commands.add_parser("status")
    radar_status.add_argument("--db", required=True)
    radar_status.set_defaults(handler=_radar_status)

    ben = commands.add_parser("ben-radar", help="Ben market radar one-time data commands")
    ben_commands = ben.add_subparsers(dest="ben_command", required=True)
    ben_sync = ben_commands.add_parser("sync")
    ben_sync.add_argument("--db", required=True)
    ben_sync.set_defaults(handler=_ben_radar_sync)
    ben_x_import = ben_commands.add_parser("x-import")
    ben_x_import.add_argument("--db", required=True)
    ben_x_import.add_argument("--accounts", default="config/x_accounts.csv")
    ben_x_import.set_defaults(handler=_ben_x_import)
    ben_x_sync = ben_commands.add_parser("x-sync")
    ben_x_sync.add_argument("--db", required=True)
    ben_x_sync.add_argument("--accounts", default="config/x_accounts.csv")
    ben_x_sync.add_argument("--force", action="store_true")
    ben_x_sync.add_argument("--include-low-confidence", action="store_true")
    ben_x_sync.set_defaults(handler=_ben_x_sync)
    ben_yahoo = ben_commands.add_parser("yahoo-diagnose")
    ben_yahoo.add_argument("--db", required=True)
    ben_yahoo.set_defaults(handler=_ben_yahoo_diagnose)

    security = commands.add_parser("security", help="Repository security checks")
    security_commands = security.add_subparsers(dest="security_command", required=True)
    security_scan = security_commands.add_parser("scan")
    security_scan.add_argument("--root", default=".")
    security_scan.set_defaults(handler=_security_scan)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.handler(args)
    except (ValidationError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
