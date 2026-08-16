from __future__ import annotations

import json
import socket
import sqlite3
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from .errors import ValidationError
from .evidence import EvidenceStore, content_sha256


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: bytes
    content_type: str = "application/json"


@dataclass(frozen=True)
class CollectionResult:
    run_id: str
    dataset_id: str
    dataset_name: str
    endpoint: str
    status: str
    fetched_count: int
    new_count: int
    duplicate_count: int
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class BatchCollectionResult:
    batch_id: str
    results: tuple[CollectionResult, ...]

    @property
    def status(self) -> str:
        statuses = {result.status for result in self.results}
        if statuses == {"SUCCESS"}:
            return "SUCCESS"
        if "SUCCESS" in statuses:
            return "PARTIAL_FAILED"
        return "FAILED"

    @property
    def fetched_count(self) -> int:
        return sum(result.fetched_count for result in self.results)

    @property
    def new_count(self) -> int:
        return sum(result.new_count for result in self.results)

    @property
    def duplicate_count(self) -> int:
        return sum(result.duplicate_count for result in self.results)


Transport = Callable[[str, float], HttpResponse]


def load_twse_config(path: str | Path) -> dict:
    config_path = Path(path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not config.get("source_id") or not config.get("datasets"):
        raise ValidationError(f"Invalid TWSE dataset config: {config_path}")
    for dataset in config["datasets"]:
        endpoint = dataset.get("endpoint", "")
        if not endpoint.startswith("https://openapi.twse.com.tw/v1/"):
            raise ValidationError(f"Dataset endpoint is outside the verified TWSE OpenAPI: {endpoint}")
        if dataset.get("method") != "GET":
            raise ValidationError(f"Unsupported dataset method: {dataset.get('method')}")
    return config


def _default_transport(url: str, timeout: float) -> HttpResponse:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "User-Agent": "Global-X-Finance-Evidence-Demo/0.2",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return HttpResponse(
            status=response.status,
            body=response.read(),
            content_type=response.headers.get("Content-Type", "application/json"),
        )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _published_at(record: dict, dataset: dict) -> str | None:
    field = dataset.get("published_at_field")
    if not field:
        return None
    value = str(record.get(field, "")).strip()
    if not value:
        return None
    if dataset.get("published_at_format") == "ROC_YYYMMDD":
        if len(value) != 7 or not value.isdigit():
            raise ValidationError(
                f"Unexpected ROC date in {dataset['dataset_id']}.{field}: {value}"
            )
        year = int(value[:3]) + 1911
        parsed = datetime(
            year,
            int(value[3:5]),
            int(value[5:7]),
            tzinfo=timezone(timedelta(hours=8)),
        )
        return parsed.isoformat()
    raise ValidationError(
        f"Unsupported published_at_format: {dataset.get('published_at_format')}"
    )


def _error_details(error: Exception) -> tuple[str, str]:
    if isinstance(error, urllib.error.HTTPError):
        return f"HTTP_{error.code}", str(error.reason)[:1000]
    if isinstance(error, (TimeoutError, socket.timeout)):
        return "TIMEOUT", str(error)[:1000] or "TWSE OpenAPI request timed out"
    if isinstance(error, json.JSONDecodeError):
        return "INVALID_JSON", str(error)[:1000]
    if isinstance(error, ValidationError):
        return "INVALID_RESPONSE", str(error)[:1000]
    if isinstance(error, urllib.error.URLError):
        reason = error.reason
        if isinstance(reason, (TimeoutError, socket.timeout)):
            return "TIMEOUT", str(reason)[:1000]
        return "NETWORK_ERROR", str(reason)[:1000]
    return "UNEXPECTED_ERROR", str(error)[:1000]


class TwseOpenApiCollector:
    def __init__(
        self,
        connection: sqlite3.Connection,
        config: dict,
        *,
        transport: Transport | None = None,
        timeout: float = 60,
        test_mode: bool = False,
    ):
        self.connection = connection
        self.config = config
        self.transport = transport or _default_transport
        self.timeout = timeout
        self.data_label = "SYNTHETIC_TEST_DATA" if test_mode else "REAL_OFFICIAL_SOURCE"

    def collect_all(self, source_id: str | None = None) -> BatchCollectionResult:
        requested_source_id = source_id or self.config["source_id"]
        source = self.connection.execute(
            """
            SELECT s.id, s.source_id, s.collection_status, s.market_id
            FROM sources s WHERE s.source_id = ?
            """,
            (requested_source_id,),
        ).fetchone()
        if source is None:
            raise ValidationError(f"Unknown source_id: {requested_source_id}")
        if source["collection_status"] != "API_VERIFIED":
            raise ValidationError(
                f"Automatic collection denied for {requested_source_id}: "
                f"collection_status={source['collection_status']}"
            )
        if requested_source_id != self.config["source_id"]:
            raise ValidationError(
                f"No audited dataset configuration for source_id: {requested_source_id}"
            )

        batch_id = str(uuid.uuid4())
        results = tuple(
            self._collect_dataset(source, dataset, batch_id)
            for dataset in self.config["datasets"]
        )
        return BatchCollectionResult(batch_id=batch_id, results=results)

    def _collect_dataset(self, source: sqlite3.Row, dataset: dict, batch_id: str) -> CollectionResult:
        run_id = str(uuid.uuid4())
        started_at = _utc_now()
        endpoint = dataset["endpoint"]
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO collection_runs (
                    id, market_id, source_id, started_at, status, item_count,
                    collector_version, batch_id, endpoint, dataset_name,
                    new_item_count, duplicate_item_count
                ) VALUES (?, ?, ?, ?, 'RUNNING', 0, ?, ?, ?, ?, 0, 0)
                """,
                (
                    run_id, source["market_id"], source["id"], started_at,
                    self.config["collector_version"], batch_id, endpoint,
                    dataset["dataset_name"],
                ),
            )

        try:
            response = self.transport(endpoint, self.timeout)
            if response.status != 200:
                raise urllib.error.HTTPError(
                    endpoint, response.status, "Non-200 TWSE response", {}, None
                )
            payload = json.loads(response.body.decode("utf-8-sig"))
            if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
                raise ValidationError("TWSE response must be an array of JSON objects")

            prepared: list[tuple[dict, str, str | None, str]] = []
            for record in payload:
                original_content = json.dumps(
                    record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                )
                digest = content_sha256(original_content)
                evidence_locator = f"{endpoint}#record-sha256={digest}"
                prepared.append(
                    (record, original_content, _published_at(record, dataset), evidence_locator)
                )

            fetched_at = _utc_now()
            store = EvidenceStore(self.connection)
            new_count = 0
            duplicate_count = 0
            self.connection.execute("BEGIN")
            for record, original_content, published_at, evidence_locator in prepared:
                result = store.save_raw_item(
                    source_id=source["source_id"],
                    original_url=evidence_locator,
                    canonical_url=endpoint,
                    original_content=original_content,
                    published_at=published_at,
                    fetched_at=fetched_at,
                    mime_type=response.content_type.split(";", 1)[0],
                    raw_payload=record,
                    data_label=self.data_label,
                    collection_run_id=run_id,
                    commit=False,
                )
                if result.created:
                    new_count += 1
                else:
                    duplicate_count += 1
            finished_at = _utc_now()
            self.connection.execute(
                """
                UPDATE collection_runs
                SET finished_at = ?, status = 'SUCCESS', item_count = ?,
                    new_item_count = ?, duplicate_item_count = ?
                WHERE id = ?
                """,
                (finished_at, len(payload), new_count, duplicate_count, run_id),
            )
            self.connection.commit()
            return CollectionResult(
                run_id=run_id,
                dataset_id=dataset["dataset_id"],
                dataset_name=dataset["dataset_name"],
                endpoint=endpoint,
                status="SUCCESS",
                fetched_count=len(payload),
                new_count=new_count,
                duplicate_count=duplicate_count,
            )
        except Exception as error:
            self.connection.rollback()
            error_code, error_message = _error_details(error)
            finished_at = _utc_now()
            with self.connection:
                self.connection.execute(
                    """
                    UPDATE collection_runs
                    SET finished_at = ?, status = 'FAILED', error_code = ?,
                        error_message = ?
                    WHERE id = ?
                    """,
                    (finished_at, error_code, error_message, run_id),
                )
            return CollectionResult(
                run_id=run_id,
                dataset_id=dataset["dataset_id"],
                dataset_name=dataset["dataset_name"],
                endpoint=endpoint,
                status="FAILED",
                fetched_count=0,
                new_count=0,
                duplicate_count=0,
                error_code=error_code,
                error_message=error_message,
            )
