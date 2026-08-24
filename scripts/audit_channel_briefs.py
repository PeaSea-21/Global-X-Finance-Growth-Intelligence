from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any


SECURITY_ID = re.compile(r"^(TWSE|TPEX):[A-Z0-9]+$")


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def audit_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    as_of = _parse_datetime(payload["data_as_of"])
    session_date = payload["market_session_date"]
    violations: list[dict[str, str]] = []
    channels: dict[str, dict[str, Any]] = {}

    def fail(candidate_id: str, code: str) -> None:
        violations.append({"date": session_date, "candidate_id": candidate_id, "code": code})

    for brief in payload["briefs"]:
        assignments = brief["assignments"]
        target = int(brief["target_count"])
        top = assignments[:target]
        candidate_ids = [row["candidate_id"] for row in assignments]
        titles = ["".join(row["title"].casefold().split()) for row in assignments]
        if len(candidate_ids) != len(set(candidate_ids)):
            fail(brief["channel_id"], "DUPLICATE_CANDIDATE_ID")
        if len(titles) != len(set(titles)):
            fail(brief["channel_id"], "DUPLICATE_TITLE")
        if [row["candidate_rank"] for row in assignments] != list(range(1, len(assignments) + 1)):
            fail(brief["channel_id"], "NON_SEQUENTIAL_RANK")
        if brief["status"] == "READY" and len(top) != target:
            fail(brief["channel_id"], "READY_WITHOUT_TOP_TARGET")

        for item in assignments:
            candidate_id = item["candidate_id"]
            if item.get("market_session_date") != session_date:
                fail(candidate_id, "SESSION_DATE_MISMATCH")
            if item.get("data_as_of") != payload["data_as_of"]:
                fail(candidate_id, "DATA_AS_OF_MISMATCH")
            evidence = item.get("evidence", []) + item.get("opinion_evidence", [])
            if not evidence:
                fail(candidate_id, "NO_TRACEABLE_EVIDENCE")
            if not item.get("security_ids") or any(
                not SECURITY_ID.fullmatch(value) for value in item["security_ids"]
            ):
                fail(candidate_id, "INVALID_MARKET_SECURITY_ID")
            for row in evidence:
                if row.get("trade_date"):
                    try:
                        if date.fromisoformat(row["trade_date"]) > as_of.date():
                            fail(candidate_id, "FUTURE_TRADE_DATE")
                    except ValueError:
                        fail(candidate_id, "INVALID_TRADE_DATE")
                for key in ("published_at", "announced_at"):
                    if row.get(key) and _parse_datetime(row[key]) > as_of:
                        fail(candidate_id, "FUTURE_EVIDENCE")

            if brief["channel_type"] == "SIGNAL_HEAVY":
                if item["candidate_type"] != "MARKET_SIGNAL":
                    fail(candidate_id, "SIGNAL_CHANNEL_TYPE_MISMATCH")
                if "NOT_FUND_FLOW" not in item["risk_flags"]:
                    fail(candidate_id, "MISSING_NOT_FUND_FLOW_WARNING")
            elif brief["channel_type"] == "EVENT_HEAVY":
                if item["candidate_type"] == "MARKET_SIGNAL" and item["editorial_status"] != "NEEDS_RESEARCH":
                    fail(candidate_id, "UNCONFIRMED_SIGNAL_NOT_RESEARCH")
            else:
                if item["candidate_type"] != "CROSS_ENTITY":
                    fail(candidate_id, "INDUSTRY_CHANNEL_TYPE_MISMATCH")
                if len(item["security_ids"]) < 2:
                    fail(candidate_id, "CROSS_ENTITY_BELOW_TWO_SECURITIES")
                if any(
                    row.get("industry_mapping_status") != "MAPPED_COMMON_STOCK"
                    for row in item["stock_details"]
                ):
                    fail(candidate_id, "UNMAPPED_INDUSTRY_SECURITY")
                if "CO_OCCURRENCE_NOT_CAUSATION" not in item["risk_flags"]:
                    fail(candidate_id, "MISSING_CAUSALITY_WARNING")

        channels[brief["channel_type"]] = {
            "channel_name": brief["channel_name"],
            "status": brief["status"],
            "qualified_count": brief["qualified_count"],
            "top_count": len(top),
            "backup_count": max(0, len(assignments) - target),
            "top_types": [row["candidate_type"] for row in top],
            "top_candidate_ids": [row["candidate_id"] for row in top],
            "shortage_reasons": brief["shortage_reasons"],
        }

    if payload["ranking_method"] != "RULE_BASED_FALLBACK":
        fail("RUN", "UNEXPECTED_RANKING_METHOD")
    signal_top = channels.get("SIGNAL_HEAVY", {}).get("top_candidate_ids", [])
    event_top = channels.get("EVENT_HEAVY", {}).get("top_candidate_ids", [])
    if signal_top == event_top:
        fail("RUN", "SIGNAL_AND_EVENT_TOP5_IDENTICAL")

    return {
        "market_session_date": session_date,
        "session_state": payload["session_state"],
        "coverage_status": payload["coverage_status"],
        "data_as_of": payload["data_as_of"],
        "ranking_method": payload["ranking_method"],
        "source_readiness": payload["source_readiness"],
        "channels": channels,
        "signal_event_top5_overlap": len(set(signal_top) & set(event_top)),
        "assignment_count": sum(len(brief["assignments"]) for brief in payload["briefs"]),
    }, violations


def database_summary(database: Path) -> dict[str, Any]:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        versions = [
            dict(row) for row in connection.execute(
                """SELECT channel_id, market_session_date, MAX(brief_version) AS latest_version
                   FROM ben_channel_daily_briefs
                   GROUP BY channel_id, market_session_date
                   ORDER BY market_session_date, channel_id"""
            )
        ]
        mappings = [
            dict(row) for row in connection.execute(
                """SELECT exchange_code, mapping_status, COUNT(*) AS count
                   FROM security_industry_mappings
                   GROUP BY exchange_code, mapping_status
                   ORDER BY exchange_code, mapping_status"""
            )
        ]
        orphan_evidence = connection.execute(
            """SELECT COUNT(*) FROM security_industry_mappings m
               LEFT JOIN raw_items r ON r.id=m.raw_item_id WHERE r.id IS NULL"""
        ).fetchone()[0]
    finally:
        connection.close()
    return {
        "latest_brief_versions": versions,
        "industry_mapping_counts": mappings,
        "industry_mapping_orphan_evidence": orphan_evidence,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit BEN P06B channel Replay artifacts.")
    parser.add_argument("--input-dir", default="research/ben_radar_channel_p06b")
    parser.add_argument("--database", default="data/taiwan-demo.db")
    parser.add_argument("--expected-days", type=int, default=5)
    parser.add_argument("--output", default="research/ben_radar_channel_p06b/acceptance_report.json")
    args = parser.parse_args()

    paths = sorted(Path(args.input_dir).glob("channel_brief_*.json"))
    reports = []
    violations: list[dict[str, str]] = []
    for path in paths:
        report, file_violations = audit_payload(json.loads(path.read_text(encoding="utf-8")))
        reports.append(report)
        violations.extend(file_violations)
    if len(paths) != args.expected_days:
        violations.append({
            "date": "ALL", "candidate_id": "RUN",
            "code": f"EXPECTED_{args.expected_days}_REPLAY_FILES_GOT_{len(paths)}",
        })
    database = database_summary(Path(args.database))
    if database["industry_mapping_orphan_evidence"]:
        violations.append({
            "date": "ALL", "candidate_id": "INDUSTRY_MAPPING",
            "code": "ORPHAN_MAPPING_EVIDENCE",
        })

    output = {
        "artifact": "BEN_CHANNEL_P06B_ACCEPTANCE",
        "status": "PASS" if not violations else "FAIL",
        "checked_files": [str(path) for path in paths],
        "replay_count": len(paths),
        "reports": reports,
        "database": database,
        "violations": violations,
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": output["status"], "replay_count": len(paths),
        "violation_count": len(violations), "output": str(target),
    }, ensure_ascii=False, indent=2))
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
