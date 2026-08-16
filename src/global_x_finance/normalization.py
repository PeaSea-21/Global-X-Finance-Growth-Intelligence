from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from .errors import ValidationError


UNKNOWN = "UNKNOWN"
NORMALIZATION_VERSION = "twse-normalizer-0.3.0"
SIGNAL_LABEL = "RULE_BASED_OFFICIAL_SIGNAL"
TOP_RANK_LIMIT = 10


@dataclass(frozen=True)
class NormalizationResult:
    normalized_new_count: int
    normalized_existing_count: int
    entity_new_count: int
    signal_new_count: int
    signal_existing_count: int
    total_normalized_count: int
    total_signal_count: int


def _text(value: Any) -> str:
    if value is None:
        return UNKNOWN
    cleaned = str(value).strip()
    return cleaned if cleaned else UNKNOWN


def _decimal(value: Any) -> Decimal | None:
    cleaned = _text(value)
    if cleaned == UNKNOWN or cleaned in {"--", "---", "N/A"}:
        return None
    try:
        return Decimal(cleaned.replace(",", ""))
    except InvalidOperation:
        return None


def _data_date(published_at: str | None) -> str:
    if not published_at:
        return UNKNOWN
    try:
        return datetime.fromisoformat(published_at.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return UNKNOWN


def freshness_status(data_date: str, *, today: str | None = None) -> str:
    if data_date == UNKNOWN:
        return "UNKNOWN_DATA_DATE"
    # Taiwan uses UTC+08:00 year-round. A fixed offset keeps the one-click
    # Windows demo independent of the optional IANA tzdata package.
    taiwan_time = timezone(timedelta(hours=8))
    local_today = today or datetime.now(taiwan_time).date().isoformat()
    if data_date == local_today:
        return "CURRENT_OFFICIAL_DATA"
    return "OFFICIAL_LATEST_AVAILABLE_DATA"


class TwseNormalizationService:
    def __init__(self, connection: sqlite3.Connection, config: dict):
        self.connection = connection
        self.config = config
        self.datasets_by_endpoint = {
            dataset["endpoint"]: dataset for dataset in config.get("datasets", [])
        }
        if not self.datasets_by_endpoint:
            raise ValidationError("TWSE dataset configuration is empty")

    def normalize_all(self, source_id: str | None = None) -> NormalizationResult:
        requested_source = source_id or self.config["source_id"]
        if requested_source != self.config["source_id"]:
            raise ValidationError(
                f"No audited normalization configuration for source_id: {requested_source}"
            )
        source = self.connection.execute(
            """
            SELECT s.id, s.source_id, s.publisher, s.market_id, m.country_code
            FROM sources s JOIN markets m ON m.id = s.market_id
            WHERE s.source_id = ?
            """,
            (requested_source,),
        ).fetchone()
        if source is None:
            raise ValidationError(f"Unknown source_id: {requested_source}")

        placeholders = ",".join("?" for _ in self.datasets_by_endpoint)
        raw_rows = self.connection.execute(
            f"""
            SELECT ri.*, cr.endpoint, cr.dataset_name
            FROM raw_items ri
            JOIN collection_runs cr ON cr.id = ri.collection_run_id
            WHERE ri.source_id = ? AND cr.endpoint IN ({placeholders})
            ORDER BY ri.created_at, ri.id
            """,
            (source["id"], *self.datasets_by_endpoint.keys()),
        ).fetchall()

        normalized_new = 0
        normalized_existing = 0
        entity_new = 0
        with self.connection:
            for raw in raw_rows:
                existing = self.connection.execute(
                    "SELECT id FROM normalized_items WHERE raw_item_id = ?", (raw["id"],)
                ).fetchone()
                if existing:
                    normalized_existing += 1
                    continue
                dataset = self.datasets_by_endpoint[raw["endpoint"]]
                normalized = self._map_record(raw, dataset, source)
                normalized_id = str(uuid.uuid4())
                self._insert_normalized(normalized_id, raw, source, normalized)
                normalized_new += 1

                entity_spec = normalized.pop("_entity", None)
                if entity_spec:
                    entity_id, created = self._upsert_entity(source, entity_spec)
                    entity_new += int(created)
                    self.connection.execute(
                        """
                        INSERT OR IGNORE INTO item_entities (
                            item_id, entity_id, relation_type, confidence
                        ) VALUES (?, ?, ?, 1.0)
                        """,
                        (normalized_id, entity_id, entity_spec["relation_type"]),
                    )

            signal_new, signal_existing = self._build_signal_cards(source)

        total_normalized = self.connection.execute(
            "SELECT COUNT(*) FROM normalized_items WHERE market_id = ?", (source["market_id"],)
        ).fetchone()[0]
        total_signals = self.connection.execute(
            "SELECT COUNT(*) FROM official_signal_cards WHERE market_id = ?",
            (source["market_id"],),
        ).fetchone()[0]
        return NormalizationResult(
            normalized_new_count=normalized_new,
            normalized_existing_count=normalized_existing,
            entity_new_count=entity_new,
            signal_new_count=signal_new,
            signal_existing_count=signal_existing,
            total_normalized_count=total_normalized,
            total_signal_count=total_signals,
        )

    def _map_record(self, raw: sqlite3.Row, dataset: dict, source: sqlite3.Row) -> dict:
        try:
            payload = json.loads(raw["raw_payload_json"])
        except json.JSONDecodeError as error:
            raise ValidationError(f"Raw Evidence {raw['id']} contains invalid JSON") from error
        if not isinstance(payload, dict):
            raise ValidationError(f"Raw Evidence {raw['id']} must contain a JSON object")

        base = {
            "market_id": source["market_id"],
            "market": source["country_code"],
            "dataset_id": dataset["dataset_id"],
            "data_date": _data_date(raw["published_at"]),
            "stock_code": UNKNOWN,
            "company_name": UNKNOWN,
            "opening_price": UNKNOWN,
            "highest_price": UNKNOWN,
            "lowest_price": UNKNOWN,
            "closing_price": UNKNOWN,
            "trade_volume": UNKNOWN,
            "trade_value": UNKNOWN,
            "price_change": UNKNOWN,
            "market_index_name": UNKNOWN,
            "market_index_close": UNKNOWN,
            "market_index_change_points": UNKNOWN,
            "market_index_change_percent": UNKNOWN,
            "industry_category": UNKNOWN,
            "company_count": UNKNOWN,
            "issued_shares": UNKNOWN,
            "foreign_mainland_shares": UNKNOWN,
            "foreign_holding_percentage": UNKNOWN,
        }
        dataset_id = dataset["dataset_id"]
        if dataset_id == "twse_listed_stock_daily_trading":
            base.update(
                record_type="LISTED_SECURITY_DAILY_TRADING",
                stock_code=_text(payload.get("Code")),
                company_name=_text(payload.get("Name")),
                opening_price=_text(payload.get("OpeningPrice")),
                highest_price=_text(payload.get("HighestPrice")),
                lowest_price=_text(payload.get("LowestPrice")),
                closing_price=_text(payload.get("ClosingPrice")),
                trade_volume=_text(payload.get("TradeVolume")),
                trade_value=_text(payload.get("TradeValue")),
                price_change=_text(payload.get("Change")),
            )
            base["title"] = f"{base['stock_code']} {base['company_name']} 上市日成交資訊"
            if base["stock_code"] != UNKNOWN:
                base["_entity"] = {
                    "entity_type": "LISTED_SECURITY",
                    "entity_key": f"TW:LISTED_SECURITY:{base['stock_code']}",
                    "canonical_name": base["company_name"],
                    "official_code": base["stock_code"],
                    "relation_type": "ABOUT_SECURITY",
                }
        elif dataset_id == "twse_market_close_statistics":
            base.update(
                record_type="MARKET_CLOSE_STATISTIC",
                market_index_name=_text(payload.get("指數")),
                market_index_close=_text(payload.get("收盤指數")),
                market_index_change_points=_text(payload.get("漲跌點數")),
                market_index_change_percent=_text(payload.get("漲跌百分比")),
            )
            base["title"] = f"{base['market_index_name']} 大盤統計"
            if base["market_index_name"] != UNKNOWN:
                base["_entity"] = {
                    "entity_type": "MARKET_INDEX",
                    "entity_key": f"TW:MARKET_INDEX:{base['market_index_name']}",
                    "canonical_name": base["market_index_name"],
                    "official_code": UNKNOWN,
                    "relation_type": "ABOUT_MARKET_INDEX",
                }
        elif dataset_id == "twse_foreign_mainland_holding_ratio":
            base.update(
                record_type="FOREIGN_HOLDING_BY_INDUSTRY",
                industry_category=_text(payload.get("IndustryCat")),
                company_count=_text(payload.get("Numbers")),
                issued_shares=_text(payload.get("ShareNumber")),
                foreign_mainland_shares=_text(payload.get("ForeignMainlandAreaShare")),
                foreign_holding_percentage=_text(payload.get("Percentage")),
            )
            base["title"] = f"{base['industry_category']} 外資及陸資持股比例"
            if base["industry_category"] != UNKNOWN:
                base["_entity"] = {
                    "entity_type": "INDUSTRY_CATEGORY",
                    "entity_key": f"TW:INDUSTRY:{base['industry_category']}",
                    "canonical_name": base["industry_category"],
                    "official_code": UNKNOWN,
                    "relation_type": "ABOUT_INDUSTRY",
                }
        else:
            raise ValidationError(f"Unsupported audited dataset_id: {dataset_id}")
        return base

    def _insert_normalized(
        self,
        normalized_id: str,
        raw: sqlite3.Row,
        source: sqlite3.Row,
        normalized: dict,
    ) -> None:
        entity_spec = normalized.get("_entity")
        body_values = {key: value for key, value in normalized.items() if not key.startswith("_")}
        metadata = {
            "raw_evidence_id": raw["id"],
            "official_url": raw["canonical_url"] or raw["original_url"],
            "fetched_at": raw["fetched_at"],
            "content_hash": raw["content_hash"],
            "mapping_status": "OFFICIAL_FIELD_MAPPING",
            "entity_key": entity_spec["entity_key"] if entity_spec else UNKNOWN,
        }
        columns = [
            "market_id", "dataset_id", "record_type", "data_date", "stock_code",
            "company_name", "opening_price", "highest_price", "lowest_price",
            "closing_price", "trade_volume", "trade_value", "price_change",
            "market_index_name", "market_index_close", "market_index_change_points",
            "market_index_change_percent", "industry_category", "company_count",
            "issued_shares", "foreign_mainland_shares", "foreign_holding_percentage",
        ]
        self.connection.execute(
            f"""
            INSERT INTO normalized_items (
                id, raw_item_id, language, title, body, author,
                normalized_published_at, normalization_version, metadata_json,
                {", ".join(columns)}
            ) VALUES ({", ".join("?" for _ in range(9 + len(columns)))})
            """,
            (
                normalized_id,
                raw["id"],
                "zh-Hant",
                normalized["title"],
                json.dumps(body_values, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                source["publisher"],
                raw["published_at"],
                NORMALIZATION_VERSION,
                json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                *(normalized[column] for column in columns),
            ),
        )

    def _upsert_entity(self, source: sqlite3.Row, spec: dict) -> tuple[str, bool]:
        existing = self.connection.execute(
            """
            SELECT id FROM entities
            WHERE market_id = ? AND entity_type = ? AND entity_key = ?
            """,
            (source["market_id"], spec["entity_type"], spec["entity_key"]),
        ).fetchone()
        if existing:
            return existing["id"], False
        entity_id = str(uuid.uuid4())
        identifiers = {
            "market": source["country_code"],
            "official_code": spec["official_code"],
            "publisher": source["publisher"],
            "mapping_status": "OFFICIAL_SOURCE_FIELD",
        }
        self.connection.execute(
            """
            INSERT INTO entities (
                id, entity_type, canonical_name, market_id, identifiers_json, entity_key
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                entity_id,
                spec["entity_type"],
                spec["canonical_name"],
                source["market_id"],
                json.dumps(identifiers, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                spec["entity_key"],
            ),
        )
        return entity_id, True

    def _build_signal_cards(self, source: sqlite3.Row) -> tuple[int, int]:
        created = 0
        existing = 0
        stock_rows = self.connection.execute(
            """
            SELECT ni.*, ri.canonical_url, ri.original_url,
                   ie.entity_id
            FROM normalized_items ni
            JOIN raw_items ri ON ri.id = ni.raw_item_id
            LEFT JOIN item_entities ie
              ON ie.item_id = ni.id AND ie.relation_type = 'ABOUT_SECURITY'
            WHERE ni.market_id = ?
              AND ni.record_type = 'LISTED_SECURITY_DAILY_TRADING'
              AND ni.normalization_version = ?
            """,
            (source["market_id"], NORMALIZATION_VERSION),
        ).fetchall()
        by_date: dict[str, list[sqlite3.Row]] = {}
        for row in stock_rows:
            by_date.setdefault(row["data_date"], []).append(row)

        for data_date, rows in by_date.items():
            created_count, existing_count = self._rank_cards(
                source,
                rows,
                data_date,
                field="trade_volume",
                signal_type="HIGH_TRADE_VOLUME",
                formula_version="TRADE_VOLUME_RANK_TOP10_V1",
                metric_label="成交量",
                risk_notice="僅為同一官方資料日期的日頻橫截面排名，不代表市場熱點、持續流動性或投資建議。",
            )
            created += created_count
            existing += existing_count
            created_count, existing_count = self._rank_cards(
                source,
                rows,
                data_date,
                field="trade_value",
                signal_type="HIGH_TRADE_VALUE",
                formula_version="TRADE_VALUE_RANK_TOP10_V1",
                metric_label="成交金額",
                risk_notice="僅為同一官方資料日期的日頻橫截面排名，不代表市場熱點、資金流向或投資建議。",
            )
            created += created_count
            existing += existing_count

            change_ranked: list[tuple[Decimal, sqlite3.Row, Decimal]] = []
            for row in rows:
                close = _decimal(row["closing_price"])
                change = _decimal(row["price_change"])
                if close is None or change is None:
                    continue
                previous_close = close - change
                if previous_close == 0:
                    continue
                rate = (change / previous_close) * Decimal("100")
                change_ranked.append((abs(rate), row, rate))
            change_ranked.sort(key=lambda item: (-item[0], item[1]["stock_code"]))
            valid_count = len(change_ranked)
            for rank, (_, row, rate) in enumerate(change_ranked[:TOP_RANK_LIMIT], start=1):
                metric = f"{rate.quantize(Decimal('0.0001'))}%"
                basis = (
                    f"官方 Change={row['price_change']}、ClosingPrice={row['closing_price']}；"
                    f"abs(Change / (ClosingPrice - Change)) × 100；"
                    f"同日 {valid_count} 筆可計算記錄中絕對值排名第 {rank}。"
                )
                was_created = self._insert_signal(
                    source,
                    row,
                    "NOTABLE_DAILY_CHANGE",
                    data_date,
                    metric,
                    basis,
                    "ABS_DAILY_CHANGE_RATE_RANK_TOP10_V1",
                    "根據官方日頻收盤資料計算，不是盤中或兩小時即時熱點，也不是買入／賣出信號，不構成投資建議。",
                )
                created += int(was_created)
                existing += int(not was_created)

        foreign_rows = self.connection.execute(
            """
            SELECT ni.*, ri.canonical_url, ri.original_url,
                   ie.entity_id
            FROM normalized_items ni
            JOIN raw_items ri ON ri.id = ni.raw_item_id
            LEFT JOIN item_entities ie
              ON ie.item_id = ni.id AND ie.relation_type = 'ABOUT_INDUSTRY'
            WHERE ni.market_id = ?
              AND ni.record_type = 'FOREIGN_HOLDING_BY_INDUSTRY'
              AND ni.normalization_version = ?
            """,
            (source["market_id"], NORMALIZATION_VERSION),
        ).fetchall()
        for row in foreign_rows:
            basis = (
                f"官方 Percentage={row['foreign_holding_percentage']}；"
                f"IndustryCat={row['industry_category']}；"
                f"ForeignMainlandAreaShare={row['foreign_mainland_shares']}；"
                f"ShareNumber={row['issued_shares']}。"
            )
            was_created = self._insert_signal(
                source,
                row,
                "FOREIGN_HOLDING_RATIO",
                row["data_date"],
                row["foreign_holding_percentage"],
                basis,
                "FOREIGN_HOLDING_RATIO_OFFICIAL_FIELD_V1",
                "此為產業類別彙總的官方外資及陸資持股比例，不是單一股票資金流向、買賣信號或投資建議。",
            )
            created += int(was_created)
            existing += int(not was_created)
        return created, existing

    def _rank_cards(
        self,
        source: sqlite3.Row,
        rows: list[sqlite3.Row],
        data_date: str,
        *,
        field: str,
        signal_type: str,
        formula_version: str,
        metric_label: str,
        risk_notice: str,
    ) -> tuple[int, int]:
        ranked = [(_decimal(row[field]), row) for row in rows]
        ranked = [(value, row) for value, row in ranked if value is not None]
        ranked.sort(key=lambda item: (-item[0], item[1]["stock_code"]))
        created = 0
        existing = 0
        for rank, (_, row) in enumerate(ranked[:TOP_RANK_LIMIT], start=1):
            basis = (
                f"官方 {field}={row[field]}；同一官方資料日期 {len(ranked)} 筆有效記錄中"
                f"{metric_label}排名第 {rank}，取前 {TOP_RANK_LIMIT} 名。"
            )
            was_created = self._insert_signal(
                source,
                row,
                signal_type,
                data_date,
                row[field],
                basis,
                formula_version,
                risk_notice,
            )
            created += int(was_created)
            existing += int(not was_created)
        return created, existing

    def _insert_signal(
        self,
        source: sqlite3.Row,
        row: sqlite3.Row,
        signal_type: str,
        data_date: str,
        metric_value: str,
        calculation_basis: str,
        formula_version: str,
        risk_notice: str,
    ) -> bool:
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO official_signal_cards (
                id, normalized_item_id, entity_id, market_id, signal_label,
                signal_type, data_date, metric_value, calculation_basis,
                formula_version, evidence_raw_item_id, official_url,
                freshness_status, risk_notice
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                row["id"],
                row["entity_id"],
                source["market_id"],
                SIGNAL_LABEL,
                signal_type,
                data_date,
                metric_value,
                calculation_basis,
                formula_version,
                row["raw_item_id"],
                row["canonical_url"] or row["original_url"],
                freshness_status(data_date),
                risk_notice,
            ),
        )
        return cursor.rowcount == 1
