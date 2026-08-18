from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from .realtime_radar import parse_datetime


SAME_EVENT = "SAME_EVENT"
DIFFERENT_EVENT = "DIFFERENT_EVENT"
RELATED_BUT_DISTINCT = "RELATED_BUT_DISTINCT"

_STOPWORDS = {
    "about", "after", "again", "against", "amid", "among", "around", "because",
    "before", "being", "could", "from", "have", "into", "more", "over", "said",
    "says", "than", "that", "their", "there", "these", "they", "this", "through",
    "under", "with", "would", "market", "markets", "stock", "stocks", "news",
}
_CURRENCIES = {
    "$": "USD", "usd": "USD", "us$": "USD", "nt$": "TWD", "twd": "TWD",
    "€": "EUR", "eur": "EUR", "£": "GBP", "gbp": "GBP", "¥": "JPY/CNY",
}
_GEOGRAPHIES = {
    "taiwan": "TW", "台灣": "TW", "台湾": "TW", "china": "CN", "中國": "CN",
    "中国": "CN", "united states": "US", "u.s.": "US", "america": "US",
    "japan": "JP", "日本": "JP", "india": "IN", "印度": "IN", "russia": "RU",
    "moscow": "RU", "俄羅斯": "RU", "ukraine": "UA", "烏克蘭": "UA",
    "europe": "EU", "歐洲": "EU", "belgium": "BE", "sweden": "SE",
}
_STAGES = {
    "RUMOR_OR_REVIEW": ("weighs", "considering", "in talks", "explores", "seeks", "傳出", "洽談", "考慮"),
    "ANNOUNCED": ("announces", "announced", "unveils", "unveiled", "launches", "launched", "發布", "发布", "宣布", "推出"),
    "APPROVED": ("approved", "cleared", "authorizes", "獲准", "批准", "核准"),
    "COMPLETED": ("completed", "closes", "closed", "signed", "完成", "成交", "簽署", "签署"),
    "RESULTS": ("earnings", "results", "revenue", "profit", "財報", "财报", "營收", "营收", "獲利", "获利"),
}


@dataclass(frozen=True)
class ClusterDecision:
    label: str
    candidate: bool
    similarity: float
    time_delta_hours: float | None
    common_entities: tuple[str, ...]
    common_actors: tuple[str, ...]
    common_actions: tuple[str, ...]
    common_targets: tuple[str, ...]
    common_numbers: tuple[str, ...]
    common_topics: tuple[str, ...]
    merge_reason: str | None
    reject_reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _tokens(text: str) -> set[str]:
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff%$€£¥.]+", " ", (text or "").lower())
    words = {word for word in normalized.split() if len(word) > 1 and word not in _STOPWORDS}
    chinese = "".join(re.findall(r"[\u4e00-\u9fff]", normalized))
    words.update(chinese[index:index + 2] for index in range(max(0, len(chinese) - 1)))
    return words


def _numbers(text: str) -> tuple[list[str], list[str], list[str]]:
    values: list[str] = []
    currencies: list[str] = []
    percentages: list[str] = []
    pattern = re.compile(
        r"(?i)(?:(US\$|NT\$|USD|TWD|EUR|GBP|[$€£¥])\s*)?"
        r"(\d+(?:\.\d+)?)\s*(trillion|billion|million|bn|mn|萬|万|億|亿|兆)?\s*(%)?"
    )
    for match in pattern.finditer(text or ""):
        currency, number, scale, percent = match.groups()
        if len(number) == 4 and number.startswith(("19", "20")) and not currency and not scale and not percent:
            continue
        normalized_scale = {
            "bln": "billion", "bn": "billion", "mn": "million",
            "億": "billion_zh", "亿": "billion_zh", "萬": "ten_thousand", "万": "ten_thousand",
        }.get((scale or "").lower(), (scale or "").lower())
        value = f"{number}{normalized_scale}"
        if percent:
            percentages.append(f"{number}%")
        elif currency:
            normalized_currency = _CURRENCIES.get(currency.lower(), _CURRENCIES.get(currency, currency.upper()))
            currencies.append(normalized_currency)
            values.append(f"{normalized_currency}:{value}")
        elif scale:
            values.append(value)
    return sorted(set(values)), sorted(set(currencies)), sorted(set(percentages))


def _targets(text: str) -> list[str]:
    lowered = re.sub(r"\s+", " ", (text or "").lower())
    targets: set[str] = set()
    patterns = (
        r"(?:invest(?:ment)?\s+(?:of\s+[^ ]+\s+)?in|invest(?:s|ed)?\s+in|stake\s+in|acquir(?:e|es|ed|ing)|buy(?:s|ing)?|partner(?:s|ed)?\s+with|deal\s+with)\s+([a-z0-9][a-z0-9&.\- ]{1,45})",
        r"(?:投資|投资|收購|收购|入股|合作|供應|供应)\s*([\u4e00-\u9fffa-z0-9][\u4e00-\u9fffa-z0-9&.\- ]{1,24})",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, lowered):
            candidate = re.split(r"[,，。;；:：]|\b(?:after|amid|as|for|to|that|which|who)\b", match.group(1))[0]
            words = [word for word in candidate.strip().split() if word not in _STOPWORDS][:6]
            if words:
                targets.add(" ".join(words))
    return sorted(targets)


def _actors(text: str) -> list[str]:
    value = text or ""
    actors: set[str] = set()
    for match in re.finditer(r"\b[A-Z][A-Za-z0-9.+'-]*(?:\s+[A-Z][A-Za-z0-9.+'-]*){0,3}\b", value):
        phrase = match.group(0).strip(" .'\"")
        phrase = re.sub(r"['’]s$", "", phrase)
        excluded = {"the", "a", "an", "why", "how", "can", "first", "second", "news", "sunday", "taiwan", "china", "india", "russia"}
        words = [word.lower() for word in phrase.split() if word.lower() not in excluded]
        if words:
            actors.add(" ".join(words))
            actors.update(word for word in words if len(word) >= 4)
            actors.update(" ".join(words[index:index + 2]) for index in range(max(0, len(words) - 1)))
    for token in re.findall(r"\b[A-Za-z]+[A-Z][A-Za-z0-9.]*\b|\b[A-Za-z]+\d+(?:\.\d+)*[A-Za-z0-9.-]*\b", value):
        actors.add(token.lower())
    return sorted(actors)


def _stage(text: str) -> str | None:
    lowered = (text or "").lower()
    for stage, terms in _STAGES.items():
        if any(term.lower() in lowered for term in terms):
            return stage
    return None


def event_fingerprint(item: dict[str, Any]) -> dict[str, Any]:
    text = str(item.get("text") or item.get("original_title") or item.get("original_text") or "")
    entities = sorted({str(value) for value in item.get("entities", ()) if value})
    actions = sorted({str(value) for value in item.get("actions", ()) if value})
    topics = sorted({str(value) for value in item.get("topics", ()) if value})
    values, currencies, percentages = _numbers(text)
    geographies = sorted({code for term, code in _GEOGRAPHIES.items() if term in text.lower()})
    object_tokens = sorted(_tokens(text))[:24]
    primary = entities[0] if entities else None
    timestamp = item.get("published_at") or item.get("created_at")
    parsed = parse_datetime(timestamp)
    return {
        "primary_entity": primary,
        "ticker": primary,
        "company": primary,
        "actor": _actors(text),
        "action": actions,
        "event_stage": _stage(text),
        "target": _targets(text),
        "object": object_tokens,
        "number": values,
        "currency": currencies,
        "percentage": percentages,
        "geography": geographies,
        "theme": topics,
        "timestamp": parsed.isoformat() if parsed else timestamp,
        "event_date": parsed.date().isoformat() if parsed else None,
        "source_type": item.get("kind") or item.get("source_type") or "UNKNOWN",
    }


def _time_delta(left: dict[str, Any], right: dict[str, Any]) -> float | None:
    left_time = parse_datetime(left.get("published_at") or left.get("created_at"))
    right_time = parse_datetime(right.get("published_at") or right.get("created_at"))
    if left_time is None or right_time is None:
        return None
    return abs((left_time - right_time).total_seconds()) / 3600


def _normalized_urls(item: dict[str, Any]) -> set[str]:
    return {str(value).rstrip("/") for value in item.get("external_urls", ()) if value}


def decide_event_pair(left: dict[str, Any], right: dict[str, Any]) -> ClusterDecision:
    """Two-stage pair classifier: high-recall retrieval followed by strict merge."""
    left_fp, right_fp = event_fingerprint(left), event_fingerprint(right)
    left_tokens, right_tokens = _tokens(str(left.get("text") or "")), _tokens(str(right.get("text") or ""))
    union = left_tokens | right_tokens
    similarity = len(left_tokens & right_tokens) / len(union) if union else 0.0
    common_entities = tuple(sorted(set(left_fp["ticker"]) & set(right_fp["ticker"]))) if isinstance(left_fp["ticker"], list) else tuple(sorted(set(left.get("entities", ())) & set(right.get("entities", ()))))
    common_actors = tuple(sorted(set(left_fp["actor"]) & set(right_fp["actor"])))
    common_actions = tuple(sorted(set(left_fp["action"]) & set(right_fp["action"])))
    common_targets = tuple(sorted(set(left_fp["target"]) & set(right_fp["target"])))
    common_numbers = tuple(sorted((set(left_fp["number"]) | set(left_fp["percentage"])) & (set(right_fp["number"]) | set(right_fp["percentage"]))))
    common_topics = tuple(sorted(set(left_fp["theme"]) & set(right_fp["theme"])))
    shared_urls = _normalized_urls(left) & _normalized_urls(right)
    delta = _time_delta(left, right)

    candidate = bool(
        shared_urls
        or common_entities
        or common_actors
        or common_targets
        or (common_actions and common_topics)
        or (common_actions and common_numbers)
        or similarity >= 0.18
    )
    common = dict(
        candidate=candidate,
        similarity=round(similarity, 4),
        time_delta_hours=round(delta, 3) if delta is not None else None,
        common_entities=common_entities,
        common_actors=common_actors,
        common_actions=common_actions,
        common_targets=common_targets,
        common_numbers=common_numbers,
        common_topics=common_topics,
    )
    if not candidate:
        return ClusterDecision(DIFFERENT_EVENT, merge_reason=None, reject_reason="候选召回未命中：无共享实体、动作、目标、数字或足够文本重合", **common)
    if delta is None:
        return ClusterDecision(DIFFERENT_EVENT, merge_reason=None, reject_reason="缺少可比较的原始发布时间", **common)
    if delta > 36:
        label = RELATED_BUT_DISTINCT if common_entities or common_actors else DIFFERENT_EVENT
        return ClusterDecision(label, merge_reason=None, reject_reason=f"时间差 {delta:.1f} 小时，超过 36 小时事件窗口", **common)
    if shared_urls:
        return ClusterDecision(SAME_EVENT, merge_reason="共享规范化原始链接", reject_reason=None, **common)

    left_stage, right_stage = left_fp["event_stage"], right_fp["event_stage"]
    if left_stage and right_stage and left_stage != right_stage and (common_entities or common_actors or common_targets):
        return ClusterDecision(RELATED_BUT_DISTINCT, merge_reason=None, reject_reason=f"同一主题的不同事件阶段：{left_stage} vs {right_stage}", **common)

    left_numeric = set(left_fp["number"]) | set(left_fp["percentage"])
    right_numeric = set(right_fp["number"]) | set(right_fp["percentage"])
    numeric_conflict = bool(left_numeric and right_numeric and not common_numbers)
    if common_actions and common_actors:
        if common_numbers or len(common_actors) >= 2:
            return ClusterDecision(SAME_EVENT, merge_reason="共享事件主体与动作，并由数字、第二主体或文本重合确认", reject_reason=None, **common)
        return ClusterDecision(RELATED_BUT_DISTINCT, merge_reason=None, reject_reason="共享主体与动作，但不足以确认同一对象或事实", **common)
    if common_entities and common_actions:
        if numeric_conflict and similarity < 0.42 and not common_targets and len(common_actors) < 2:
            return ClusterDecision(RELATED_BUT_DISTINCT, merge_reason=None, reject_reason="公司与动作相同，但关键数字不一致且没有共同目标", **common)
        if common_targets or common_numbers or similarity >= 0.24:
            return ClusterDecision(SAME_EVENT, merge_reason="共享公司与核心动作，并由目标、数字或文本重合确认", reject_reason=None, **common)
        return ClusterDecision(RELATED_BUT_DISTINCT, merge_reason=None, reject_reason="共享公司与动作，但缺少共同目标、数字或足够文本重合", **common)
    if common_targets and common_actions and similarity >= 0.18:
        return ClusterDecision(SAME_EVENT, merge_reason="共享动作与事件目标", reject_reason=None, **common)
    if common_topics and common_actions and similarity >= 0.38:
        return ClusterDecision(SAME_EVENT, merge_reason="共享主题与动作且文本高度重合", reject_reason=None, **common)
    if common_entities or common_actors or common_targets:
        return ClusterDecision(RELATED_BUT_DISTINCT, merge_reason=None, reject_reason="有关联，但核心动作、对象或事件阶段不足以确认同一事件", **common)
    if common_topics and ((common_actions and similarity >= 0.12) or similarity >= 0.20):
        return ClusterDecision(RELATED_BUT_DISTINCT, merge_reason=None, reject_reason="共享主题但核心事实不同", **common)
    if common_actions and similarity >= 0.55:
        return ClusterDecision(SAME_EVENT, merge_reason="无显式 ticker，但动作与文本高度重合", reject_reason=None, **common)
    return ClusterDecision(DIFFERENT_EVENT, merge_reason=None, reject_reason="严格合并阶段证据不足", **common)


def diagnostic_record(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    decision = decide_event_pair(left, right)
    return {
        "left_id": left.get("id"),
        "right_id": right.get("id"),
        "left_fingerprint": event_fingerprint(left),
        "right_fingerprint": event_fingerprint(right),
        "decision": decision.to_dict(),
    }
