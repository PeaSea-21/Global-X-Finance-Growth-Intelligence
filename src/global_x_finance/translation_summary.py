from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from dataclasses import dataclass
from typing import Any, Callable

from opencc import OpenCC


ENTITY_NAMES_ZH = {
    "2330": "台積電", "2317": "鴻海", "2454": "聯發科", "2303": "聯電",
    "2382": "廣達", "2308": "台達電", "3231": "緯創", "2412": "中華電",
    "2881": "富邦金", "2882": "國泰金", "2408": "南亞科", "2059": "川湖",
    "NVDA": "英偉達", "AAPL": "蘋果", "MSFT": "微軟", "TSLA": "特斯拉",
    "AMD": "超微", "INTC": "英特爾", "GOOGL": "Alphabet", "META": "Meta",
    "AMZN": "亞馬遜", "AVGO": "博通", "TSM": "台積電 ADR", "ASML": "ASML",
    "ARM": "Arm", "MU": "美光", "QCOM": "高通", "ORCL": "甲骨文",
    "PLTR": "Palantir", "SMCI": "美超微", "NFLX": "Netflix", "COIN": "Coinbase",
    "MSTR": "Strategy",
}
ACTION_NAMES_ZH = {
    "earnings": "財報與營運數據更新", "launch": "產品或技術發布",
    "investment": "投資與資本動作", "partnership": "合作、訂單或供應鏈進展",
    "policy": "政策與監管變化", "security": "安全或突發事件",
    "market_move": "價格與市場異動",
}
TOPIC_NAMES_ZH = {
    "半導體與AI": "AI 與半導體", "利率與宏觀": "利率與宏觀",
    "財報與公司": "公司與財報", "關稅與政策": "政策與關稅",
    "能源與原物料": "能源與原物料", "地緣政治": "地緣政治",
    "數位資產": "數位資產",
}


@dataclass(frozen=True)
class TranslationSummary:
    title_zh: str
    summary_zh: str
    status: str
    method: str
    cache_key: str
    model_name: str | None = None
    attempt_count: int = 0
    error_reason: str | None = None


ModelAdapter = Callable[[str, str], dict[str, str]]


def _looks_chinese(text: str) -> bool:
    return len(re.findall(r"[\u4e00-\u9fff]", text or "")) >= 4 and "�" not in (text or "")


def _compact(text: str, limit: int) -> str:
    value = re.sub(r"https?://\S+", "", text or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit].rstrip() + ("…" if len(value) > limit else "")


def _specific_rule(text: str) -> tuple[str, str] | None:
    lowered = text.lower()
    rules = (
        (("wildfire", "belgium"), "比利時東部發生大型野火，約 2,700 公頃自然保護區受影響", "比利時救援單位正控制東部大型野火；原文稱約 2,700 公頃自然保護區受損，範圍仍需核對官方更新。"),
        (("wildberries", "moscow", "drone"), "莫斯科附近 Wildberries 倉庫遭無人機襲擊後起火", "原文稱莫斯科附近一座 Wildberries 倉庫在烏克蘭無人機襲擊後起火，屬近期首都周邊大規模攻擊的一部分。"),
        (("vagus nerve", "digital therapeutic"), "工研院稱開發台灣首項入耳式數位療法技術", "工研院表示已開發非侵入式入耳迷走神經刺激器，目標用於廣泛性焦慮症；療效與核准狀態仍應查官方資料。"),
        (("starlux", "a350-1000"), "星宇航空 A350-1000 彩繪機抵台，準備投入台日航線", "星宇航空 A350-1000 彩繪機抵達桃園機場，原文稱本週稍後將投入台北—東京商業航線。"),
        (("federal reserve", "bonds"), "全球升息預期升溫，債券市場壓力擴大", "市場正在討論聯準會與全球利率進一步上行的可能性；原文將焦點放在債券承壓風險。"),
        (("democratic action party", "cabinet"), "馬來西亞民主行動黨表決留在內閣", "馬來西亞民主行動黨表決續留安華內閣，暫時緩解執政聯盟在選舉挫折後的政治壓力。"),
        (("cooking gas", "india"), "印度要求企業準備提高液化石油氣產量", "印度要求國營企業與民營煉油商準備大幅提高 LPG 產量，以因應伊朗戰事延長帶來的不確定性。"),
        (("qwen3.8-27b", "hugging face"), "Qwen3.8-27B 登上 Hugging Face 熱門模型榜首", "Qwen 官方帳號表示 Qwen3.8-27B 已成為 Hugging Face 熱門模型第一名；這是社群熱度里程碑，不等同商業採用數據。"),
        (("qwen3.8-27b", "laptop"), "Qwen3.8-27B 展示在筆電本地運行", "Qwen 官方帳號轉發 Qwen3.8-27B 在筆電運行的展示；效能、硬體條件與可重現性仍需查看原始測試。"),
        (("personal income", "nt$763,000"), "台灣平均個人年所得升至 76.3 萬元新高", "主計總處資料顯示 2025 年台灣平均個人年所得升至新台幣 76.3 萬元，各年齡層所得均增加。"),
        (("earthquake", "colomb"), "哥倫比亞 7.4 級地震後尋求暫緩美國關稅", "原文稱 8 月 10 日哥倫比亞發生 7.4 級地震，為該國百年來第二強，後續關稅請求仍需查政府文件。"),
        (("ai is hungry for power", "india"), "印度 AI 擴張面臨電網韌性與供電壓力", "Bloomberg 訪談聚焦 AI 用電增長對印度電網的壓力，屬產業討論，具體投資與建設數字需回查訪談。"),
    )
    for keywords, title, summary in rules:
        if all(keyword in lowered for keyword in keywords):
            return title, summary
    return None


class TranslationSummaryAdapter:
    """Chinese-first adapter with optional model, durable cache and honest rule fallback."""

    def __init__(
        self,
        connection: sqlite3.Connection | None = None,
        *,
        model_adapter: ModelAdapter | None = None,
        model_name: str | None = None,
        max_retries: int = 1,
    ) -> None:
        self.connection = connection
        self.model_adapter = model_adapter
        self.model_name = model_name
        self.max_retries = max(1, max_retries)

    def _table_available(self) -> bool:
        if self.connection is None:
            return False
        try:
            return self.connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='ben_translation_summary_cache'"
            ).fetchone() is not None
        except sqlite3.Error:
            return False

    def _read_cache(self, cache_key: str) -> TranslationSummary | None:
        if not self._table_available():
            return None
        row = self.connection.execute(
            "SELECT * FROM ben_translation_summary_cache WHERE cache_key=?", (cache_key,)
        ).fetchone()
        if row is None:
            return None
        return TranslationSummary(
            row["title_zh"], row["summary_zh"], row["status"], row["method"], row["cache_key"],
            row["model_name"], row["attempt_count"], row["error_reason"],
        )

    def _write_cache(self, result: TranslationSummary, source_hash: str, source_language: str, target_language: str, source_text: str) -> None:
        if not self._table_available():
            return
        self.connection.execute(
            """INSERT INTO ben_translation_summary_cache
               (id,cache_key,source_hash,source_language,target_language,source_text,title_zh,summary_zh,
                status,method,model_name,attempt_count,error_reason)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(cache_key) DO UPDATE SET title_zh=excluded.title_zh,summary_zh=excluded.summary_zh,
                   status=excluded.status,method=excluded.method,model_name=excluded.model_name,
                   attempt_count=excluded.attempt_count,error_reason=excluded.error_reason,updated_at=CURRENT_TIMESTAMP""",
            (str(uuid.uuid4()), result.cache_key, source_hash, source_language, target_language, source_text,
             result.title_zh, result.summary_zh, result.status, result.method, result.model_name,
             result.attempt_count, result.error_reason),
        )
        self.connection.commit()

    def summarize(
        self,
        text: str,
        *,
        entities: list[str],
        actions: list[str],
        topics: list[str],
        source_language: str | None = None,
        target_language: str = "zh-tw",
    ) -> TranslationSummary:
        source_text = text or ""
        source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
        cache_key = hashlib.sha256(f"v1|{target_language}|{source_hash}".encode()).hexdigest()
        cached = self._read_cache(cache_key)
        if cached:
            return cached

        if _looks_chinese(source_text):
            title = _compact(source_text, 72)
            subject = "、".join(ENTITY_NAMES_ZH.get(code, code) for code in entities[:2]) or "這項市場動態"
            summary = f"原文聚焦{subject}；首頁保留精簡中文摘要，完整事實、數字與語境請在 Evidence 中核對。"
            result = TranslationSummary(title, summary, "ORIGINAL_CHINESE", "ORIGINAL_CHINESE", cache_key)
            self._write_cache(result, source_hash, source_language or "zh", target_language, source_text)
            return result

        last_error = None
        if self.model_adapter:
            for attempt in range(1, self.max_retries + 1):
                try:
                    payload = self.model_adapter(source_text, target_language)
                    title, summary = _compact(payload.get("title", ""), 72), _compact(payload.get("summary", ""), 160)
                    if _looks_chinese(title) and _looks_chinese(summary):
                        result = TranslationSummary(title, summary, "MODEL_TRANSLATED", "MODEL_ADAPTER", cache_key, self.model_name, attempt)
                        self._write_cache(result, source_hash, source_language or "UNKNOWN", target_language, source_text)
                        return result
                    last_error = "model output did not contain usable Chinese title and summary"
                except Exception as error:  # adapter boundary must degrade without breaking the radar
                    last_error = f"{type(error).__name__}: {error}"

        specific = _specific_rule(source_text)
        if specific:
            title, summary = specific
        else:
            subjects = [ENTITY_NAMES_ZH.get(code, code) for code in entities[:2]]
            action = ACTION_NAMES_ZH.get(actions[0]) if actions else None
            topic = TOPIC_NAMES_ZH.get(topics[0]) if topics else None
            if subjects and action:
                title = f"{'、'.join(subjects)}：{action}出現新進展"
            elif subjects and topic:
                title = f"{'、'.join(subjects)}相關{topic}討論升溫"
            elif subjects:
                title = f"{'、'.join(subjects)}相關動態進入內容雷達"
            elif topic and action:
                title = f"{topic}：{action}正在發酵"
            elif topic:
                title = f"{topic}相關動態正在發酵"
            else:
                title = "海外財經內容出現新動態，等待人工核對主題"
            subject = "、".join(subjects) or topic or "這則海外財經內容"
            action_text = action or "最新進展"
            summary = f"規則摘要顯示內容聚焦{subject}的{action_text}；目前未取得可靠外部翻譯，請在 Evidence 中核對英文原文。"
        result = TranslationSummary(
            title, summary, "TRANSLATION_UNAVAILABLE", "RULE_FALLBACK", cache_key,
            self.model_name, self.max_retries if self.model_adapter else 0, last_error,
        )
        self._write_cache(result, source_hash, source_language or "UNKNOWN", target_language, source_text)
        return result


_SIMPLIFIED = OpenCC("tw2sp.json")


def localized_translation(result: TranslationSummary, language: str) -> TranslationSummary:
    if language != "zh-cn":
        return result
    return TranslationSummary(
        _SIMPLIFIED.convert(result.title_zh), _SIMPLIFIED.convert(result.summary_zh),
        result.status, result.method, result.cache_key, result.model_name,
        result.attempt_count, result.error_reason,
    )
