from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


OUTCOME_STATES = {
    "CONFIRMED",
    "PARTIALLY_CONFIRMED",
    "NOT_CONFIRMED",
    "INVALIDATED",
    "PENDING_DATA",
}
RESOLVED_STATES = OUTCOME_STATES - {"PENDING_DATA"}
ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"required file is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _is_http_url(value: Any) -> bool:
    parsed = urlparse(str(value or ""))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _event_fingerprint(update: dict[str, Any]) -> str:
    encoded = json.dumps(
        update, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_update(update: dict[str, Any]) -> None:
    status = update.get("status")
    if status not in OUTCOME_STATES:
        raise ValueError(f"invalid outcome status: {status}")
    if not str(update.get("snapshot_fingerprint") or "").strip():
        raise ValueError("review update is missing snapshot_fingerprint")
    if not str(update.get("candidate_id") or "").strip():
        raise ValueError("review update is missing candidate_id")
    if len(str(update.get("summary") or "").strip()) < 12:
        raise ValueError("review update summary is missing or too short")
    if status in RESOLVED_STATES:
        if not str(update.get("observation_date") or "").strip():
            raise ValueError("resolved review requires observation_date")
        evidence = list(update.get("evidence") or [])
        if not evidence:
            raise ValueError("resolved review requires Evidence")
        if any(
            not _is_http_url(row.get("human_verification_url") or row.get("url"))
            for row in evidence
        ):
            raise ValueError("resolved review Evidence requires a human-verification URL")


def apply_updates(site_data_path: str | Path, updates_path: str | Path) -> dict[str, Any]:
    site_path = Path(site_data_path)
    site_root = site_path.parent.resolve()
    site_payload = _read_json(site_path)
    workbench = site_payload.get("channel_workbench")
    if not isinstance(workbench, dict):
        raise ValueError("channel_workbench is missing")
    history_index = list(workbench.get("channel_history_index") or [])
    by_fingerprint = {
        str(row.get("snapshot_fingerprint") or ""): row for row in history_index
    }
    updates_payload = _read_json(Path(updates_path))
    updates = list(updates_payload.get("updates") or [])
    if not updates:
        raise ValueError("review update file contains no updates")

    applied = 0
    duplicates = 0
    touched: dict[str, tuple[dict[str, Any], Path, dict[str, Any]]] = {}
    recorded_at = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    for update in updates:
        _validate_update(update)
        fingerprint = str(update["snapshot_fingerprint"])
        index_row = by_fingerprint.get(fingerprint)
        if not index_row:
            raise ValueError(f"unknown history snapshot: {fingerprint}")
        relative_path = Path(str(index_row.get("path") or ""))
        artifact_path = (site_root / relative_path).resolve()
        try:
            artifact_path.relative_to(site_root / "history")
        except ValueError as exc:
            raise ValueError("history index points outside the history directory") from exc
        artifact = touched.get(fingerprint, (None, None, None))[0]
        if artifact is None:
            artifact = _read_json(artifact_path)
        if artifact.get("snapshot_fingerprint") != fingerprint:
            raise ValueError("history artifact fingerprint mismatch")
        channel = artifact.get("channel") or {}
        topics = list(channel.get("topics") or [])
        topic = next(
            (
                row
                for row in topics
                if str(row.get("candidate_id") or "") == str(update["candidate_id"])
            ),
            None,
        )
        if topic is None:
            raise ValueError(f"history topic not found: {update['candidate_id']}")

        event_payload = {
            "candidate_id": str(update["candidate_id"]),
            "status": update["status"],
            "summary": str(update["summary"]).strip(),
            "observation_date": update.get("observation_date"),
            "measured_result": update.get("measured_result"),
            "evidence": list(update.get("evidence") or []),
            "checkpoint_results": list(update.get("checkpoint_results") or []),
        }
        event_id = _event_fingerprint(event_payload)
        events = list(artifact.get("review_events") or [])
        if any(row.get("event_id") == event_id for row in events):
            duplicates += 1
        else:
            events.append(
                {
                    **event_payload,
                    "event_id": event_id,
                    "recorded_at": recorded_at,
                }
            )
            artifact["review_events"] = events
            applied += 1
        touched[fingerprint] = (artifact, artifact_path, index_row)

    for artifact, artifact_path, index_row in touched.values():
        artifact_path.write_text(
            json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        latest_by_topic = {
            str(row.get("candidate_id") or ""): str(row.get("status") or "PENDING_DATA")
            for row in list(artifact.get("review_events") or [])
        }
        status_counts: dict[str, int] = {}
        for topic in list((artifact.get("channel") or {}).get("topics") or []):
            status = latest_by_topic.get(
                str(topic.get("candidate_id") or ""),
                str((topic.get("outcome_review") or {}).get("status") or "PENDING_DATA"),
            )
            status_counts[status] = status_counts.get(status, 0) + 1
        index_row["status_counts"] = status_counts
        index_row["last_reviewed_at"] = recorded_at

    workbench["channel_history_index"] = history_index
    site_payload["channel_workbench"] = workbench
    site_path.write_text(
        json.dumps(site_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {
        "status": "PASS",
        "update_count": len(updates),
        "applied_count": applied,
        "duplicate_count": duplicates,
        "history_files_touched": len(touched),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Append Evidence-backed result reviews to immutable BEN channel history."
    )
    parser.add_argument(
        "--site-data",
        default=str(ROOT / "sites" / "ben-content-studio" / "data.json"),
    )
    parser.add_argument("--updates", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            apply_updates(args.site_data, args.updates),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
