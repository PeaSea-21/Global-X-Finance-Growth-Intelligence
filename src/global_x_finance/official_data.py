from __future__ import annotations

import hashlib
import json
import re
import socket
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from .errors import ValidationError
from .evidence import EvidenceStore, content_sha256
from .twse_collector import HttpResponse


TAIPEI = timezone(timedelta(hours=8))
PERMISSION_STATES = {
    "TECHNICALLY_VERIFIED",
    "INTERNAL_USE_VERIFIED",
    "PUBLIC_DISPLAY_VERIFIED",
    "REDISTRIBUTION_REQUIRES_LICENSE",
    "UNKNOWN",
}
OFFICIAL_HOSTS = {
    "openapi.twse.com.tw",
    "www.twse.com.tw",
    "www.tpex.org.tw",
}
COMPANY_TICKER = re.compile(r"^[1-9][0-9]{3}$")


@dataclass(frozen=True)
class EndpointResult:
    source_key: str
    dataset: str
    endpoint: str
    status: str
    fetched_count: int
    stored_count: int
    duplicate_count: int
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class OfficialSyncResult:
    endpoint_results: tuple[EndpointResult, ...]
    twse_security_count: int
    tpex_security_count: int
    twse_market_data_count: int
    tpex_market_data_count: int
    disclosure_count: int
    disclosure_mapped_count: int

    @property
    def status(self) -> str:
        statuses = {row.status for row in self.endpoint_results}
        if statuses == {"SUCCESS"}:
            return "PASS"
        if "SUCCESS" in statuses:
            return "PARTIAL"
        return "FAIL"

    def as_dict(self) -> dict:
        result = asdict(self)
        result["status"] = self.status
        return result


Transport = Callable[[str, float], HttpResponse]


def _default_transport(url: str, timeout: float) -> HttpResponse:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "User-Agent": "BEN-Radar-Official-Data/1.0 (+bounded-official-data-connector)",
            "Cache-Control": "no-cache",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return HttpResponse(
            status=response.status,
            body=response.read(),
            content_type=response.headers.get("Content-Type", "application/json"),
        )


def load_official_data_config(path: str | Path) -> dict:
    config_path = Path(path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    sources = config.get("sources")
    if not config.get("collector_version") or not isinstance(sources, list):
        raise ValidationError(f"Invalid official-data config: {config_path}")
    keys = {source.get("source_key") for source in sources}
    if keys != {"TWSE", "TPEX", "MOPS"}:
        raise ValidationError("Official-data config must contain exactly TWSE, TPEX, and MOPS")
    for source in sources:
        if not source.get("source_id"):
            raise ValidationError("Each official-data source requires source_id")
        permissions = source.get("permissions", {})
        for field in (
            "technical_status",
            "internal_use_status",
            "public_display_status",
            "redistribution_status",
        ):
            if permissions.get(field) not in PERMISSION_STATES:
                raise ValidationError(f"Unsupported {source['source_key']}.{field}")
        endpoints = []
        for key in ("snapshot_endpoint", "history_endpoint"):
            if source.get(key):
                endpoints.append(source[key])
        if source.get("history_endpoint_template"):
                endpoints.append(
                    source["history_endpoint_template"].format(
                        yyyymmdd="20260101", date="2026/01/01", ticker="2330"
                    )
                )
        endpoints.extend(row["endpoint"] for row in source.get("disclosure_endpoints", []))
        for endpoint in endpoints:
            host = urllib.parse.urlparse(endpoint).hostname
            if host not in OFFICIAL_HOSTS or not endpoint.startswith("https://"):
                raise ValidationError(f"Endpoint is outside audited official hosts: {endpoint}")
    return config


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _error_details(error: Exception) -> tuple[str, str]:
    if isinstance(error, urllib.error.HTTPError):
        return f"HTTP_{error.code}", str(error.reason)[:1000]
    if isinstance(error, (TimeoutError, socket.timeout)):
        return "TIMEOUT", str(error)[:1000]
    if isinstance(error, json.JSONDecodeError):
        return "INVALID_JSON", str(error)[:1000]
    if isinstance(error, ValidationError):
        return "INVALID_RESPONSE", str(error)[:1000]
    if isinstance(error, urllib.error.URLError):
        return "NETWORK_ERROR", str(error.reason)[:1000]
    return "UNEXPECTED_ERROR", str(error)[:1000]


def _roc_date(value: object) -> str | None:
    cleaned = str(value or "").strip().replace("/", "")
    if len(cleaned) != 7 or not cleaned.isdigit():
        return None
    try:
        return datetime(
            int(cleaned[:3]) + 1911,
            int(cleaned[3:5]),
            int(cleaned[5:7]),
            tzinfo=TAIPEI,
        ).date().isoformat()
    except ValueError:
        return None


def _published_at(trade_date: str | None) -> str | None:
    if not trade_date:
        return None
    return datetime.fromisoformat(trade_date).replace(tzinfo=TAIPEI).isoformat()


def _announcement_at(date_value: object, time_value: object) -> str | None:
    date_text = _roc_date(date_value)
    if not date_text:
        return None
    digits = re.sub(r"\D", "", str(time_value or "")).zfill(6)[-6:]
    try:
        return datetime.fromisoformat(
            f"{date_text}T{digits[:2]}:{digits[2:4]}:{digits[4:6]}+08:00"
        ).isoformat()
    except ValueError:
        return _published_at(date_text)


def _number(value: object) -> int | None:
    cleaned = str(value or "").strip().replace(",", "")
    if not cleaned or cleaned in {"--", "---", "----", "N/A"}:
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


def _price(value: object) -> str | None:
    cleaned = str(value or "").strip().replace(",", "")
    return None if not cleaned or cleaned in {"--", "---", "----", "N/A"} else cleaned


def _company_ticker(value: object) -> str | None:
    ticker = str(value or "").strip()
    return ticker if COMPANY_TICKER.fullmatch(ticker) else None


def _history_months(reference: datetime, count: int) -> tuple[str, ...]:
    year = reference.year
    month = reference.month
    values = []
    for _ in range(max(1, count)):
        values.append(f"{year:04d}{month:02d}01")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return tuple(values)


class OfficialDataService:
    def __init__(
        self,
        connection: sqlite3.Connection,
        config: dict,
        *,
        transport: Transport | None = None,
        timeout: float = 60,
        now: datetime | None = None,
        test_mode: bool = False,
    ):
        self.connection = connection
        self.config = config
        self.transport = transport or _default_transport
        self.timeout = timeout
        self.now = now or datetime.now(TAIPEI)
        self.data_label = "SYNTHETIC_TEST_DATA" if test_mode else "REAL_OFFICIAL_SOURCE"
        self.sources = {row["source_key"]: row for row in config["sources"]}

    def sync_all(self) -> OfficialSyncResult:
        db_sources = self._validate_sources()
        self._save_permissions(db_sources)
        results: list[EndpointResult] = []

        twse = self.sources["TWSE"]
        results.append(
            self._collect_list_endpoint(
                db_sources["TWSE"],
                "TWSE",
                "twse_security_snapshot",
                twse["snapshot_endpoint"],
                lambda record, raw_id, fetched: self._store_twse_market_data(
                    db_sources["TWSE"], record, raw_id, fetched
                ),
                self._twse_snapshot_record,
                published_at_resolver=lambda record: _published_at(
                    _roc_date(record.get("Date"))
                ),
            )
        )
        for ticker in twse.get("history_tickers", []):
            for month in _history_months(self.now, int(self.config.get("history_months", 1))):
                endpoint = twse["history_endpoint_template"].format(
                    yyyymmdd=month, ticker=ticker
                )
                results.append(
                    self._collect_twse_history(db_sources["TWSE"], ticker, endpoint)
                )

        tpex = self.sources["TPEX"]
        results.append(
            self._collect_list_endpoint(
                db_sources["TPEX"],
                "TPEX",
                "tpex_mainboard_daily_close_quotes",
                tpex["snapshot_endpoint"],
                lambda record, raw_id, fetched: self._store_tpex_market_data(
                    db_sources["TPEX"], record, raw_id, fetched
                ),
                lambda record: record,
                published_at_resolver=lambda record: _published_at(
                    _roc_date(record.get("Date"))
                ),
            )
        )
        for ticker in tpex.get("history_tickers", []):
            for month in _history_months(self.now, int(self.config.get("history_months", 1))):
                endpoint = tpex["history_endpoint_template"].format(
                    date=f"{month[:4]}/{month[4:6]}/{month[6:]}", ticker=ticker
                )
                results.append(
                    self._collect_tpex_history(db_sources["TPEX"], ticker, endpoint)
                )

        mops = self.sources["MOPS"]
        for disclosure in mops["disclosure_endpoints"]:
            exchange = disclosure["exchange_code"]
            results.append(
                self._collect_list_endpoint(
                    db_sources["MOPS"],
                    "MOPS",
                    f"mops_daily_material_information_{exchange.lower()}",
                    disclosure["endpoint"],
                    lambda record, raw_id, fetched, exchange=exchange, endpoint=disclosure["endpoint"]: self._store_disclosure(
                        db_sources["MOPS"], exchange, record, raw_id, fetched, endpoint
                    ),
                    lambda record: record,
                    published_at_resolver=lambda record: _announcement_at(
                        record.get("發言日期"), record.get("發言時間")
                    ),
                )
            )
        return self._summary(tuple(results))

    def _validate_sources(self) -> dict[str, sqlite3.Row]:
        resolved = {}
        for key, config_source in self.sources.items():
            row = self.connection.execute(
                "SELECT * FROM sources WHERE source_id = ?", (config_source["source_id"],)
            ).fetchone()
            if row is None:
                raise ValidationError(f"Unknown source_id: {config_source['source_id']}")
            if row["collection_status"] != "API_VERIFIED":
                raise ValidationError(
                    f"Automatic collection denied for {config_source['source_id']}: "
                    f"collection_status={row['collection_status']}"
                )
            resolved[key] = row
        return resolved

    def _save_permissions(self, db_sources: dict[str, sqlite3.Row]) -> None:
        checked_at = self.now.astimezone(timezone.utc).isoformat()
        with self.connection:
            for key, source in self.sources.items():
                permissions = source["permissions"]
                self.connection.execute(
                    """
                    INSERT INTO official_source_permissions (
                        source_id, technical_status, internal_use_status,
                        public_display_status, redistribution_status,
                        evidence_url, checked_at, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(source_id) DO UPDATE SET
                        technical_status=excluded.technical_status,
                        internal_use_status=excluded.internal_use_status,
                        public_display_status=excluded.public_display_status,
                        redistribution_status=excluded.redistribution_status,
                        evidence_url=excluded.evidence_url,
                        checked_at=excluded.checked_at,
                        notes=excluded.notes,
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (
                        db_sources[key]["id"],
                        permissions["technical_status"],
                        permissions["internal_use_status"],
                        permissions["public_display_status"],
                        permissions["redistribution_status"],
                        permissions["evidence_url"],
                        checked_at,
                        permissions.get("notes", ""),
                    ),
                )

    @staticmethod
    def _twse_snapshot_record(record: dict) -> dict:
        return record

    def _collect_twse_history(
        self, source: sqlite3.Row, ticker: str, endpoint: str
    ) -> EndpointResult:
        def parser(document: object) -> list[dict]:
            if not isinstance(document, dict) or document.get("stat") != "OK":
                raise ValidationError(
                    f"TWSE history response is not OK: "
                    f"{document.get('stat') if isinstance(document, dict) else 'not-object'}"
                )
            fields = document.get("fields")
            rows = document.get("data")
            if not isinstance(fields, list) or not isinstance(rows, list):
                raise ValidationError("TWSE history response lacks fields/data arrays")
            return [dict(zip(fields, row, strict=False)) | {"股票代號": ticker} for row in rows]

        return self._collect_endpoint(
            source,
            "TWSE",
            f"twse_monthly_history_{ticker}",
            endpoint,
            parser,
            lambda record, raw_id, fetched: self._store_twse_history(
                source, record, raw_id, fetched
            ),
            published_at_resolver=lambda record: _published_at(_roc_date(record.get("日期"))),
        )

    def _collect_list_endpoint(
        self,
        source: sqlite3.Row,
        source_key: str,
        dataset: str,
        endpoint: str,
        store_record: Callable[[dict, str, str], bool],
        record_transform: Callable[[dict], dict],
        *,
        published_at_resolver: Callable[[dict], str | None] | None = None,
    ) -> EndpointResult:
        def parser(document: object) -> list[dict]:
            if not isinstance(document, list) or not all(isinstance(row, dict) for row in document):
                raise ValidationError(f"{dataset} response must be a JSON object array")
            return [record_transform(row) for row in document]

        return self._collect_endpoint(
            source,
            source_key,
            dataset,
            endpoint,
            parser,
            store_record,
            published_at_resolver=published_at_resolver,
        )

    def _collect_tpex_history(
        self, source: sqlite3.Row, ticker: str, endpoint: str
    ) -> EndpointResult:
        def parser(document: object) -> list[dict]:
            if not isinstance(document, dict) or document.get("stat") != "ok":
                raise ValidationError(
                    f"TPEx history response is not ok: "
                    f"{document.get('stat') if isinstance(document, dict) else 'not-object'}"
                )
            tables = document.get("tables")
            if not isinstance(tables, list) or not tables or not isinstance(tables[0], dict):
                raise ValidationError("TPEx history response lacks tables")
            rows = tables[0].get("data")
            if not isinstance(rows, list):
                raise ValidationError("TPEx history response lacks data rows")
            company_name = str(document.get("name") or ticker).strip()
            records = []
            for row in rows:
                if not isinstance(row, list) or len(row) < 9:
                    continue
                volume_thousands = _number(row[1])
                value_thousands = _number(row[2])
                records.append(
                    {
                        "股票代號": ticker,
                        "公司名稱": company_name,
                        "日期": row[0],
                        "成交股數": volume_thousands * 1000 if volume_thousands is not None else None,
                        "成交金額": value_thousands * 1000 if value_thousands is not None else None,
                        "開盤價": row[3],
                        "最高價": row[4],
                        "最低價": row[5],
                        "收盤價": row[6],
                        "漲跌價差": row[7],
                        "成交筆數": row[8],
                    }
                )
            return records

        return self._collect_endpoint(
            source,
            "TPEX",
            f"tpex_monthly_history_{ticker}",
            endpoint,
            parser,
            lambda record, raw_id, fetched: self._store_tpex_history(
                source, record, raw_id, fetched
            ),
            published_at_resolver=lambda record: _published_at(_roc_date(record.get("日期"))),
        )

    def _collect_endpoint(
        self,
        source: sqlite3.Row,
        source_key: str,
        dataset: str,
        endpoint: str,
        parser: Callable[[object], list[dict]],
        store_record: Callable[[dict, str, str], bool],
        *,
        published_at_resolver: Callable[[dict], str | None] | None = None,
    ) -> EndpointResult:
        run_id = str(uuid.uuid4())
        started_at = _utc_now()
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO collection_runs (
                    id, market_id, source_id, started_at, status, item_count,
                    collector_version, endpoint, dataset_name,
                    new_item_count, duplicate_item_count
                ) VALUES (?, ?, ?, ?, 'RUNNING', 0, ?, ?, ?, 0, 0)
                """,
                (
                    run_id,
                    source["market_id"],
                    source["id"],
                    started_at,
                    self.config["collector_version"],
                    endpoint,
                    dataset,
                ),
            )
        try:
            response = self.transport(endpoint, self.timeout)
            if response.status != 200:
                raise urllib.error.HTTPError(endpoint, response.status, "non-200 response", {}, None)
            document = json.loads(response.body.decode("utf-8-sig"))
            records = parser(document)
            fetched_at = _utc_now()
            raw_new = 0
            duplicates = 0
            normalized_new = 0
            evidence = EvidenceStore(self.connection)
            self.connection.execute("BEGIN")
            for record in records:
                original_content = json.dumps(
                    record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                )
                digest = content_sha256(original_content)
                raw_result = evidence.save_raw_item(
                    source_id=source["source_id"],
                    original_url=f"{endpoint}#record-sha256={digest}",
                    canonical_url=endpoint,
                    original_content=original_content,
                    published_at=(published_at_resolver(record) if published_at_resolver else None),
                    fetched_at=fetched_at,
                    mime_type=response.content_type.split(";", 1)[0],
                    raw_payload=record,
                    data_label=self.data_label,
                    collection_run_id=run_id,
                    commit=False,
                )
                raw_new += int(raw_result.created)
                duplicates += int(not raw_result.created)
                normalized_new += int(store_record(record, raw_result.id, fetched_at))
            finished_at = _utc_now()
            self.connection.execute(
                """
                UPDATE collection_runs SET finished_at=?, status='SUCCESS',
                    item_count=?, new_item_count=?, duplicate_item_count=?
                WHERE id=?
                """,
                (finished_at, len(records), raw_new, duplicates, run_id),
            )
            self.connection.commit()
            return EndpointResult(
                source_key, dataset, endpoint, "SUCCESS", len(records), normalized_new, duplicates
            )
        except Exception as error:
            self.connection.rollback()
            code, message = _error_details(error)
            with self.connection:
                self.connection.execute(
                    """
                    UPDATE collection_runs SET finished_at=?, status='FAILED',
                        error_code=?, error_message=? WHERE id=?
                    """,
                    (_utc_now(), code, message, run_id),
                )
            return EndpointResult(source_key, dataset, endpoint, "FAILED", 0, 0, 0, code, message)

    def _upsert_security(
        self,
        source: sqlite3.Row,
        exchange: str,
        ticker: str,
        company_name: str,
        raw_item_id: str,
        seen_at: str,
        mapping_status: str,
    ) -> tuple[str, bool]:
        security_id = f"{exchange}:{ticker}"
        existing = self.connection.execute(
            "SELECT id FROM official_securities WHERE id=?", (security_id,)
        ).fetchone()
        self.connection.execute(
            """
            INSERT INTO official_securities (
                id, market_id, exchange_code, ticker, company_name,
                mapping_status, first_source_id, latest_raw_item_id,
                first_seen_at, last_seen_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                company_name=CASE WHEN excluded.company_name <> '' THEN excluded.company_name
                                  ELSE official_securities.company_name END,
                latest_raw_item_id=excluded.latest_raw_item_id,
                last_seen_at=excluded.last_seen_at,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                security_id,
                source["market_id"],
                exchange,
                ticker,
                company_name or ticker,
                mapping_status,
                source["id"],
                raw_item_id,
                seen_at,
                seen_at,
            ),
        )
        return security_id, existing is None

    def _store_market_data(
        self,
        source: sqlite3.Row,
        exchange: str,
        ticker: str | None,
        company_name: str,
        trade_date: str | None,
        record: dict,
        raw_item_id: str,
        fetched_at: str,
    ) -> bool:
        if not ticker or not trade_date:
            return False
        security_id, _ = self._upsert_security(
            source, exchange, ticker, company_name, raw_item_id, fetched_at, "OFFICIAL_MARKET_DATA"
        )
        cursor = self.connection.execute(
            """
            INSERT INTO official_market_data_daily (
                id, security_id, market_id, exchange_code, ticker, trade_date,
                opening_price, highest_price, lowest_price, closing_price,
                price_change, trade_volume, trade_value, transaction_count,
                data_status, source_id, raw_item_id, collected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'EOD', ?, ?, ?)
            ON CONFLICT(security_id, trade_date) DO UPDATE SET
                opening_price=excluded.opening_price,
                highest_price=excluded.highest_price,
                lowest_price=excluded.lowest_price,
                closing_price=excluded.closing_price,
                price_change=excluded.price_change,
                trade_volume=excluded.trade_volume,
                trade_value=excluded.trade_value,
                transaction_count=excluded.transaction_count,
                source_id=excluded.source_id,
                raw_item_id=excluded.raw_item_id,
                collected_at=excluded.collected_at
            """,
            (
                str(uuid.uuid4()),
                security_id,
                source["market_id"],
                exchange,
                ticker,
                trade_date,
                _price(record.get("open")),
                _price(record.get("high")),
                _price(record.get("low")),
                _price(record.get("close")),
                _price(record.get("change")),
                _number(record.get("volume")),
                _number(record.get("value")),
                _number(record.get("transactions")),
                source["id"],
                raw_item_id,
                fetched_at,
            ),
        )
        return cursor.rowcount > 0

    def _store_twse_market_data(
        self, source: sqlite3.Row, record: dict, raw_item_id: str, fetched_at: str
    ) -> bool:
        return self._store_market_data(
            source,
            "TWSE",
            _company_ticker(record.get("Code")),
            str(record.get("Name") or "").strip(),
            _roc_date(record.get("Date")),
            {
                "open": record.get("OpeningPrice"),
                "high": record.get("HighestPrice"),
                "low": record.get("LowestPrice"),
                "close": record.get("ClosingPrice"),
                "change": record.get("Change"),
                "volume": record.get("TradeVolume"),
                "value": record.get("TradeValue"),
                "transactions": record.get("Transaction"),
            },
            raw_item_id,
            fetched_at,
        )

    def _store_twse_history(
        self, source: sqlite3.Row, record: dict, raw_item_id: str, fetched_at: str
    ) -> bool:
        ticker = _company_ticker(record.get("股票代號"))
        existing = self.connection.execute(
            "SELECT company_name FROM official_securities WHERE id=?", (f"TWSE:{ticker}",)
        ).fetchone() if ticker else None
        return self._store_market_data(
            source,
            "TWSE",
            ticker,
            existing["company_name"] if existing else (ticker or ""),
            _roc_date(record.get("日期")),
            {
                "open": record.get("開盤價"),
                "high": record.get("最高價"),
                "low": record.get("最低價"),
                "close": record.get("收盤價"),
                "change": record.get("漲跌價差"),
                "volume": record.get("成交股數"),
                "value": record.get("成交金額"),
                "transactions": record.get("成交筆數"),
            },
            raw_item_id,
            fetched_at,
        )

    def _store_tpex_market_data(
        self, source: sqlite3.Row, record: dict, raw_item_id: str, fetched_at: str
    ) -> bool:
        return self._store_market_data(
            source,
            "TPEX",
            _company_ticker(record.get("SecuritiesCompanyCode")),
            str(record.get("CompanyName") or "").strip(),
            _roc_date(record.get("Date")),
            {
                "open": record.get("Open"),
                "high": record.get("High"),
                "low": record.get("Low"),
                "close": record.get("Close"),
                "change": record.get("Change"),
                "volume": record.get("TradingShares"),
                "value": record.get("TransactionAmount"),
                "transactions": record.get("TransactionNumber"),
            },
            raw_item_id,
            fetched_at,
        )

    def _store_tpex_history(
        self, source: sqlite3.Row, record: dict, raw_item_id: str, fetched_at: str
    ) -> bool:
        ticker = _company_ticker(record.get("股票代號"))
        existing = self.connection.execute(
            "SELECT company_name FROM official_securities WHERE id=?", (f"TPEX:{ticker}",)
        ).fetchone() if ticker else None
        return self._store_market_data(
            source,
            "TPEX",
            ticker,
            existing["company_name"] if existing else str(record.get("公司名稱") or ticker or ""),
            _roc_date(record.get("日期")),
            {
                "open": record.get("開盤價"),
                "high": record.get("最高價"),
                "low": record.get("最低價"),
                "close": record.get("收盤價"),
                "change": record.get("漲跌價差"),
                "volume": record.get("成交股數"),
                "value": record.get("成交金額"),
                "transactions": record.get("成交筆數"),
            },
            raw_item_id,
            fetched_at,
        )

    def _store_disclosure(
        self,
        source: sqlite3.Row,
        exchange: str,
        record: dict,
        raw_item_id: str,
        fetched_at: str,
        endpoint: str,
    ) -> bool:
        raw_ticker = str(
            record.get("公司代號") or record.get("SecuritiesCompanyCode") or ""
        ).strip()
        ticker = _company_ticker(raw_ticker)
        company_name = str(record.get("公司名稱") or record.get("CompanyName") or ticker).strip()
        security_id = None
        if ticker:
            candidate_id = f"{exchange}:{ticker}"
            existing = self.connection.execute(
                "SELECT id FROM official_securities WHERE id=?", (candidate_id,)
            ).fetchone()
            mapping_status = (
                "MAPPED_EXISTING_SECURITY" if existing else "MAPPED_DISCLOSURE_SECURITY"
            )
            security_id, _ = self._upsert_security(
                source,
                exchange,
                ticker,
                company_name,
                raw_item_id,
                fetched_at,
                mapping_status,
            )
        else:
            ticker = raw_ticker or "UNKNOWN"
            mapping_status = "UNMAPPED_INVALID_CODE"
        announced_at = _announcement_at(record.get("發言日期"), record.get("發言時間"))
        announcement_date = _roc_date(record.get("發言日期"))
        event_date = _roc_date(record.get("事實發生日"))
        subject = str(record.get("主旨 ") or record.get("主旨") or "").strip()
        details = str(record.get("說明") or "").strip() or None
        clause = str(record.get("符合條款") or "").strip() or None
        stable = "|".join(
            (exchange, ticker, announcement_date or "UNKNOWN", announced_at or "UNKNOWN", subject)
        )
        disclosure_id = "MOPS:" + hashlib.sha256(stable.encode("utf-8")).hexdigest()[:32]
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO official_disclosures (
                id, security_id, market_id, exchange_code, ticker, company_name,
                announced_at, announcement_date, event_date, subject, details,
                clause, mapping_status, source_id, raw_item_id, official_url,
                collected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                disclosure_id,
                security_id,
                source["market_id"],
                exchange,
                ticker,
                company_name,
                announced_at,
                announcement_date,
                event_date,
                subject,
                details,
                clause,
                mapping_status,
                source["id"],
                raw_item_id,
                endpoint,
                fetched_at,
            ),
        )
        return cursor.rowcount == 1

    def _summary(self, results: tuple[EndpointResult, ...]) -> OfficialSyncResult:
        scalar = self.connection.execute
        return OfficialSyncResult(
            endpoint_results=results,
            twse_security_count=scalar(
                "SELECT COUNT(*) FROM official_securities WHERE exchange_code='TWSE'"
            ).fetchone()[0],
            tpex_security_count=scalar(
                "SELECT COUNT(*) FROM official_securities WHERE exchange_code='TPEX'"
            ).fetchone()[0],
            twse_market_data_count=scalar(
                "SELECT COUNT(*) FROM official_market_data_daily WHERE exchange_code='TWSE'"
            ).fetchone()[0],
            tpex_market_data_count=scalar(
                "SELECT COUNT(*) FROM official_market_data_daily WHERE exchange_code='TPEX'"
            ).fetchone()[0],
            disclosure_count=scalar("SELECT COUNT(*) FROM official_disclosures").fetchone()[0],
            disclosure_mapped_count=scalar(
                "SELECT COUNT(*) FROM official_disclosures WHERE security_id IS NOT NULL"
            ).fetchone()[0],
        )


def volume_history(
    connection: sqlite3.Connection, security_id: str, *, limit: int | None = None
) -> list[dict]:
    sql = """
        SELECT md.security_id, md.exchange_code, md.ticker, s.company_name,
               md.trade_date, md.trade_volume, md.trade_value,
               md.opening_price, md.highest_price, md.lowest_price,
               md.closing_price, md.price_change, md.raw_item_id
        FROM official_market_data_daily md
        JOIN official_securities s ON s.id=md.security_id
        WHERE md.security_id=?
        ORDER BY md.trade_date DESC
    """
    params: tuple = (security_id,)
    if limit is not None:
        sql += " LIMIT ?"
        params += (limit,)
    return [dict(row) for row in connection.execute(sql, params)]


def recent_disclosures(
    connection: sqlite3.Connection, security_id: str, *, limit: int = 20
) -> list[dict]:
    return [
        dict(row)
        for row in connection.execute(
            """
            SELECT d.id, d.security_id, d.exchange_code, d.ticker,
                   d.company_name, d.announced_at, d.event_date, d.subject,
                   d.details, d.mapping_status, d.raw_item_id, d.official_url
            FROM official_disclosures d
            WHERE d.security_id=?
            ORDER BY COALESCE(d.announced_at, d.announcement_date) DESC, d.id DESC
            LIMIT ?
            """,
            (security_id, limit),
        )
    ]


def official_data_status(connection: sqlite3.Connection) -> dict:
    permissions = [
        dict(row)
        for row in connection.execute(
            """
            SELECT s.source_id, s.publisher, p.technical_status,
                   p.internal_use_status, p.public_display_status,
                   p.redistribution_status, p.evidence_url, p.checked_at
            FROM official_source_permissions p
            JOIN sources s ON s.id=p.source_id
            ORDER BY s.source_id
            """
        )
    ]
    coverage = {}
    for exchange in ("TWSE", "TPEX"):
        row = connection.execute(
            """
            SELECT COUNT(DISTINCT security_id) AS securities,
                   COUNT(*) AS rows, MIN(trade_date) AS first_date,
                   MAX(trade_date) AS last_date
            FROM official_market_data_daily WHERE exchange_code=?
            """,
            (exchange,),
        ).fetchone()
        coverage[exchange] = dict(row)
    disclosure = connection.execute(
        """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN security_id IS NOT NULL THEN 1 ELSE 0 END) AS mapped,
               MIN(announcement_date) AS first_date,
               MAX(announcement_date) AS last_date
        FROM official_disclosures
        """
    ).fetchone()
    return {"coverage": coverage, "disclosures": dict(disclosure), "permissions": permissions}
