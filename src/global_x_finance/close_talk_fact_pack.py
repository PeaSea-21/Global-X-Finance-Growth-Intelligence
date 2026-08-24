from __future__ import annotations

import json
import math
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

from .ben_radar import NEWS_SOURCES


TAIPEI = timezone(timedelta(hours=8))
TW_MARKET_TERMS = (
    "台股", "臺股", "台積電", "聯發科", "鴻海", "加權指數", "櫃買", "外資",
    "投信", "三大法人", "融資", "融券", "半導體", "記憶體", "dram", "pcb",
    "cpo", "航運", "金融股", "twse", "tpex", "tsmc", "mediatek", "foxconn",
)


def _parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def _within_window(value: Any, *, start: datetime, end: datetime) -> bool:
    parsed = _parse_time(value)
    return parsed is not None and start <= parsed.astimezone(TAIPEI) <= end


def _source_diverse(
    rows: Iterable[dict[str, Any]], *, limit: int, group_field: str, per_group: int
) -> list[dict[str, Any]]:
    selected = []
    counts: dict[str, int] = {}
    for row in rows:
        group = str(row.get(group_field) or "UNKNOWN")
        if counts.get(group, 0) >= per_group:
            continue
        selected.append(row)
        counts[group] = counts.get(group, 0) + 1
        if len(selected) >= limit:
            break
    return selected


def _title_relevance(title: str, market: str, published_at: datetime, as_of: datetime) -> float:
    lowered = f" {title.casefold()} "
    term_hits = sum(term in lowered for term in TW_MARKET_TERMS)
    hours = max(0.0, (as_of - published_at.astimezone(TAIPEI)).total_seconds() / 3600)
    recency = max(0.0, 48.0 - hours)
    return recency + term_hits * 12 + (18 if market == "TW" else 0)


def _news_leads(
    connection: sqlite3.Connection, *, start: datetime, as_of: datetime
) -> list[dict[str, Any]]:
    importance = {row["key"]: int(row["importance"]) for row in NEWS_SOURCES}
    rows = []
    for raw in connection.execute("SELECT * FROM ben_news_items ORDER BY published_at DESC"):
        row = dict(raw)
        published = _parse_time(row.get("published_at"))
        if published is None or not _within_window(row["published_at"], start=start, end=as_of):
            continue
        title = str(row.get("original_title") or "")
        score = _title_relevance(title, row.get("market") or "", published, as_of)
        score += importance.get(row.get("source_key"), 10)
        rows.append({
            "evidence_id": f"NEWS:{row['id']}",
            "evidence_class": "MEDIA_REPORT",
            "epistemic_status": "REPORTED",
            "source_key": row["source_key"],
            "source_name": row["source_name"],
            "title": title,
            "published_at": row["published_at"],
            "fetched_at": row.get("fetched_at"),
            "url": row["original_url"],
            "summary": row.get("public_summary"),
            "market": row.get("market"),
            "selection_score": round(score, 3),
        })
    rows.sort(key=lambda row: (-row["selection_score"], row["published_at"], row["evidence_id"]))
    return _source_diverse(rows, limit=50, group_field="source_key", per_group=10)


def _x_leads(
    connection: sqlite3.Connection, *, start: datetime, as_of: datetime
) -> list[dict[str, Any]]:
    rows = []
    query = """SELECT posts.*, accounts.market_scope, accounts.impact_path
               FROM ben_x_posts posts
               JOIN ben_x_accounts accounts ON accounts.id=posts.account_id
               WHERE posts.is_repost=0 ORDER BY posts.created_at DESC"""
    for raw in connection.execute(query):
        row = dict(raw)
        if not _within_window(row.get("created_at"), start=start, end=as_of):
            continue
        text = str(row.get("original_text") or "")
        related = json.loads(row.get("related_tickers_json") or "[]")
        market_scope = str(row.get("market_scope") or "")
        term_hits = sum(term in text.casefold() for term in TW_MARKET_TERMS)
        if not related and "TW" not in market_scope.upper() and term_hits == 0:
            continue
        views = int(row.get("views") or 0)
        engagement = (
            int(row.get("likes") or 0)
            + int(row.get("reposts") or 0) * 2
            + int(row.get("quotes") or 0) * 2
            + int(row.get("replies") or 0)
        )
        score = math.log10(views + 10) * 8 + math.log10(engagement + 2) * 10
        score += term_hits * 8 + (10 if related else 0) + (8 if "TW" in market_scope.upper() else 0)
        rows.append({
            "evidence_id": f"X:{row['post_id']}",
            "evidence_class": "OPINION",
            "epistemic_status": "OPINION",
            "source_key": row["publisher_group"],
            "source_name": f"@{row['author_handle']}",
            "author_name": row["author_name"],
            "title": re.sub(r"\s+", " ", text).strip()[:240],
            "published_at": row["created_at"],
            "fetched_at": row.get("fetched_at"),
            "url": row["original_url"],
            "related_tickers": related,
            "likes": int(row.get("likes") or 0),
            "reposts": int(row.get("reposts") or 0),
            "replies": int(row.get("replies") or 0),
            "views": views or None,
            "selection_score": round(score, 3),
            "usage_boundary": "Attention/opinion evidence only; not a finance fact.",
        })
    rows.sort(key=lambda row: (-row["selection_score"], row["published_at"], row["evidence_id"]))
    return _source_diverse(rows, limit=30, group_field="source_key", per_group=3)


def _disclosure_leads(
    connection: sqlite3.Connection, *, start: datetime, as_of: datetime
) -> list[dict[str, Any]]:
    rows = []
    for raw in connection.execute("SELECT * FROM official_disclosures ORDER BY announced_at DESC"):
        row = dict(raw)
        if not _within_window(row.get("announced_at"), start=start, end=as_of):
            continue
        rows.append({
            "evidence_id": f"MOPS:{row['id']}",
            "evidence_class": "OFFICIAL_DISCLOSURE",
            "epistemic_status": "FACT",
            "source_key": "MOPS",
            "source_name": "公開資訊觀測站",
            "title": f"{row['company_name']}：{row['subject']}",
            "published_at": row["announced_at"],
            "fetched_at": row.get("fetched_at") or row.get("collected_at"),
            "url": row["official_url"],
            "security_id": row.get("security_id"),
            "event_date": row.get("event_date"),
        })
        if len(rows) >= 30:
            break
    return rows


def _candidate_leads(channel_brief: dict[str, Any]) -> list[dict[str, Any]]:
    output = []
    for brief in channel_brief.get("briefs", []):
        for candidate in brief.get("assignments", [])[:8]:
            output.append({
                "origin_channel": brief["channel_name"],
                "candidate_id": candidate["candidate_id"],
                "candidate_type": candidate["candidate_type"],
                "title": candidate["title"],
                "why_now": candidate.get("why_now", []),
                "facts": candidate.get("facts", []),
                "unknowns": candidate.get("unknowns", []),
                "security_ids": candidate.get("security_ids", []),
                "stock_details": candidate.get("stock_details", []),
                "evidence": candidate.get("evidence", []),
                "opinion_evidence": candidate.get("opinion_evidence", []),
            })
    return output


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError):
        return None


def _market_activity_leaders(
    connection: sqlite3.Connection, *, trade_date: str, limit: int = 40
) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT md.security_id, md.exchange_code, md.ticker, s.company_name,
               md.opening_price, md.highest_price, md.lowest_price,
               md.closing_price, md.price_change, md.trade_volume,
               md.trade_value, md.transaction_count, md.source_id
          FROM official_market_data_daily md
          JOIN official_securities s ON s.id = md.security_id
         WHERE md.trade_date = ?
           AND md.data_status = 'EOD'
           AND md.trade_value IS NOT NULL
         ORDER BY md.trade_value DESC, md.security_id
         LIMIT ?
        """,
        (trade_date, limit),
    ).fetchall()
    output: list[dict[str, Any]] = []
    for raw in rows:
        row = dict(raw)
        close = _decimal(row["closing_price"])
        change = _decimal(row["price_change"])
        previous = close - change if close is not None and change is not None else None
        change_pct = (
            change / previous * Decimal("100")
            if change is not None and previous not in {None, Decimal("0")}
            else None
        )
        if row["exchange_code"] == "TWSE":
            source_url = (
                "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX"
                f"?date={trade_date.replace('-', '')}&type=ALLBUT0999&response=json"
            )
        else:
            source_url = (
                "https://www.tpex.org.tw/www/zh-tw/afterTrading/otc"
                f"?date={trade_date.replace('-', '/')}&type=EW&response=json"
            )
        output.append({
            "evidence_id": f"OFFICIAL_EOD:{row['security_id']}:{trade_date}",
            "evidence_class": "OFFICIAL_EOD",
            "epistemic_status": "FACT",
            "security_id": row["security_id"],
            "exchange_code": row["exchange_code"],
            "ticker": row["ticker"],
            "company_name": row["company_name"],
            "trade_date": trade_date,
            "opening_price": float(value) if (value := _decimal(row["opening_price"])) is not None else None,
            "highest_price": float(value) if (value := _decimal(row["highest_price"])) is not None else None,
            "lowest_price": float(value) if (value := _decimal(row["lowest_price"])) is not None else None,
            "closing_price": float(close) if close is not None else None,
            "price_change": float(change) if change is not None else None,
            "change_pct": float(change_pct.quantize(Decimal("0.01"))) if change_pct is not None else None,
            "trade_volume": int(row["trade_volume"]) if row["trade_volume"] is not None else None,
            "trade_value": int(row["trade_value"]),
            "transaction_count": int(row["transaction_count"]) if row["transaction_count"] is not None else None,
            "source_id": row["source_id"],
            "source_name": "臺灣證券交易所" if row["exchange_code"] == "TWSE" else "證券櫃檯買賣中心",
            "source_url": source_url,
        })
    return output


def build_close_talk_fact_pack(
    connection: sqlite3.Connection,
    *,
    channel_brief: dict[str, Any],
    source_pack: dict[str, Any],
) -> dict[str, Any]:
    trade_date = source_pack["market_session_date"]
    if channel_brief.get("market_session_date") != trade_date:
        raise ValueError("channel brief and source pack market dates do not match")
    as_of = _parse_time(channel_brief.get("data_as_of"))
    if as_of is None:
        raise ValueError("channel brief data_as_of is invalid")
    as_of = as_of.astimezone(TAIPEI)
    start = as_of - timedelta(hours=48)
    news = _news_leads(connection, start=start, as_of=as_of)
    x_items = _x_leads(connection, start=start, as_of=as_of)
    disclosures = _disclosure_leads(connection, start=start, as_of=as_of)
    candidates = _candidate_leads(channel_brief)
    market_activity = _market_activity_leaders(connection, trade_date=trade_date)
    return {
        "schema_version": "ben-close-talk-fact-pack.v0.1",
        "market_session_date": trade_date,
        "data_as_of": as_of.isoformat(),
        "window_start": start.isoformat(),
        "window_hours": 48,
        # A BASE_READY source pack is enough for a first human-review draft.
        # Late index/flow/margin rows are carried as UNKNOWN and can produce a later revision.
        "status": "READY" if source_pack.get("base_status") == "READY" or source_pack.get("status") == "READY" else "SOURCE_PENDING",
        "generation_stage": "BASE_DRAFT" if source_pack.get("base_status") == "READY" and source_pack.get("enhancement_status") != "READY" else "ENRICHED_DRAFT" if source_pack.get("status") == "READY" else "BLOCKED",
        "cash_market_source_pack": source_pack,
        "market_activity_leaders": market_activity,
        "candidate_leads": candidates,
        "news_leads": news,
        "x_attention_leads": x_items,
        "official_disclosure_leads": disclosures,
        "coverage": {
            "candidate_leads": len(candidates),
            "market_activity_leaders": len(market_activity),
            "news_leads": len(news),
            "news_publishers": len({row["source_key"] for row in news}),
            "x_leads": len(x_items),
            "x_accounts": len({row["source_key"] for row in x_items}),
            "disclosures": len(disclosures),
        },
        "editorial_boundaries": [
            "Price/volume is a market signal, not proof of a hot topic or institutional accumulation.",
            "X is OPINION/attention evidence only.",
            "Creator transcripts are style evidence only and must not supply current finance facts.",
            "A causal explanation needs a linked official or reported source; otherwise keep it UNKNOWN.",
            "Do not use any evidence published after data_as_of.",
        ],
    }
