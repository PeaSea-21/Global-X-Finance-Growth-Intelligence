from __future__ import annotations

import json
import re
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from .errors import ValidationError
from .evidence import EvidenceStore
from .official_data import (
    TAIPEI,
    OfficialDataService,
    Transport,
    _company_ticker,
    _default_transport,
    _error_details,
    _number,
    _published_at,
    _utc_now,
)


COLLECTOR_VERSION = "market-history-backfill-1.0.0"
TWSE_BATCH_TEMPLATE = (
    "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX"
    "?date={yyyymmdd}&type=ALLBUT0999&response=json"
)
TPEX_BATCH_TEMPLATE = (
    "https://www.tpex.org.tw/www/zh-tw/afterTrading/otc"
    "?date={date}&type=EW&response=json"
)
NULL_MARKERS = {"", "--", "---", "----", "N/A"}


@dataclass(frozen=True)
class MarketBatchResult:
    market: str
    trade_date: str
    endpoint: str
    status: str
    fetched_count: int
    stored_count: int
    raw_created: bool
    error_code: str | None = None
    error_message: str | None = None


def _clean_field(value: object) -> str:
    return re.sub(r"\s+", "", str(value or "")).replace("<br>", "")


def _has_price(value: object) -> bool:
    return str(value or "").strip().replace(",", "") not in NULL_MARKERS


def _signed_change(sign: object, value: object) -> object:
    change = str(value or "").strip()
    plain_sign = re.sub(r"<[^>]+>", "", str(sign or "")).strip()
    if not change or change in NULL_MARKERS:
        return change
    if plain_sign == "-" and not change.startswith("-"):
        return f"-{change}"
    if plain_sign == "+" and not change.startswith(("+", "-")):
        return f"+{change}"
    return change


def _candidate_weekdays(reference: date, maximum_calendar_days: int = 100) -> list[date]:
    return [
        reference - timedelta(days=offset)
        for offset in range(maximum_calendar_days + 1)
        if (reference - timedelta(days=offset)).weekday() < 5
    ]


class MarketHistoryBackfillService:
    def __init__(
        self,
        connection: sqlite3.Connection,
        config: dict,
        *,
        status_path: str | Path,
        target_days: int = 40,
        minimum_days: int = 20,
        transport: Transport | None = None,
        now: datetime | None = None,
    ):
        if target_days < minimum_days or minimum_days < 1:
            raise ValidationError("target_days must be >= minimum_days >= 1")
        self.connection = connection
        self.connection.execute("PRAGMA busy_timeout = 30000")
        self.config = config
        self.status_path = Path(status_path)
        self.target_days = target_days
        self.minimum_days = minimum_days
        self.transport = transport or _default_transport
        self.now = now or datetime.now(TAIPEI)
        self.official = OfficialDataService(
            connection, config, transport=self.transport, now=self.now
        )
        self.sources = self._resolve_sources()
        self.allowed_tickers = {
            market: {
                row[0]
                for row in connection.execute(
                    "SELECT ticker FROM official_securities WHERE exchange_code=?",
                    (market,),
                )
            }
            for market in ("TWSE", "TPEX")
        }

    def _resolve_sources(self) -> dict[str, sqlite3.Row]:
        resolved = {}
        source_config = {row["source_key"]: row for row in self.config["sources"]}
        for market in ("TWSE", "TPEX"):
            row = self.connection.execute(
                "SELECT * FROM sources WHERE source_id=?",
                (source_config[market]["source_id"],),
            ).fetchone()
            if row is None or row["collection_status"] != "API_VERIFIED":
                state = "MISSING" if row is None else row["collection_status"]
                raise ValidationError(f"Official history collection denied for {market}: {state}")
            resolved[market] = row
        return resolved

    def run(self) -> dict:
        self._close_interrupted_runs()
        status = self._load_status()
        status.update(
            {
                "status": "RUNNING",
                "target_trade_days": self.target_days,
                "minimum_trade_days": self.minimum_days,
                "updated_at": _utc_now(),
            }
        )
        status.setdefault("started_at", _utc_now())
        status.setdefault("records_written", 0)
        status.setdefault("markets", {})
        for market in ("TWSE", "TPEX"):
            status["markets"].setdefault(
                market, {"completed_dates": [], "no_data_dates": [], "failed_dates": {}}
            )
        self._refresh_progress_counts(status)
        self._write_status(status)

        # Resume recorded transient failures before walking further back in time.
        # Successful recovery replaces older fallback dates in the 40-day target set.
        for market in ("TWSE", "TPEX"):
            failed_dates = status["markets"][market]["failed_dates"]
            for failed_date in sorted(tuple(failed_dates), reverse=True):
                result = self.collect_market_date(market, date.fromisoformat(failed_date))
                if result.status == "SUCCESS":
                    status["markets"][market]["completed_dates"].append(failed_date)
                    self._normalize_completed_dates(status, market)
                    failed_dates.pop(failed_date, None)
                    status["records_written"] += result.stored_count
                    status["last_completed_market"] = market
                    status["last_completed_date"] = failed_date
                elif result.status == "NO_DATA":
                    failed_dates.pop(failed_date, None)
                    no_data = status["markets"][market]["no_data_dates"]
                    if failed_date not in no_data:
                        no_data.append(failed_date)
                else:
                    failed_dates[failed_date] = {
                        "error_code": result.error_code,
                        "error_message": result.error_message,
                    }
                status["updated_at"] = _utc_now()
                self._write_status(status)

        for candidate in _candidate_weekdays(self.now.date()):
            if all(
                len(status["markets"][market]["completed_dates"]) >= self.target_days
                for market in ("TWSE", "TPEX")
            ):
                break
            for market in ("TWSE", "TPEX"):
                completed = status["markets"][market]["completed_dates"]
                if len(completed) >= self.target_days:
                    continue
                trade_date = candidate.isoformat()
                if trade_date in completed and self._date_has_rows(market, trade_date):
                    continue
                if self._successful_run_exists(market, trade_date) or self._date_is_complete(
                    market, trade_date
                ):
                    completed.append(trade_date)
                    self._normalize_completed_dates(status, market)
                    status["last_completed_market"] = market
                    status["last_completed_date"] = trade_date
                    status["updated_at"] = _utc_now()
                    self._refresh_progress_counts(status)
                    self._write_status(status)
                    continue

                result = self.collect_market_date(market, candidate)
                if result.status == "SUCCESS":
                    completed.append(trade_date)
                    self._normalize_completed_dates(status, market)
                    status["last_completed_market"] = market
                    status["last_completed_date"] = trade_date
                    status["records_written"] += result.stored_count
                    status["markets"][market]["failed_dates"].pop(trade_date, None)
                elif result.status == "NO_DATA":
                    no_data = status["markets"][market]["no_data_dates"]
                    if trade_date not in no_data:
                        no_data.append(trade_date)
                else:
                    status["markets"][market]["failed_dates"][trade_date] = {
                        "error_code": result.error_code,
                        "error_message": result.error_message,
                    }
                status["updated_at"] = _utc_now()
                self._refresh_progress_counts(status)
                self._write_status(status)

        self.refresh_history_status()
        self._refresh_progress_counts(status)
        completed = all(
            len(status["markets"][market]["completed_dates"]) >= self.target_days
            and not status["markets"][market]["failed_dates"]
            for market in ("TWSE", "TPEX")
        )
        status["status"] = "COMPLETE" if completed else "PARTIAL"
        status["updated_at"] = _utc_now()
        status["audit"] = self.audit()
        self._write_status(status)
        return status

    def collect_market_date(self, market: str, candidate: date) -> MarketBatchResult:
        if market not in {"TWSE", "TPEX"}:
            raise ValidationError(f"Unsupported market: {market}")
        if candidate > self.now.date():
            raise ValidationError("Future trade dates are not allowed")
        expected = candidate.isoformat()
        endpoint = self._endpoint(market, candidate)
        dataset = self._dataset(market, expected)
        source = self.sources[market]
        run_id = str(uuid.uuid4())
        started_at = _utc_now()
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO collection_runs (
                    id, market_id, source_id, started_at, status, item_count,
                    collector_version, endpoint, dataset_name, batch_id,
                    new_item_count, duplicate_item_count
                ) VALUES (?, ?, ?, ?, 'RUNNING', 0, ?, ?, ?, ?, 0, 0)
                """,
                (
                    run_id,
                    source["market_id"],
                    source["id"],
                    started_at,
                    COLLECTOR_VERSION,
                    endpoint,
                    dataset,
                    f"{market}:{expected}",
                ),
            )
        try:
            response = self.transport(endpoint, 60)
            if response.status != 200:
                raise ValidationError(f"{market} batch returned HTTP {response.status}")
            original_content = response.body.decode("utf-8-sig")
            document = json.loads(original_content)
            records = self._parse(market, document, expected)
            if not records:
                with self.connection:
                    self.connection.execute(
                        """
                        UPDATE collection_runs SET finished_at=?, status='SUCCESS',
                            item_count=0, error_code='NO_TRADING_DATA'
                        WHERE id=?
                        """,
                        (_utc_now(), run_id),
                    )
                return MarketBatchResult(
                    market, expected, endpoint, "NO_DATA", 0, 0, False, "NO_TRADING_DATA"
                )

            fetched_at = _utc_now()
            self.connection.execute("BEGIN")
            raw = EvidenceStore(self.connection).save_raw_item(
                source_id=source["source_id"],
                original_url=endpoint,
                canonical_url=endpoint,
                original_content=original_content,
                published_at=_published_at(expected),
                fetched_at=fetched_at,
                mime_type=response.content_type.split(";", 1)[0],
                raw_payload=document,
                data_label="REAL_OFFICIAL_SOURCE",
                collection_run_id=run_id,
                commit=False,
            )
            stored = 0
            for record in records:
                stored += int(
                    self.official._store_market_data(
                        source,
                        market,
                        record["ticker"],
                        record["company_name"],
                        expected,
                        record,
                        raw.id,
                        fetched_at,
                    )
                )
            self.connection.execute(
                """
                UPDATE collection_runs SET finished_at=?, status='SUCCESS',
                    item_count=?, new_item_count=?, duplicate_item_count=?
                WHERE id=?
                """,
                (_utc_now(), len(records), int(raw.created), int(not raw.created), run_id),
            )
            self.connection.commit()
            return MarketBatchResult(
                market, expected, endpoint, "SUCCESS", len(records), stored, raw.created
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
            return MarketBatchResult(
                market, expected, endpoint, "FAILED", 0, 0, False, code, message
            )

    def _parse(self, market: str, document: object, expected_date: str) -> list[dict]:
        if not isinstance(document, dict):
            raise ValidationError(f"{market} batch response must be an object")
        response_date = str(document.get("date") or "")
        if response_date != expected_date.replace("-", ""):
            if not document.get("tables"):
                return []
            raise ValidationError(
                f"{market} batch date mismatch: expected {expected_date}, got {response_date}"
            )
        return (
            self._parse_twse(document)
            if market == "TWSE"
            else self._parse_tpex(document)
        )

    def _parse_twse(self, document: dict) -> list[dict]:
        if document.get("stat") != "OK":
            return []
        table = None
        for candidate in document.get("tables", []):
            fields = [_clean_field(field) for field in candidate.get("fields", [])]
            if "證券代號" in fields and "成交股數" in fields and "收盤價" in fields:
                table = candidate
                break
        if table is None:
            raise ValidationError("TWSE batch response lacks the security OHLCV table")
        fields = [_clean_field(field) for field in table["fields"]]
        records = []
        for values in table.get("data", []):
            row = dict(zip(fields, values, strict=False))
            ticker = _company_ticker(row.get("證券代號"))
            if ticker not in self.allowed_tickers["TWSE"]:
                continue
            record = {
                "ticker": ticker,
                "company_name": str(row.get("證券名稱") or ticker).strip(),
                "open": row.get("開盤價"),
                "high": row.get("最高價"),
                "low": row.get("最低價"),
                "close": row.get("收盤價"),
                "change": _signed_change(row.get("漲跌(+/-)"), row.get("漲跌價差")),
                "volume": row.get("成交股數"),
                "value": row.get("成交金額"),
                "transactions": row.get("成交筆數"),
            }
            if self._valid_ohlcv(record):
                records.append(record)
        return records

    def _parse_tpex(self, document: dict) -> list[dict]:
        if document.get("stat") != "ok":
            return []
        tables = document.get("tables") or []
        if not tables or not isinstance(tables[0].get("data"), list):
            raise ValidationError("TPEx batch response lacks the security OHLCV table")
        records = []
        for row in tables[0]["data"]:
            if not isinstance(row, list) or len(row) < 10:
                continue
            ticker = _company_ticker(row[0])
            if ticker not in self.allowed_tickers["TPEX"]:
                continue
            record = {
                "ticker": ticker,
                "company_name": str(row[1] or ticker).strip(),
                "close": row[2],
                "change": row[3],
                "open": row[4],
                "high": row[5],
                "low": row[6],
                "volume": row[7],
                "value": row[8],
                "transactions": row[9],
            }
            if self._valid_ohlcv(record):
                records.append(record)
        return records

    @staticmethod
    def _valid_ohlcv(record: dict) -> bool:
        return (
            all(_has_price(record.get(field)) for field in ("open", "high", "low", "close"))
            and _number(record.get("volume")) is not None
            and _number(record.get("volume")) >= 0
        )

    @staticmethod
    def _dataset(market: str, trade_date: str) -> str:
        return f"market_history_backfill_{market.lower()}_{trade_date.replace('-', '')}"

    @staticmethod
    def _endpoint(market: str, candidate: date) -> str:
        compact = candidate.strftime("%Y%m%d")
        if market == "TWSE":
            return TWSE_BATCH_TEMPLATE.format(yyyymmdd=compact)
        return TPEX_BATCH_TEMPLATE.format(date=candidate.strftime("%Y/%m/%d"))

    def _successful_run_exists(self, market: str, trade_date: str) -> bool:
        return self.connection.execute(
            """
            SELECT 1 FROM collection_runs
            WHERE collector_version=? AND dataset_name=?
              AND status='SUCCESS' AND item_count>0
            LIMIT 1
            """,
            (COLLECTOR_VERSION, self._dataset(market, trade_date)),
        ).fetchone() is not None

    def _date_has_rows(self, market: str, trade_date: str) -> bool:
        return self.connection.execute(
            "SELECT 1 FROM official_market_data_daily WHERE exchange_code=? AND trade_date=? LIMIT 1",
            (market, trade_date),
        ).fetchone() is not None

    def _date_is_complete(self, market: str, trade_date: str) -> bool:
        total = len(self.allowed_tickers[market])
        present = self.connection.execute(
            """
            SELECT COUNT(DISTINCT security_id)
            FROM official_market_data_daily
            WHERE exchange_code=? AND trade_date=?
            """,
            (market, trade_date),
        ).fetchone()[0]
        return total > 0 and present >= total

    def _close_interrupted_runs(self) -> None:
        with self.connection:
            self.connection.execute(
                """
                UPDATE collection_runs
                SET status='FAILED', finished_at=?, error_code='INTERRUPTED',
                    error_message='Previous market history backfill did not finish'
                WHERE collector_version=? AND status='RUNNING'
                """,
                (_utc_now(), COLLECTOR_VERSION),
            )

    def refresh_history_status(self) -> None:
        today = self.now.date().isoformat()
        with self.connection:
            self.connection.execute(
                """
                UPDATE official_market_data_daily
                SET data_status='UNKNOWN'
                WHERE opening_price IS NULL OR highest_price IS NULL
                   OR lowest_price IS NULL OR closing_price IS NULL
                   OR trade_volume IS NULL OR trade_date>?
                """,
                (today,),
            )
            self.connection.execute(
                """
                UPDATE official_securities
                SET history_trade_days=(
                        SELECT COUNT(DISTINCT md.trade_date)
                        FROM official_market_data_daily md
                        WHERE md.security_id=official_securities.id
                          AND md.data_status='EOD' AND md.trade_date<=?
                    ),
                    history_first_date=(
                        SELECT MIN(md.trade_date) FROM official_market_data_daily md
                        WHERE md.security_id=official_securities.id
                          AND md.data_status='EOD' AND md.trade_date<=?
                    ),
                    history_last_date=(
                        SELECT MAX(md.trade_date) FROM official_market_data_daily md
                        WHERE md.security_id=official_securities.id
                          AND md.data_status='EOD' AND md.trade_date<=?
                    ),
                    history_status=CASE WHEN (
                        SELECT COUNT(DISTINCT md.trade_date)
                        FROM official_market_data_daily md
                        WHERE md.security_id=official_securities.id
                          AND md.data_status='EOD' AND md.trade_date<=?
                    )>=? THEN 'READY' ELSE 'INSUFFICIENT_HISTORY' END,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (today, today, today, today, self.minimum_days),
            )

    def audit(self) -> dict:
        today = self.now.date().isoformat()
        markets = {}
        for market in ("TWSE", "TPEX"):
            row = self.connection.execute(
                """
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN history_trade_days>0 THEN 1 ELSE 0 END) AS with_history,
                       SUM(CASE WHEN history_trade_days>=? THEN 1 ELSE 0 END) AS ge_minimum,
                       SUM(CASE WHEN history_trade_days<? THEN 1 ELSE 0 END) AS insufficient,
                       MIN(history_first_date) AS first_date,
                       MAX(history_last_date) AS last_date
                FROM official_securities WHERE exchange_code=?
                """,
                (self.minimum_days, self.minimum_days, market),
            ).fetchone()
            markets[market] = dict(row)
        scalar = lambda sql, params=(): self.connection.execute(sql, params).fetchone()[0]
        return {
            "markets": markets,
            "market_data_records": scalar("SELECT COUNT(*) FROM official_market_data_daily"),
            "duplicate_security_dates": scalar(
                """
                SELECT COUNT(*) FROM (
                    SELECT security_id, trade_date, COUNT(*) n
                    FROM official_market_data_daily
                    GROUP BY security_id, trade_date HAVING n>1
                )
                """
            ),
            "null_ohlcv_eod": scalar(
                """
                SELECT COUNT(*) FROM official_market_data_daily
                WHERE data_status='EOD' AND (
                    opening_price IS NULL OR highest_price IS NULL OR
                    lowest_price IS NULL OR closing_price IS NULL OR trade_volume IS NULL
                )
                """
            ),
            "negative_volume": scalar(
                "SELECT COUNT(*) FROM official_market_data_daily WHERE trade_volume<0"
            ),
            "invalid_date": scalar(
                """
                SELECT COUNT(*) FROM official_market_data_daily
                WHERE trade_date NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
                """
            ),
            "future_date": scalar(
                "SELECT COUNT(*) FROM official_market_data_daily WHERE trade_date>?",
                (today,),
            ),
            "unmapped_security": scalar(
                """
                SELECT COUNT(*) FROM official_market_data_daily md
                LEFT JOIN official_securities s ON s.id=md.security_id
                WHERE s.id IS NULL
                """
            ),
        }

    def _load_status(self) -> dict:
        if not self.status_path.exists():
            return {}
        try:
            value = json.loads(self.status_path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _write_status(self, status: dict) -> None:
        self.status_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.status_path.with_suffix(self.status_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.status_path)

    def _normalize_completed_dates(self, status: dict, market: str) -> None:
        dates = sorted(set(status["markets"][market]["completed_dates"]), reverse=True)
        status["markets"][market]["completed_dates"] = dates[: self.target_days]

    def _refresh_progress_counts(self, status: dict) -> None:
        for market in ("TWSE", "TPEX"):
            total = len(self.allowed_tickers[market])
            completed = self.connection.execute(
                """
                SELECT COUNT(*) FROM official_securities
                WHERE exchange_code=? AND history_trade_days>=?
                """,
                (market, self.minimum_days),
            ).fetchone()[0]
            status[f"{market}_total"] = total
            status[f"{market}_completed"] = completed


def run_market_history_backfill(
    connection: sqlite3.Connection,
    config: dict,
    *,
    status_path: str | Path,
    target_days: int = 40,
    minimum_days: int = 20,
    transport: Transport | None = None,
    now: datetime | None = None,
) -> dict:
    return MarketHistoryBackfillService(
        connection,
        config,
        status_path=status_path,
        target_days=target_days,
        minimum_days=minimum_days,
        transport=transport,
        now=now,
    ).run()
