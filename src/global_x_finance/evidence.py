from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .errors import ValidationError


ALLOWED_DATA_LABELS = {
    "RAW_EVIDENCE", "REAL_OFFICIAL_SOURCE", "SYNTHETIC_TEST_DATA",
    "UNKNOWN", "NEEDS_VERIFICATION"
}


@dataclass(frozen=True)
class RawItemResult:
    id: str
    created: bool
    duplicate_reason: str | None = None


def content_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _validate_timestamp(value: str | None, field: str) -> None:
    if not value:
        return
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValidationError(f"{field} must be an ISO-8601 timestamp") from error


class EvidenceStore:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def save_raw_item(
        self,
        *,
        source_id: str,
        original_url: str | None,
        original_content: str,
        published_at: str | None,
        fetched_at: str | None = None,
        mime_type: str = "text/plain",
        raw_payload: Any = None,
        data_label: str = "RAW_EVIDENCE",
        collection_run_id: str | None = None,
        canonical_url: str | None = None,
        commit: bool = True,
    ) -> RawItemResult:
        if not original_content:
            raise ValidationError("original_content is required")
        if original_url:
            parsed = urlparse(original_url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValidationError("original_url must be an http(s) URL")
        if data_label not in ALLOWED_DATA_LABELS:
            raise ValidationError(f"Unsupported data_label: {data_label}")
        fetched = fetched_at or datetime.now(timezone.utc).isoformat()
        _validate_timestamp(published_at, "published_at")
        _validate_timestamp(fetched, "fetched_at")
        digest = content_sha256(original_content)

        source = self.connection.execute(
            "SELECT id FROM sources WHERE source_id = ?", (source_id,)
        ).fetchone()
        if source is None:
            raise ValidationError(f"Unknown source_id: {source_id}")

        if original_url:
            duplicate = self.connection.execute(
                "SELECT id FROM raw_items WHERE original_url = ?", (original_url,)
            ).fetchone()
            if duplicate:
                return RawItemResult(duplicate["id"], False, "original_url")
        duplicate = self.connection.execute(
            "SELECT id FROM raw_items WHERE content_hash = ?", (digest,)
        ).fetchone()
        if duplicate:
            return RawItemResult(duplicate["id"], False, "content_hash")

        raw_item_id = str(uuid.uuid4())
        payload_json = json.dumps(
            {} if raw_payload is None else raw_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        parameters = (
            raw_item_id, collection_run_id, source["id"], original_url,
            canonical_url or original_url, original_content, published_at,
            fetched, digest, mime_type, payload_json, data_label,
        )
        statement = """
            INSERT INTO raw_items (
                id, collection_run_id, source_id, original_url, canonical_url,
                original_content, published_at, fetched_at, content_hash,
                mime_type, raw_payload_json, data_label
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        if commit:
            with self.connection:
                self.connection.execute(statement, parameters)
        else:
            self.connection.execute(statement, parameters)
        return RawItemResult(raw_item_id, True)

