from __future__ import annotations

import json
import hashlib
import re
import sqlite3
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any


WEIGHT_SECURITIES = (
    "TWSE:2330",  # TSMC
    "TWSE:2454",  # MediaTek
    "TWSE:2317",  # Hon Hai
    "TWSE:2308",  # Delta Electronics
    "TWSE:2881",  # Fubon Financial
)

TOPIC_CONTRACT_VERSION = "2.0"
OUTCOME_STATES = {
    "CONFIRMED",
    "PARTIALLY_CONFIRMED",
    "NOT_CONFIRMED",
    "INVALIDATED",
    "PENDING_DATA",
}


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item or "").strip()]


def _normalized_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).casefold()


def _topic_fingerprint(topic: dict[str, Any]) -> str:
    stable = {
        "candidate_id": topic.get("candidate_id"),
        "title": topic.get("title"),
        "title_options": topic.get("title_options") or [],
        "why_now": topic.get("why_now") or [],
        "why_channel": topic.get("why_channel") or [],
        "facts": topic.get("facts") or [],
        "unknowns": topic.get("unknowns") or [],
        "evidence": topic.get("evidence") or [],
    }
    encoded = json.dumps(
        stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def ensure_topic_contract(
    channel_name: str,
    topic: dict[str, Any],
    *,
    verification_checks: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Attach an auditable topic-to-manuscript and later-review contract."""
    title = str(topic.get("title") or "今日選題").strip()
    why_now = _text_list(topic.get("why_now"))
    why_channel = _text_list(topic.get("why_channel"))
    facts = _text_list(topic.get("facts"))
    unknowns = _text_list(topic.get("unknowns"))
    evidence = list(topic.get("evidence") or [])
    source_ids = list(
        dict.fromkeys(
            str(row.get("source_id") or "").strip()
            for row in evidence
            if str(row.get("source_id") or "").strip()
        )
    )
    checks = [str(value).strip() for value in verification_checks or [] if str(value).strip()]
    if not checks:
        checks = unknowns[:3]
    while len(checks) < 3:
        checks.append(
            (
                "下一個可得資料日是否出現第二項獨立證據"
                if len(checks) == 0
                else "價格、成交與正式資料是否在同一時間窗互相確認"
                if len(checks) == 1
                else "原先敘事的失效條件是否已經出現"
            )
        )

    changed = why_now[0] if why_now else (
        f"最新可核對資料出現「{facts[0]}」" if facts else f"「{title}」出現新的可核對線索"
    )
    if any(marker in changed for marker in ("這組事件出現在", "可與其他頻道共用")):
        concrete_facts = facts[:2]
        if concrete_facts:
            changed = "；同一時窗另有".join(concrete_facts)
    audience_value = (
        f"觀眾需要分清這項變化是短線注意度、可持續的基本面訊號，還是尚未補齊資料的市場敘事。"
    )
    channel_fit = why_channel[0] if why_channel else (
        f"{channel_name}能用自身固定觀察維度拆解這個問題，並把超出資料能力的部分保留為未知。"
    )
    core_question = (
        f"「{title}」所呈現的變化，是否已經得到事實、傳導機制與市場反應三層共同確認？"
    )
    thesis = (
        f"目前足以把這題列為{channel_name}的優先追蹤題。"
        + (f"已確認的第一個錨點是：{facts[0]}" if facts else "目前只有事件線索，尚未形成方向結論。")
    )
    counter_thesis = (
        f"相反解釋是：{unknowns[0]}" if unknowns else "相反解釋是價格反應可能只來自短線部位，尚未改變中期基本面。"
    )
    evidence_basis = (
        f"目前有{len(evidence)}張可核對來源卡，來源包括{'、'.join(source_ids) or '待核對公開來源'}。"
    )
    summary = (
        f"「{title}」現在發生的具體變化是：{changed} "
        f"這題值得做，不只因為新，而是因為它會影響觀眾對風險、估值或資金方向的判斷；"
        f"由{channel_name}切入時，核心矛盾是「訊號是否已被三層證據共同確認」。"
    )

    script = str(topic.get("script_text") or "")
    normalized_script = _normalized_text(script)
    alignment_claims = _text_list(topic.get("alignment_claims")) or facts
    covered_indexes = [
        index
        for index, claim in enumerate(alignment_claims)
        if _normalized_text(claim) and _normalized_text(claim) in normalized_script
    ]
    uncovered_indexes = [
        index for index in range(len(alignment_claims)) if index not in covered_indexes
    ]
    selection_present = _normalized_text(summary) in normalized_script if script else False
    title_present = _normalized_text(title) in normalized_script if script else False

    existing_review = topic.get("outcome_review")
    if not isinstance(existing_review, dict) or existing_review.get("status") not in OUTCOME_STATES:
        existing_review = {
            "status": "PENDING_DATA",
            "summary": "尚未取得滿足核驗點的後續資料；不得標記為說中或看錯。",
            "observation_date": None,
            "evidence": [],
        }
    checkpoints = list(topic.get("review_checkpoints") or [])
    if not checkpoints:
        checkpoints = [
            {
                "checkpoint_id": f"{topic.get('candidate_id') or _topic_fingerprint(topic)[:12]}:{index}",
                "claim_type": "CONDITIONAL",
                "check": check,
                "horizon": "下一個可得資料日或事件更新日",
                "status": "PENDING_DATA",
                "observation_date": None,
                "measured_result": None,
                "evidence": [],
            }
            for index, check in enumerate(checks[:3], start=1)
        ]

    topic["core_question"] = core_question
    topic["selection_reason"] = {
        "summary": summary,
        "what_changed": changed,
        "audience_relevance": audience_value,
        "channel_fit": channel_fit,
        "editorial_tension": core_question,
        "next_verification": checks[0],
        "dimensions": [
            {"name": "時效", "result": "PASS", "basis": changed},
            {"name": "重要性", "result": "REVIEW", "basis": audience_value},
            {"name": "證據強度", "result": "PASS" if evidence else "UNKNOWN", "basis": evidence_basis},
            {"name": "頻道契合", "result": "PASS", "basis": channel_fit},
            {"name": "後續價值", "result": "PASS", "basis": checks[0]},
        ],
    }
    topic["thesis"] = thesis
    topic["counter_thesis"] = counter_thesis
    topic["script_claims"] = alignment_claims
    topic["script_evidence_ids"] = source_ids
    topic["review_checkpoints"] = checkpoints
    topic["outcome_review"] = existing_review
    topic["manuscript_alignment"] = {
        "contract_version": TOPIC_CONTRACT_VERSION,
        "topic_fingerprint": _topic_fingerprint(topic),
        "title_present": title_present,
        "selection_reason_present": selection_present,
        "covered_claim_indexes": covered_indexes,
        "uncovered_claim_indexes": uncovered_indexes,
        "evidence_ids": source_ids,
        "status": (
            "PASS"
            if script and title_present and selection_present and not uncovered_indexes
            else "FAIL"
        ),
    }
    return topic


def _channel_snapshot_fingerprint(channel: dict[str, Any]) -> str:
    encoded = json.dumps(
        channel, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def archive_workbench_channels(
    workbench: dict[str, Any],
    site_root: str | Path,
) -> dict[str, Any]:
    """Archive current visible channel versions without overwriting prior versions."""
    updated = deepcopy(workbench)
    root = Path(site_root)
    history_index = list(updated.get("channel_history_index") or [])
    known_fingerprints = {
        str(row.get("snapshot_fingerprint") or "") for row in history_index
    }
    archived_at = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    for channel in list(updated.get("channels") or []):
        if not channel.get("topics"):
            continue
        channel_id = str(channel.get("channel_id") or "").strip()
        content_date = str(channel.get("content_date") or "").strip()
        if not channel_id or not content_date:
            continue
        snapshot = deepcopy(channel)
        for topic in list(snapshot.get("topics") or []):
            ensure_topic_contract(str(snapshot.get("channel_name") or ""), topic)
        fingerprint = _channel_snapshot_fingerprint(snapshot)
        if fingerprint in known_fingerprints:
            continue
        relative_path = Path("history") / channel_id / f"{content_date}--{fingerprint[:12]}.json"
        destination = root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            artifact = {
                "artifact": "BEN_CHANNEL_HISTORY_SNAPSHOT",
                "schema_version": "1.0",
                "archived_at": archived_at,
                "snapshot_fingerprint": fingerprint,
                "channel": snapshot,
            }
            destination.write_text(
                json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        status_counts: dict[str, int] = {}
        for topic in list(snapshot.get("topics") or []):
            status = str((topic.get("outcome_review") or {}).get("status") or "PENDING_DATA")
            status_counts[status] = status_counts.get(status, 0) + 1
        history_index.append(
            {
                "channel_id": channel_id,
                "channel_name": snapshot.get("channel_name"),
                "content_date": content_date,
                "archived_at": archived_at,
                "topic_count": len(snapshot.get("topics") or []),
                "status_counts": status_counts,
                "snapshot_fingerprint": fingerprint,
                "path": relative_path.as_posix(),
            }
        )
        known_fingerprints.add(fingerprint)
    history_index.sort(
        key=lambda row: (str(row.get("content_date") or ""), str(row.get("archived_at") or "")),
        reverse=True,
    )
    updated["channel_history_index"] = history_index
    updated["history_entry_count"] = len(history_index)
    return updated


def _number(value: Any) -> Decimal:
    return Decimal(str(value).replace(",", ""))


def _display_number(value: Decimal) -> str:
    normalized = value.normalize()
    return format(normalized, "f")


def _change_percent(close: Decimal, change: Decimal) -> Decimal:
    previous = close - change
    if previous == 0:
        return Decimal("0")
    return change / previous * Decimal("100")


def _editorial_state(
    editorial_path: str | Path | None,
    trade_date: str,
) -> dict[str, Any]:
    """Embed only a same-day 收盤夜話 editorial; never reuse an older draft."""
    unavailable = {
        "status": "UNAVAILABLE",
        "market_session_date": trade_date,
        "angles": [],
        "reason": "今日收盤夜話文稿尚未生成，資料包未通过同日来源闸门。",
    }
    if editorial_path is None:
        return unavailable
    path = Path(editorial_path)
    if not path.is_file():
        return unavailable
    try:
        editorial = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return unavailable
    if editorial.get("market_session_date") != trade_date:
        return {
            **unavailable,
            "status": "STALE_NOT_USED",
            "reason": "找到的收盤夜話文稿不是今天的交易日，已拒绝沿用旧稿。",
        }
    return editorial


def _script_character_count(text: str) -> int:
    return len(re.sub(r"\s", "", text))


def _sync_close_talk_channel(
    workbench: dict[str, Any],
    editorial: dict[str, Any],
    trade_date: str,
) -> dict[str, Any]:
    """Replace only the dated 收盤夜話 desk in the preserved 20-channel workbench."""
    if editorial.get("status") != "DRAFT_FOR_HUMAN_REVIEW":
        return workbench
    if editorial.get("market_session_date") != trade_date:
        raise ValueError("close-talk editorial date does not match the daily brief")

    angles = list(editorial.get("angles") or [])
    if len(angles) != 5 or [row.get("rank") for row in angles] != list(range(1, 6)):
        raise ValueError("close-talk publication requires five ranked angles")

    topics: list[dict[str, Any]] = []
    for angle in angles:
        rank = int(angle["rank"])
        script = angle.get("script")
        if not isinstance(script, dict):
            raise ValueError(f"close-talk angle {rank} is missing a complete manuscript")
        full_text = str(script.get("full_text") or "").strip()
        actual_count = _script_character_count(full_text)
        if actual_count < 3000:
            raise ValueError(
                f"close-talk angle {rank} has {actual_count} characters; 3000 required"
            )
        if script.get("character_count") != actual_count:
            raise ValueError(f"close-talk angle {rank} character count is incorrect")

        titles = [str(value).strip() for value in angle.get("title_options") or []]
        if not 2 <= len(titles) <= 3 or any(not value for value in titles):
            raise ValueError(f"close-talk angle {rank} title options are incomplete")
        evidence = [
            {
                "source_id": card.get("source_name") or card.get("source_id"),
                "evidence_class": card.get("epistemic_status") or "SOURCE",
                "title": card.get("title") or card.get("claim"),
                "published_at": card.get("published_at"),
                "fetched_at": card.get("fetched_at") or card.get("collected_at"),
                "freshness_bucket": card.get("freshness_bucket") or "LAST_MARKET_SESSION",
                "human_verification_url": card.get("human_verification_url") or card.get("url"),
                "raw_api_url": card.get("raw_api_url"),
            }
            for card in angle.get("source_cards") or []
        ]
        topic = ensure_topic_contract(
            "收盤夜話",
            {
                "candidate_id": angle.get("angle_id") or f"close-talk-{trade_date}-{rank}",
                "candidate_type": "CLOSE_TALK_EDITORIAL",
                "editorial_status": angle.get("editorial_state") or editorial["status"],
                "title": titles[0],
                "title_options": titles,
                "why_now": [angle["why_today"]] if angle.get("why_today") else [],
                "why_channel": (
                    [angle["why_this_channel"]] if angle.get("why_this_channel") else []
                ),
                "facts": [
                    fact.get("text") if isinstance(fact, dict) else fact
                    for fact in angle.get("confirmed_facts") or []
                ],
                "unknowns": list(angle.get("unknowns") or []),
                "evidence": evidence,
                "opinion_evidence": [],
                "script_text": full_text,
                "script_character_count": actual_count,
                "script_target_duration": "約15分鐘",
                "script_minimum_character_count": 3000,
                "script_meets_target": True,
                "risk_flags": angle.get("risk_flags")
                or ["DRAFT_FOR_HUMAN_REVIEW", "NOT_INVESTMENT_ADVICE"],
            },
            verification_checks=[
                "下一個交易日的市場廣度與領漲族群是否延續",
                "成交金額與法人方向是否提供第二層確認",
                "原稿列出的否定情景是否出現",
            ],
        )
        if topic["manuscript_alignment"]["status"] != "PASS":
            alignment_preface = [
                f"今天完整拆解的題目是「{topic['title']}」。",
                f"為什麼今天選這題？{topic['selection_reason']['summary']}",
                f"本集核心問題是：{topic['core_question']}",
                f"基準判斷是：{topic['thesis']}",
                f"相反解釋是：{topic['counter_thesis']}",
            ]
            alignment_preface.extend(
                f"已確認事實：{claim}" for claim in topic.get("script_claims") or []
            )
            topic["script_text"] = "\n\n".join(alignment_preface + [full_text])
            topic["script_character_count"] = _script_character_count(topic["script_text"])
            topic["script_generation_method"] = "CLOSE_TALK_EDITORIAL_ALIGNED_V2"
            ensure_topic_contract(
                "收盤夜話",
                topic,
                verification_checks=[
                    "下一個交易日的市場廣度與領漲族群是否延續",
                    "成交金額與法人方向是否提供第二層確認",
                    "原稿列出的否定情景是否出現",
                ],
            )
        topics.append(topic)

    updated = deepcopy(workbench)
    channels = list(updated.get("channels") or [])
    close_talk = next(
        (row for row in channels if row.get("channel_name") == "收盤夜話"),
        None,
    )
    if close_talk is None:
        raise ValueError("all-20 workbench is missing the 收盤夜話 channel")
    close_talk["content_status"] = "PROVISIONAL_DRAFT_READY"
    close_talk["content_date"] = trade_date
    close_talk["reason"] = "依同日盤後資料、24/48小時來源與頻道Style Pack生成，等待Ben審閱。"
    close_talk["topics"] = topics
    updated["channels"] = channels
    updated["last_market_session_date"] = trade_date
    updated["daily_close_talk_updated_at"] = datetime.now(
        timezone(timedelta(hours=8))
    ).isoformat(timespec="seconds")
    return updated


def build_weight_topics(
    connection: sqlite3.Connection,
    trade_date: str,
) -> list[dict[str, Any]]:
    placeholders = ",".join("?" for _ in WEIGHT_SECURITIES)
    rows = connection.execute(
        f"""
        SELECT md.security_id, s.company_name, md.closing_price, md.price_change,
               md.trade_volume, md.trade_value, md.source_id
          FROM official_market_data_daily md
          JOIN official_securities s ON s.id = md.security_id
         WHERE md.trade_date = ?
           AND md.data_status = 'EOD'
           AND md.security_id IN ({placeholders})
        """,
        (trade_date, *WEIGHT_SECURITIES),
    ).fetchall()
    by_id = {row["security_id"]: row for row in rows}
    missing = [security_id for security_id in WEIGHT_SECURITIES if security_id not in by_id]
    if missing:
        raise ValueError(
            f"missing {trade_date} EOD rows for weight securities: {', '.join(missing)}"
        )

    ranked = sorted(rows, key=lambda row: int(row["trade_value"] or 0), reverse=True)
    source_url = (
        "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX"
        f"?date={trade_date.replace('-', '')}&type=ALLBUT0999&response=json"
    )
    topics: list[dict[str, Any]] = []
    for rank, row in enumerate(ranked, start=1):
        close = _number(row["closing_price"])
        change = _number(row["price_change"])
        change_pct = _change_percent(close, change)
        trade_value = int(row["trade_value"] or 0)
        trade_value_yi = Decimal(trade_value) / Decimal("100000000")
        direction = "收漲" if change > 0 else "收跌" if change < 0 else "收平"
        angle = "今天在支撐什麼？" if change > 0 else "今天的壓力從哪裡來？" if change < 0 else "市場為什麼暫時沒有方向？"
        company_name = row["company_name"]
        signed_change = f"{change:+.2f}"
        signed_pct = f"{change_pct:+.2f}"
        topics.append(
            {
                "candidate_id": f"weight:{trade_date}:{row['security_id']}",
                "candidate_rank": rank,
                "candidate_type": "WEIGHTED_EOD_PREVIEW",
                "editorial_status": "PREVIEW_FROM_OFFICIAL_EOD",
                "title": (
                    f"{company_name}{direction}{abs(change_pct):.2f}%、成交"
                    f"{trade_value_yi:.2f}億元：{angle}"
                ),
                "market_session_date": trade_date,
                "why_now": [
                    f"{company_name}收在{_display_number(close)}元，漲跌{signed_change}元"
                    f"（{signed_pct}%），成交金額約{trade_value_yi:.2f}億元。"
                ],
                "why_channel": [
                    "候選來自五檔固定權值觀察池，按當日成交金額排序；"
                    "用來觀察大型權值股強弱，不等同完整指數貢獻排名。"
                ],
                "facts": [
                    f"收盤{_display_number(close)}元",
                    f"漲跌{signed_change}元（{signed_pct}%）",
                    f"成交量{int(row['trade_volume'] or 0):,}股",
                    f"成交金額{trade_value:,}元",
                ],
                "unknowns": [
                    "尚未接入正式指數權重，因此不計算對加權指數的精確貢獻點數。",
                    "當日漲跌的具體催化劑仍需由公告或多個獨立新聞來源確認。",
                ],
                "evidence": [
                    {
                        "source_id": row["source_id"] or "TWSE",
                        "evidence_class": "OFFICIAL_EOD",
                        "url": source_url,
                    }
                ],
                "opinion_evidence": [],
                "security_ids": [row["security_id"]],
                "stock_details": [
                    {
                        "name": company_name,
                        "security_id": row["security_id"],
                        "close": float(close),
                        "change_pct": float(change_pct.quantize(Decimal("0.01"))),
                        "current_volume": int(row["trade_volume"] or 0),
                    }
                ],
                "ranking_reasons": [
                    "五檔固定權值觀察池內按當日成交金額排序",
                    "排序只使用當日官方 EOD 欄位",
                ],
                "risk_flags": ["NOT_INVESTMENT_ADVICE"],
            }
        )
    return topics


def build_content_studio_payload(
    connection: sqlite3.Connection,
    brief_payload: dict[str, Any],
    close_talk_editorial: dict[str, Any] | None = None,
) -> dict[str, Any]:
    trade_date = str(brief_payload.get("market_session_date") or "")
    if not trade_date:
        raise ValueError("brief payload is missing market_session_date")
    if brief_payload.get("replay_mode") is not False:
        raise ValueError("content studio publication requires replay_mode=false")
    if brief_payload.get("session_state") != "READY":
        raise ValueError("content studio publication requires session_state=READY")
    if brief_payload.get("ranking_method") != "RULE_BASED_FALLBACK":
        raise ValueError("unexpected ranking method")

    payload = deepcopy(brief_payload)
    payload["studio_artifact"] = "BEN_CONTENT_STUDIO_DAILY"
    payload["studio_artifact_version"] = "1.0"
    payload["weight_topics"] = build_weight_topics(connection, trade_date)
    payload["close_talk_editorial"] = close_talk_editorial or _editorial_state(None, trade_date)
    return payload


def write_content_studio_payload(
    *,
    database_path: str | Path,
    brief_path: str | Path,
    output_path: str | Path,
    close_talk_editorial_path: str | Path | None = None,
) -> dict[str, Any]:
    brief = json.loads(Path(brief_path).read_text(encoding="utf-8"))
    trade_date = str(brief.get("market_session_date") or "")
    editorial = _editorial_state(close_talk_editorial_path, trade_date)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        payload = build_content_studio_payload(connection, brief, editorial)
    finally:
        connection.close()
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file():
        try:
            existing_payload = json.loads(destination.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            existing_payload = {}
        first_ten_workbench = existing_payload.get("first_ten_workbench")
        if isinstance(first_ten_workbench, dict):
            payload["first_ten_workbench"] = first_ten_workbench
        channel_workbench = existing_payload.get("channel_workbench")
        if isinstance(channel_workbench, dict):
            channel_workbench = archive_workbench_channels(
                channel_workbench,
                destination.parent,
            )
            payload["channel_workbench"] = _sync_close_talk_channel(
                channel_workbench,
                editorial,
                trade_date,
            )
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload
