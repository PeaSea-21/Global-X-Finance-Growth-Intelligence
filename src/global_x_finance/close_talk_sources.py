from __future__ import annotations

import json
import math
import re
import sqlite3
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable


TAIPEI = timezone(timedelta(hours=8))
USER_AGENT = "BEN-Radar-Close-Talk/0.1 (+bounded-official-post-close-collector)"

CLOSE_TALK_DATASETS = (
    {
        "dataset_id": "TWSE_INDEX_AND_SECTORS",
        "source_name": "臺灣證券交易所",
        "source_class": "OFFICIAL",
        "required": False,
        "phase": "ENHANCEMENT",
        "url": "https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX",
        "endpoints": [
            {
                "role": "primary",
                "url": "https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX",
            },
            {
                "role": "same_day_fallback",
                "url_template": "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={yyyymmdd}&type=ALLBUT0999&response=json",
            },
        ],
        "parser": "twse_indices",
        "availability": "TWSE dated afterTrading endpoint is usually usable shortly after close; primary OpenAPI may lag.",
    },
    {
        "dataset_id": "TPEX_INDEX",
        "source_name": "證券櫃檯買賣中心",
        "source_class": "OFFICIAL",
        "required": False,
        "phase": "ENHANCEMENT",
        "url": "https://www.tpex.org.tw/openapi/v1/tpex_daily_trading_index",
        "endpoints": [
            {
                "role": "primary",
                "url": "https://www.tpex.org.tw/openapi/v1/tpex_daily_trading_index",
            },
        ],
        "parser": "tpex_index",
        "availability": "TPEx OpenAPI is polled after the EOD rows; if it still exposes the prior session it stays UNKNOWN.",
    },
    {
        "dataset_id": "TWSE_INSTITUTIONAL_FLOW",
        "source_name": "臺灣證券交易所",
        "source_class": "OFFICIAL",
        "required": False,
        "phase": "ENHANCEMENT",
        "url_template": "https://www.twse.com.tw/rwd/zh/fund/BFI82U?dayDate={yyyymmdd}&type=day&response=json",
        "parser": "twse_institutional",
    },
    {
        "dataset_id": "TPEX_INSTITUTIONAL_FLOW",
        "source_name": "證券櫃檯買賣中心",
        "source_class": "OFFICIAL",
        "required": False,
        "phase": "ENHANCEMENT",
        "url": "https://www.tpex.org.tw/openapi/v1/tpex_3insti_summary",
        "parser": "tpex_institutional",
    },
    {
        "dataset_id": "TWSE_MARGIN_SHORT",
        "source_name": "臺灣證券交易所",
        "source_class": "OFFICIAL",
        "required": False,
        "phase": "ENHANCEMENT",
        "url_template": "https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN?date={yyyymmdd}&selectType=ALL&response=json",
        "parser": "twse_margin",
    },
    {
        "dataset_id": "TPEX_MARGIN_SHORT",
        "source_name": "證券櫃檯買賣中心",
        "source_class": "OFFICIAL",
        "required": False,
        "phase": "ENHANCEMENT",
        "url": "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_margin_balance",
        "parser": "tpex_margin",
    },
)


class SourcePending(ValueError):
    pass


Fetcher = Callable[[str, float], Any]


def _default_fetcher(url: str, timeout: float) -> Any:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8-sig"))


def _roc_date(value: Any) -> str | None:
    text = str(value or "").strip().replace("/", "")
    if len(text) != 7 or not text.isdigit():
        return None
    try:
        return date(int(text[:3]) + 1911, int(text[3:5]), int(text[5:7])).isoformat()
    except ValueError:
        return None


def _twse_date(value: Any) -> str | None:
    text = str(value or "").strip().replace("/", "").replace("-", "")
    if len(text) == 8 and text.isdigit():
        try:
            return date(int(text[:4]), int(text[4:6]), int(text[6:8])).isoformat()
        except ValueError:
            return None
    return _roc_date(text)


def _integer(value: Any) -> int | None:
    text = str(value or "").strip().replace(",", "")
    if not text or text in {"--", "---", "N/A"}:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _decimal(value: Any) -> float | None:
    text = str(value or "").strip().replace(",", "")
    if not text or text in {"--", "---", "N/A"}:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def _assert_trade_date(actual: str | None, expected: str, dataset_id: str) -> None:
    if actual != expected:
        raise SourcePending(f"{dataset_id} latest trade date is {actual or 'UNKNOWN'}, expected {expected}")


def _parse_twse_indices(document: Any, trade_date: str) -> dict[str, Any]:
    if not isinstance(document, list):
        raise ValueError("TWSE index response is not a list")
    rows = [row for row in document if _roc_date(row.get("日期")) == trade_date]
    if not rows:
        latest = max((_roc_date(row.get("日期")) or "" for row in document), default=None)
        _assert_trade_date(latest, trade_date, "TWSE_INDEX_AND_SECTORS")
    weighted = next((row for row in rows if row.get("指數") == "發行量加權股價指數"), None)
    if weighted is None:
        raise ValueError("TWSE weighted index is missing")
    index_rows = [
        {
            "name": str(row.get("指數") or "").strip(),
            "close": _decimal(row.get("收盤指數")),
            "change_points": _decimal(row.get("漲跌點數")),
            "change_pct": _decimal(row.get("漲跌百分比")),
        }
        for row in rows
        if str(row.get("指數") or "").strip()
    ]
    sector_rows = [
        row for row in index_rows
        if "類指數" in row["name"] and row["change_pct"] is not None
    ]
    sector_rows.sort(key=lambda row: row["change_pct"], reverse=True)
    return {
        "weighted_index": next(row for row in index_rows if row["name"] == "發行量加權股價指數"),
        "top_sectors": sector_rows[:5],
        "bottom_sectors": list(reversed(sector_rows[-5:])),
        "index_record_count": len(index_rows),
    }


def _parse_twse_indices_rwd(document: Any, trade_date: str) -> dict[str, Any]:
    """Parse TWSE's dated afterTrading response used when OpenAPI lags."""
    if not isinstance(document, dict) or not isinstance(document.get("tables"), list):
        raise ValueError("TWSE dated index response is not an object with tables")
    actual = _twse_date(document.get("date"))
    if actual and actual != trade_date:
        _assert_trade_date(actual, trade_date, "TWSE_INDEX_AND_SECTORS")
    rows: list[dict[str, Any]] = []
    for table in document["tables"]:
        fields = [str(value) for value in (table.get("fields") or [])]
        data = table.get("data") or []
        if not fields or "指數" not in fields:
            continue
        positions = {field: index for index, field in enumerate(fields)}
        for raw in data:
            if len(raw) <= max(positions.values(), default=0):
                continue
            name = str(raw[positions["指數"]] or "").strip()
            if not name:
                continue
            close = _decimal(raw[positions.get("收盤指數", 0)])
            change_points = _decimal(raw[positions.get("漲跌點數", 0)])
            change_pct = _decimal(raw[positions.get("漲跌百分比(%)", 0)])
            sign = str(raw[positions.get("漲跌(+/-)", 0)] or "")
            if "-" in re.sub(r"<[^>]+>", "", sign):
                if change_points is not None:
                    change_points = -abs(change_points)
                if change_pct is not None:
                    change_pct = -abs(change_pct)
            rows.append({
                "name": name,
                "close": close,
                "change_points": change_points,
                "change_pct": change_pct,
            })
    if not rows:
        raise ValueError("TWSE dated index rows are missing")
    sector_rows = [
        row for row in rows
        if "類指數" in row["name"] and row["change_pct"] is not None
    ]
    sector_rows.sort(key=lambda row: row["change_pct"], reverse=True)
    weighted = next((row for row in rows if row["name"] == "發行量加權股價指數"), None)
    if weighted is None:
        raise ValueError("TWSE weighted index is missing")
    return {
        "weighted_index": weighted,
        "top_sectors": sector_rows[:5],
        "bottom_sectors": list(reversed(sector_rows[-5:])),
        "index_record_count": len(rows),
    }


def _parse_tpex_index(document: Any, trade_date: str) -> dict[str, Any]:
    if not isinstance(document, list):
        raise ValueError("TPEX index response is not a list")
    row = next((item for item in document if _roc_date(item.get("Date")) == trade_date), None)
    if row is None:
        latest = max((_roc_date(item.get("Date")) or "" for item in document), default=None)
        _assert_trade_date(latest, trade_date, "TPEX_INDEX")
    return {
        "index_close": _decimal(row.get("TPExIndex")),
        "change_points": _decimal(row.get("Change")),
        "trade_volume": _integer(row.get("TradeVolume")),
        "trade_value": _integer(row.get("TradeAmount")),
        "transactions": _integer(row.get("NumberOfTransactions")),
    }


def _parse_twse_institutional(document: Any, trade_date: str) -> dict[str, Any]:
    actual = str(document.get("date") or "")
    actual = f"{actual[:4]}-{actual[4:6]}-{actual[6:8]}" if len(actual) == 8 else None
    _assert_trade_date(actual, trade_date, "TWSE_INSTITUTIONAL_FLOW")
    if document.get("stat") != "OK":
        raise ValueError("TWSE institutional response is not OK")
    rows = {
        str(row[0]).strip(): _integer(row[3])
        for row in document.get("data", [])
        if len(row) >= 4
    }
    return {
        "foreign_net": rows.get("外資及陸資(不含外資自營商)"),
        "investment_trust_net": rows.get("投信"),
        "dealer_proprietary_net": rows.get("自營商(自行買賣)"),
        "dealer_hedge_net": rows.get("自營商(避險)"),
        "total_net": rows.get("合計"),
        "unit": "TWD",
    }


def _parse_tpex_institutional(document: Any, trade_date: str) -> dict[str, Any]:
    if not isinstance(document, list):
        raise ValueError("TPEX institutional response is not a list")
    rows = [row for row in document if _roc_date(row.get("Date")) == trade_date]
    if not rows:
        latest = max((_roc_date(row.get("Date")) or "" for row in document), default=None)
        _assert_trade_date(latest, trade_date, "TPEX_INSTITUTIONAL_FLOW")
    values = {str(row.get("Investor") or "").strip(): _integer(row.get("Net")) for row in rows}
    return {
        "foreign_net": values.get("外資及陸資合計"),
        "investment_trust_net": values.get("投信"),
        "dealer_net": values.get("自營商合計"),
        "total_net": values.get("三大法人合計*"),
        "unit": "TWD",
    }


def _parse_twse_margin(document: Any, trade_date: str) -> dict[str, Any]:
    actual = str(document.get("date") or "")
    actual = f"{actual[:4]}-{actual[4:6]}-{actual[6:8]}" if len(actual) == 8 else None
    _assert_trade_date(actual, trade_date, "TWSE_MARGIN_SHORT")
    if document.get("stat") != "OK" or not document.get("tables"):
        raise ValueError("TWSE margin response is not OK")
    rows = {str(row[0]).strip(): row for row in document["tables"][0].get("data", []) if len(row) >= 6}
    margin_units = rows.get("融資(交易單位)", [])
    short_units = rows.get("融券(交易單位)", [])
    margin_value = rows.get("融資金額(仟元)", [])
    return {
        "margin_balance_units_previous": _integer(margin_units[4]) if margin_units else None,
        "margin_balance_units_current": _integer(margin_units[5]) if margin_units else None,
        "short_balance_units_previous": _integer(short_units[4]) if short_units else None,
        "short_balance_units_current": _integer(short_units[5]) if short_units else None,
        "margin_value_thousand_twd_previous": _integer(margin_value[4]) if margin_value else None,
        "margin_value_thousand_twd_current": _integer(margin_value[5]) if margin_value else None,
    }


def _parse_tpex_margin(document: Any, trade_date: str) -> dict[str, Any]:
    if not isinstance(document, list):
        raise ValueError("TPEX margin response is not a list")
    rows = [row for row in document if _roc_date(row.get("Date")) == trade_date]
    if not rows:
        latest = max((_roc_date(row.get("Date")) or "" for row in document), default=None)
        _assert_trade_date(latest, trade_date, "TPEX_MARGIN_SHORT")

    def total(field: str) -> int:
        return sum(_integer(row.get(field)) or 0 for row in rows)

    return {
        "security_count": len(rows),
        "margin_balance_units_previous": total("MarginPurchaseBalancePreviousDay"),
        "margin_balance_units_current": total("MarginPurchaseBalance"),
        "short_balance_units_previous": total("ShortSaleBalancePreviousDay"),
        "short_balance_units_current": total("ShortSaleBalance"),
    }


PARSERS = {
    "twse_indices": _parse_twse_indices,
    "twse_indices_rwd": _parse_twse_indices_rwd,
    "tpex_index": _parse_tpex_index,
    "twse_institutional": _parse_twse_institutional,
    "tpex_institutional": _parse_tpex_institutional,
    "twse_margin": _parse_twse_margin,
    "tpex_margin": _parse_tpex_margin,
}


def market_breadth(connection: sqlite3.Connection, trade_date: str) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for exchange in ("TWSE", "TPEX"):
        rows = connection.execute(
            """SELECT price_change, trade_value FROM official_market_data_daily
               WHERE exchange_code=? AND trade_date=? AND data_status='EOD'""",
            (exchange, trade_date),
        )
        advances = declines = unchanged = unknown = 0
        turnover = 0
        for row in rows:
            change = _decimal(row["price_change"])
            if change is None:
                unknown += 1
            elif change > 0:
                advances += 1
            elif change < 0:
                declines += 1
            else:
                unchanged += 1
            turnover += int(row["trade_value"] or 0)
        observed = advances + declines + unchanged + unknown
        output[exchange] = {
            "advances": advances,
            "declines": declines,
            "unchanged": unchanged,
            "unknown_change": unknown,
            "observed_securities": observed,
            "covered_security_trade_value": turnover,
            "trade_value_scope": "SUM_OF_STORED_EOD_SECURITY_ROWS_NOT_FULL_MARKET_TURNOVER",
        }
    if any(not row["observed_securities"] for row in output.values()):
        raise SourcePending(f"market EOD breadth is incomplete for {trade_date}")
    return output


def _dataset_url(dataset: dict[str, Any], trade_date: str) -> str:
    return dataset.get("url") or dataset["url_template"].format(
        yyyymmdd=trade_date.replace("-", "")
    )


def _dataset_endpoints(dataset: dict[str, Any], trade_date: str) -> list[dict[str, str]]:
    configured = dataset.get("endpoints")
    if not configured:
        return [{"role": "primary", "url": _dataset_url(dataset, trade_date)}]
    result = []
    for endpoint in configured:
        url = endpoint.get("url") or endpoint.get("url_template", "").format(
            yyyymmdd=trade_date.replace("-", "")
        )
        if url:
            result.append({"role": endpoint.get("role", "fallback"), "url": url})
    return result


def collect_close_talk_source_pack(
    connection: sqlite3.Connection,
    trade_date: str,
    *,
    fetcher: Fetcher | None = None,
    now: datetime | None = None,
    timeout: float = 40,
) -> dict[str, Any]:
    date.fromisoformat(trade_date)
    fetcher = fetcher or _default_fetcher
    collected_at = (now or datetime.now(TAIPEI)).astimezone(TAIPEI).isoformat()
    results: list[dict[str, Any]] = []

    try:
        facts = market_breadth(connection, trade_date)
        results.append({
            "dataset_id": "MARKET_BREADTH_AND_TURNOVER",
            "source_name": "TWSE/TPEx official EOD derived",
            "source_class": "DERIVED_FROM_OFFICIAL",
            "required": True,
            "phase": "BASE",
            "status": "READY",
            "data_as_of": trade_date,
            "source_url": None,
            "facts": facts,
        })
    except SourcePending as error:
        results.append({
            "dataset_id": "MARKET_BREADTH_AND_TURNOVER",
            "source_name": "TWSE/TPEx official EOD derived",
            "source_class": "DERIVED_FROM_OFFICIAL",
            "required": True,
            "status": "SOURCE_PENDING",
            "data_as_of": None,
            "source_url": None,
            "error": str(error),
        })

    def collect_one(dataset: dict[str, Any]) -> dict[str, Any]:
        endpoints = _dataset_endpoints(dataset, trade_date)
        base = {
            "dataset_id": dataset["dataset_id"],
            "source_name": dataset["source_name"],
            "source_class": dataset["source_class"],
            "required": dataset["required"],
            "phase": dataset.get("phase", "ENHANCEMENT"),
            "source_url": endpoints[0]["url"],
            "availability": dataset.get("availability"),
        }
        attempts = []
        last_error: Exception | None = None
        for endpoint in endpoints:
            try:
                document = fetcher(endpoint["url"], timeout)
                parser_name = dataset["parser"]
                if endpoint["role"] == "same_day_fallback" and dataset["dataset_id"] == "TWSE_INDEX_AND_SECTORS":
                    parser_name = "twse_indices_rwd"
                facts = PARSERS[parser_name](document, trade_date)
                attempts.append({"role": endpoint["role"], "url": endpoint["url"], "status": "READY"})
                return {
                    **base, "status": "READY", "data_as_of": trade_date,
                    "facts": facts, "source_url": endpoint["url"], "source_endpoint_role": endpoint["role"],
                    "attempts": attempts,
                }
            except SourcePending as error:
                last_error = error
                attempts.append({"role": endpoint["role"], "url": endpoint["url"], "status": "SOURCE_PENDING", "error": str(error)[:500]})
            except Exception as error:
                last_error = error
                attempts.append({"role": endpoint["role"], "url": endpoint["url"], "status": "FAILED", "error": f"{type(error).__name__}: {str(error)[:500]}"})
        status = "SOURCE_PENDING" if isinstance(last_error, SourcePending) else "FAILED"
        error_text = str(last_error)[:500] if last_error else "no endpoint configured"
        return {**base, "status": status, "data_as_of": None, "error": error_text, "attempts": attempts}

    with ThreadPoolExecutor(max_workers=len(CLOSE_TALK_DATASETS)) as executor:
        futures = {executor.submit(collect_one, dataset): dataset for dataset in CLOSE_TALK_DATASETS}
        for future in as_completed(futures):
            results.append(future.result())

    order = {"MARKET_BREADTH_AND_TURNOVER": 0, **{
        row["dataset_id"]: index for index, row in enumerate(CLOSE_TALK_DATASETS, start=1)
    }}
    results.sort(key=lambda row: order[row["dataset_id"]])
    required_ready = all(row["status"] == "READY" for row in results if row["required"])
    base_ready = all(row["status"] == "READY" for row in results if row.get("phase") == "BASE")
    all_ready = all(row["status"] == "READY" for row in results)
    missing = [row["dataset_id"] for row in results if row["status"] != "READY"]
    return {
        "schema_version": "ben-close-talk-source-pack.v0.1",
        "market_session_date": trade_date,
        "collected_at": collected_at,
        "status": "READY" if required_ready else "SOURCE_PENDING",
        "base_status": "READY" if base_ready else "SOURCE_PENDING",
        "enhancement_status": "READY" if all_ready else "SOURCE_PENDING",
        "generation_stage": "BASE_DRAFT_ALLOWED" if base_ready else "BLOCKED",
        "coverage_status": "COMPLETE_FOR_CASH_MARKET_BASE" if all_ready else "BASE_READY_OPTIONAL_PENDING" if base_ready else "INCOMPLETE_REQUIRED",
        "event_lookback_hours": 48,
        "datasets": results,
        "missing_datasets": missing,
        "known_not_connected": [
            "TAIFEX futures close/basis/open interest",
            "TAIFEX institutional futures positions",
            "TAIFEX Put/Call ratio and options positioning",
            "securities lending context",
        ],
        "fact_boundary": "Only READY rows with matching market_session_date may be used as current-session facts.",
        "source_schedule": {
            "base_collection": "13:35-13:50 Asia/Taipei: TWSE/TPEx same-session EOD rows, breadth, 48-hour news and MOPS",
            "enhancement_poll_1": "14:05 Asia/Taipei: dated index/sector and institutional-flow retries",
            "enhancement_poll_2": "14:45 Asia/Taipei: final official index/flow/margin retry and comprehensive 48-hour search",
            "stale_data_policy": "A prior-session response remains UNKNOWN and never becomes today's fact.",
        },
    }
