from __future__ import annotations

import hashlib
import html
import json
import re
import sqlite3
import statistics
import urllib.error
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Callable


USER_AGENT = "Mozilla/5.0 (compatible; GlobalXFinanceDemo/0.6; +local-demo)"

NEWS_SOURCES = (
    {
        "key": "yahoo_tw",
        "name": "Yahoo奇摩股市",
        "urls": ("https://tw.stock.yahoo.com/rss?category=tw-market",),
        "market": "TW",
        "language": "zh-Hant",
        "source_id": "TW-B04",
        "publisher_group": "yahoo",
        "importance": 16,
    },
    {
        "key": "yahoo_finance",
        "name": "Yahoo Finance",
        "urls": (
            "https://finance.yahoo.com/news/rssindex",
            "https://finance.yahoo.com/rss/topstories",
        ),
        "market": "US",
        "language": "en",
        "source_id": "NEWS-YAHOO-FINANCE",
        "publisher_group": "yahoo",
        "importance": 17,
    },
    {
        "key": "investing",
        "name": "Investing.com",
        "urls": ("https://www.investing.com/rss/news_25.rss",),
        "market": "INTL",
        "language": "en",
        "source_id": "NEWS-INVESTING",
        "publisher_group": "investing",
        "importance": 15,
    },
    {
        "key": "cnbc",
        "name": "CNBC",
        "urls": ("https://www.cnbc.com/id/100003114/device/rss/rss.html",),
        "market": "US",
        "language": "en",
        "source_id": "NEWS-CNBC",
        "publisher_group": "cnbc",
        "importance": 18,
    },
)

MAJOR_STOCKS = ("2330", "2317", "2454", "2303", "2382", "2308", "3231", "2412", "2881", "2882")

ENTITY_KEYWORDS = {
    "2330": ("台積電", "tsmc"),
    "2317": ("鴻海", "hon hai", "foxconn"),
    "2454": ("聯發科", "mediatek"),
    "2303": ("聯電", "umc", "united microelectronics"),
    "2382": ("廣達", "quanta"),
    "2308": ("台達電", "delta electronics"),
    "3231": ("緯創", "wistron"),
    "2412": ("中華電", "chunghwa telecom"),
    "2881": ("富邦金", "fubon financial"),
    "2882": ("國泰金", "cathay financial"),
    "2408": ("南亞科", "nanya"),
    "2059": ("川湖",),
    "NVDA": ("nvidia", "英偉達", "輝達"),
    "AAPL": ("apple", "蘋果"),
    "MSFT": ("microsoft", "微軟"),
    "TSLA": ("tesla", "特斯拉"),
    "AMD": ("advanced micro devices", "amd", "超微"),
    "INTC": ("intel", "英特爾"),
    "GOOGL": ("alphabet", "google", "谷歌"),
    "META": ("meta platforms", "facebook", "meta"),
    "AMZN": ("amazon", "亞馬遜"),
    "AVGO": ("broadcom", "博通"),
    "TSM": ("台積電 adr", "tsm adr"),
    "ASML": ("asml", "艾司摩爾"),
    "ARM": ("arm holdings", "arm ltd", "arm chip"),
    "MU": ("micron", "美光"),
    "QCOM": ("qualcomm", "高通"),
    "ORCL": ("oracle", "甲骨文"),
    "PLTR": ("palantir", "帕蘭提爾"),
    "SMCI": ("super micro", "supermicro", "美超微"),
    "NFLX": ("netflix", "網飛"),
    "COIN": ("coinbase",),
    "MSTR": ("microstrategy", "strategy inc"),
}

TOPIC_KEYWORDS = {
    "半導體與AI": ("semiconductor", "chip", "nvidia", "tsmc", "artificial intelligence", " ai ", "ai ", " ai", "claude", "openai", "anthropic", "gemini", "qwen", "伺服器", "半導體", "晶片", "人工智慧"),
    "利率與宏觀": ("federal reserve", "fed ", "rate cut", "interest rate", "inflation", "cpi", "gdp", "economy", "利率", "通膨", "央行", "經濟"),
    "財報與公司": ("earnings", "revenue", "profit", "財報", "營收", "獲利"),
    "關稅與政策": ("tariff", "regulation", "policy", "sanction", "export control", "關稅", "監管", "政策", "制裁", "出口管制"),
    "能源與原物料": ("oil", "gas", "lng", "energy", "copper", "gold", "crude", "石油", "天然氣", "能源", "黃金"),
    "地緣政治": ("war", "drone", "missile", "strike", "iran", "russia", "moscow", "ukraine", "戰爭", "無人機", "飛彈", "伊朗", "俄羅斯", "烏克蘭"),
    "數位資產": ("bitcoin", "ethereum", "crypto", "coinbase", "microstrategy", "比特幣", "以太幣", "加密貨幣"),
}


@dataclass(frozen=True)
class BenSyncResult:
    news_results: tuple[dict, ...]
    pool_count: int
    history_valid_count: int
    history_failed: tuple[str, ...]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fetch(url: str, timeout: int = 20) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml, application/json, text/html;q=0.8"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), response.headers.get("Content-Type", "application/octet-stream")


def _clean_html(value: str | None) -> str:
    text = re.sub(r"<[^>]+>", " ", html.unescape(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def _parse_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
        except ValueError:
            return None


def parse_rss(payload: bytes) -> list[dict]:
    root = ET.fromstring(payload)
    items: list[dict] = []
    for node in root.iter():
        if node.tag.split("}")[-1] not in {"item", "entry"}:
            continue
        values: dict[str, str] = {}
        for child in node:
            key = child.tag.split("}")[-1]
            if key == "link" and child.attrib.get("href"):
                values[key] = child.attrib["href"]
            elif child.text:
                values[key] = child.text.strip()
        title = _clean_html(values.get("title"))
        url = _clean_html(values.get("link"))
        published = _parse_date(values.get("pubDate") or values.get("published") or values.get("updated"))
        summary = _clean_html(values.get("description") or values.get("summary") or values.get("content"))
        if title and url and published:
            items.append({"title": title, "url": url, "published_at": published, "summary": summary})
    return items[:40]


def _ensure_source(connection: sqlite3.Connection, source: dict, endpoint_url: str, verified_at: str) -> str:
    existing = connection.execute("SELECT id FROM sources WHERE source_id = ?", (source["source_id"],)).fetchone()
    if existing:
        return existing["id"]
    market_code = "TW" if source["market"] == "TW" else "US"
    market = connection.execute("SELECT id FROM markets WHERE country_code = ?", (market_code,)).fetchone()
    source_pk = str(uuid.uuid4())
    connection.execute(
        """
        INSERT INTO sources (
            id, source_id, source_url, publisher, publisher_group, market_id,
            source_type, signal_role, reliability_level, verified_at, evidence_url,
            registry_status, collection_status, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, 'FINANCIAL_NEWS_FEED', 'DISCOVERY', 'B', ?, ?,
                  'ACTIVE', 'PUBLIC_FEED_VERIFIED_ONCE', ?)
        """,
        (source_pk, source["source_id"], endpoint_url, source["name"], source["publisher_group"], market["id"], verified_at, endpoint_url, json.dumps({"verification_scope": "P03B one-time public feed"})),
    )
    return source_pk


def collect_news_once(connection: sqlite3.Connection, fetcher: Callable[[str, int], tuple[bytes, str]] = _fetch) -> tuple[dict, ...]:
    results: list[dict] = []
    for source in NEWS_SOURCES:
        started = _now()
        payload = None
        content_type = "application/rss+xml"
        used_url = source["urls"][0]
        errors: list[str] = []
        for url in source["urls"][:2]:
            used_url = url
            try:
                payload, content_type = fetcher(url, 20)
                break
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as error:
                code = getattr(error, "code", None)
                errors.append(f"HTTP {code}" if code else error.__class__.__name__)
        valid_items: list[dict] = []
        if payload is not None:
            try:
                valid_items = parse_rss(payload)
            except (ET.ParseError, UnicodeError) as error:
                errors.append(f"RSS_PARSE_{error.__class__.__name__}")
        finished = _now()
        status = "SUCCESS" if valid_items else "FAILED"
        reason = None if status == "SUCCESS" else "; ".join(errors) or "NO_VALID_TITLE_TIME_LINK"
        run_id = str(uuid.uuid4())
        connection.execute(
            """INSERT INTO ben_news_runs
               (id, source_key, source_name, endpoint_url, attempted_at, finished_at,
                status, fetched_count, valid_item_count, error_reason)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, source["key"], source["name"], used_url, started, finished, status, len(valid_items), len(valid_items), reason),
        )
        if status == "SUCCESS":
            source_pk = _ensure_source(connection, source, used_url, finished)
            market_code = "TW" if source["market"] == "TW" else "US"
            market_id = connection.execute("SELECT id FROM markets WHERE country_code = ?", (market_code,)).fetchone()["id"]
            collection_run_id = str(uuid.uuid4())
            connection.execute(
                """INSERT INTO collection_runs
                   (id, market_id, source_id, started_at, finished_at, status, item_count, collector_version)
                   VALUES (?, ?, ?, ?, ?, 'SUCCESS', ?, 'ben-news-rss-v1')""",
                (collection_run_id, market_id, source_pk, started, finished, len(valid_items)),
            )
            for item in valid_items:
                content = f"{item['title']}\n{item['summary']}".strip()
                digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
                existing = connection.execute("SELECT id FROM raw_items WHERE original_url = ? OR content_hash = ?", (item["url"], digest)).fetchone()
                raw_id = existing["id"] if existing else str(uuid.uuid4())
                if not existing:
                    connection.execute(
                        """INSERT INTO raw_items
                           (id, collection_run_id, source_id, original_url, canonical_url,
                            original_content, published_at, fetched_at, content_hash, mime_type,
                            raw_payload_json, data_label)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEWS_SOURCE_EVIDENCE')""",
                        (raw_id, collection_run_id, source_pk, item["url"], item["url"], content, item["published_at"], finished, digest, content_type, json.dumps(item, ensure_ascii=False)),
                    )
                connection.execute(
                    """INSERT OR IGNORE INTO ben_news_items
                       (id, raw_item_id, source_key, original_title, source_name, published_at,
                        fetched_at, original_url, public_summary, market, language, content_hash)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (str(uuid.uuid4()), raw_id, source["key"], item["title"], source["name"], item["published_at"], finished, item["url"], item["summary"] or None, source["market"], source["language"], digest),
                )
        connection.commit()
        results.append({"source_key": source["key"], "source_name": source["name"], "status": status, "valid_item_count": len(valid_items), "error_reason": reason, "endpoint_url": used_url})
    return tuple(results)


def build_demo_pool(connection: sqlite3.Connection, limit: int = 30) -> list[dict]:
    latest = connection.execute("SELECT MAX(data_date) FROM normalized_items WHERE record_type = 'LISTED_SECURITY_DAILY_TRADING' AND data_date <> 'UNKNOWN'").fetchone()[0]
    rows = connection.execute(
        """SELECT stock_code, company_name, trade_volume FROM normalized_items
           WHERE record_type = 'LISTED_SECURITY_DAILY_TRADING' AND data_date = ?""",
        (latest,),
    ).fetchall()
    valid = [dict(row) for row in rows if re.fullmatch(r"\d{4}", row["stock_code"] or "")]
    valid.sort(key=lambda row: int(str(row["trade_volume"] or "0").replace(",", "")), reverse=True)
    by_code = {row["stock_code"]: row for row in valid}
    output: list[dict] = []
    for code in MAJOR_STOCKS:
        if code in by_code:
            output.append(by_code[code])
    for row in valid:
        if row["stock_code"] not in {item["stock_code"] for item in output}:
            output.append(row)
        if len(output) >= limit:
            break
    return output[:limit]


def _roc_date(value: str) -> str:
    year, month, day = value.split("/")
    return f"{int(year) + 1911:04d}-{int(month):02d}-{int(day):02d}"


def _number(value: str) -> str:
    cleaned = value.replace(",", "").replace("+", "").strip()
    return cleaned if cleaned not in {"", "--"} else "UNKNOWN"


def _month_keys(latest_date: str) -> tuple[str, str]:
    current = date.fromisoformat(latest_date).replace(day=1)
    previous = date(current.year - (1 if current.month == 1 else 0), 12 if current.month == 1 else current.month - 1, 1)
    return previous.strftime("%Y%m%d"), current.strftime("%Y%m%d")


def collect_history_once(connection: sqlite3.Connection, pool: list[dict], fetcher: Callable[[str, int], tuple[bytes, str]] = _fetch) -> tuple[int, tuple[str, ...]]:
    latest_date = connection.execute("SELECT MAX(data_date) FROM normalized_items WHERE record_type = 'LISTED_SECURITY_DAILY_TRADING' AND data_date <> 'UNKNOWN'").fetchone()[0]
    months = _month_keys(latest_date)
    cached_codes = {
        row["stock_code"]
        for row in connection.execute(
            "SELECT stock_code FROM ben_stock_history WHERE trade_date <= ? GROUP BY stock_code HAVING COUNT(*) >= 21",
            (latest_date,),
        )
    }

    def fetch_stock(stock: dict) -> tuple[dict, list[tuple[str, dict]], str | None]:
        if stock["stock_code"] in cached_codes:
            return stock, [], None
        rows: list[tuple[str, dict]] = []
        try:
            for month in months:
                url = f"https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date={month}&stockNo={stock['stock_code']}&response=json"
                payload, _ = fetcher(url, 20)
                document = json.loads(payload.decode("utf-8"))
                if document.get("stat") != "OK":
                    raise ValueError(document.get("stat", "TWSE_NOT_OK"))
                for values in document.get("data", []):
                    if len(values) < 7:
                        continue
                    row = {
                        "trade_date": _roc_date(values[0]), "trade_volume": int(_number(values[1])),
                        "trade_value": int(_number(values[2])), "opening_price": _number(values[3]),
                        "highest_price": _number(values[4]), "lowest_price": _number(values[5]),
                        "closing_price": _number(values[6]), "raw": values,
                    }
                    rows.append((url, row))
            return stock, rows, None
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as error:
            return stock, [], error.__class__.__name__

    failed: list[str] = []
    fetched_at = _now()
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(fetch_stock, stock) for stock in pool]
        for future in as_completed(futures):
            stock, rows, error = future.result()
            if error:
                failed.append(f"{stock['stock_code']}:{error}")
                continue
            for url, row in rows:
                connection.execute(
                    """INSERT OR IGNORE INTO ben_stock_history
                       (id, stock_code, company_name, trade_date, opening_price, highest_price,
                        lowest_price, closing_price, trade_volume, trade_value, source_url,
                        fetched_at, raw_payload_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (str(uuid.uuid4()), stock["stock_code"], stock["company_name"], row["trade_date"], row["opening_price"], row["highest_price"], row["lowest_price"], row["closing_price"], row["trade_volume"], row["trade_value"], url, fetched_at, json.dumps(row["raw"], ensure_ascii=False)),
                )
    connection.commit()
    valid = connection.execute("SELECT COUNT(*) FROM (SELECT stock_code FROM ben_stock_history GROUP BY stock_code HAVING COUNT(*) >= 21)").fetchone()[0]
    return valid, tuple(sorted(failed))


def sync_ben_radar(connection: sqlite3.Connection) -> BenSyncResult:
    news_results = collect_news_once(connection)
    pool = build_demo_pool(connection)
    history_valid, history_failed = collect_history_once(connection, pool)
    return BenSyncResult(news_results, len(pool), history_valid, history_failed)


def format_volume_lots(shares: int) -> str:
    lots = shares / 1000
    if lots >= 10_000:
        return f"{lots / 10_000:.2f}萬張"
    return f"{lots:,.0f}張"


def format_trade_value(value: int | None) -> str:
    if value is None:
        return "UNKNOWN"
    if value >= 100_000_000:
        return f"新台幣{value / 100_000_000:.2f}億元"
    return f"新台幣{value / 10_000:,.0f}萬元"


def detect_entities(text: str) -> list[str]:
    value = text.lower()
    matches: list[str] = []
    for code, keywords in ENTITY_KEYWORDS.items():
        for keyword in keywords:
            normalized = keyword.lower()
            if re.fullmatch(r"[a-z0-9 .-]+", normalized):
                if re.search(rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])", value):
                    matches.append(code)
                    break
            elif normalized in value:
                matches.append(code)
                break
    return matches


def chinese_summary(title: str) -> str:
    entities = detect_entities(title)
    topics = [name for name, keywords in TOPIC_KEYWORDS.items() if any(keyword.lower() in title.lower() for keyword in keywords)]
    parts = entities[:2] + topics[:1]
    if parts:
        return f"這則報導聚焦{'、'.join(parts)}相關最新動態，具體事實與數字以原文為準。"
    return f"這是一則最新財經報導；原始主題為「{title[:55]}{'…' if len(title) > 55 else ''}」。"


def _title_tokens(title: str) -> set[str]:
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", title.lower())
    words = {word for word in normalized.split() if len(word) > 1 and word not in {"the", "and", "for", "with", "from", "says"}}
    chinese = "".join(re.findall(r"[\u4e00-\u9fff]", normalized))
    words.update(chinese[index:index + 2] for index in range(max(0, len(chinese) - 1)))
    return words


def cluster_news(rows: list[dict]) -> list[dict]:
    clusters: list[dict] = []
    for row in sorted(rows, key=lambda item: item["published_at"], reverse=True):
        tokens = _title_tokens(row["original_title"])
        target = None
        for cluster in clusters:
            union = tokens | cluster["tokens"]
            similarity = len(tokens & cluster["tokens"]) / len(union) if union else 0
            if similarity >= 0.48:
                target = cluster
                break
        if target is None:
            clusters.append({"tokens": tokens, "items": [row]})
        else:
            target["items"].append(row)
            target["tokens"].update(tokens)
    return clusters


def compute_anomalies(connection: sqlite3.Connection, news_rows: list[dict]) -> tuple[list[dict], int, int]:
    codes = [row["stock_code"] for row in connection.execute("SELECT DISTINCT stock_code FROM ben_stock_history ORDER BY stock_code LIMIT 30")]
    latest_date = connection.execute("SELECT MAX(data_date) FROM normalized_items WHERE record_type = 'LISTED_SECURITY_DAILY_TRADING' AND data_date <> 'UNKNOWN'").fetchone()[0]
    news_text = " ".join(row["original_title"] for row in news_rows).lower()
    anomalies: list[dict] = []
    valid_count = 0
    for code in codes:
        rows = [dict(row) for row in connection.execute("SELECT * FROM ben_stock_history WHERE stock_code = ? AND trade_date <= ? ORDER BY trade_date", (code, latest_date))]
        if len(rows) < 21:
            continue
        current, previous = rows[-1], rows[-21:-1]
        if current["trade_date"] != latest_date:
            continue
        valid_count += 1
        median_volume = statistics.median(row["trade_volume"] for row in previous)
        if not median_volume:
            continue
        rvol = current["trade_volume"] / median_volume
        close = float(current["closing_price"])
        prior_close = float(previous[-1]["closing_price"])
        change_pct = (close / prior_close - 1) * 100 if prior_close else 0
        prior_high = max(float(row["highest_price"]) for row in previous)
        prior_low = min(float(row["lowest_price"]) for row in previous)
        breakout = "突破20日高點" if close > prior_high and rvol >= 1.5 else "跌破20日低點" if close < prior_low and rvol >= 1.5 else None
        relative = rvol >= 2
        resonance = abs(change_pct) >= 3 and rvol >= 2
        associated_news = code in news_text or current["company_name"].lower() in news_text
        if not (relative or breakout or resonance):
            continue
        if median_volume < 1_000_000 and code not in MAJOR_STOCKS and not associated_news:
            continue
        level = "極端放量" if rvol >= 5 else "強放量" if rvol >= 3 else "明顯放量" if rvol >= 2 else "區間突破"
        rules = [level]
        if breakout:
            rules.append(breakout)
        if resonance:
            rules.append("價量共振")
        anomalies.append({
            **current, "rvol": rvol, "change_pct": change_pct, "rules": rules,
            "breakout": breakout, "relative": relative, "resonance": resonance,
            "associated_news": associated_news, "volume_label": format_volume_lots(current["trade_volume"]),
            "trade_value_label": format_trade_value(current["trade_value"]),
            "raw_volume_label": f"原始成交量 {current['trade_volume']:,} 股",
            "explanation": f"今日成交{format_volume_lots(current['trade_volume'])}，為過去20日中位量的{rvol:.1f}倍" + (f"；收盤價{breakout}" if breakout else "") + (f"；股價變動{change_pct:+.2f}%與量能同步異常" if resonance else "") + "。",
        })
    anomalies.sort(key=lambda item: (-item["rvol"], 0 if item["breakout"] else 1, -abs(item["change_pct"]), 0 if item["associated_news"] else 1, 0 if item["stock_code"] in MAJOR_STOCKS else 1))
    return anomalies, len(codes), valid_count


def build_hotspots(news_rows: list[dict], anomalies: list[dict], now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    anomaly_codes = {item["stock_code"] for item in anomalies}
    output: list[dict] = []
    source_importance = {source["key"]: source["importance"] for source in NEWS_SOURCES}
    for cluster in cluster_news(news_rows):
        items = cluster["items"]
        primary = items[0]
        published = datetime.fromisoformat(primary["published_at"].replace("Z", "+00:00"))
        hours = max(0, (now - published.astimezone(timezone.utc)).total_seconds() / 3600)
        recency = 30 if hours <= 2 else 24 if hours <= 6 else 18 if hours <= 12 else 12
        independent_sources = len({item["source_name"] for item in items})
        cross = 20 if independent_sources >= 3 else 12 if independent_sources == 2 else 0
        entities = sorted({entity for item in items for entity in detect_entities(item["original_title"])})
        text = " ".join(item["original_title"] for item in items).lower()
        important = any(keyword.lower() in text for keywords in TOPIC_KEYWORDS.values() for keyword in keywords) or bool(entities)
        importance = 20 if important else 8
        linked = sorted(set(entities) & anomaly_codes)
        score = min(100, recency + max(source_importance.get(item["source_key"], 10) for item in items) + cross + importance + (10 if linked else 0))
        reasons = [f"{hours:.1f}小時內發布", f"來源重要度 {max(source_importance.get(item['source_key'], 10) for item in items)}/20"]
        reasons.append(f"{independent_sources}個獨立來源交叉報導" if independent_sources > 1 else "目前為單一來源，仍需交叉核實")
        if entities:
            reasons.append(f"涉及重要公司或標的：{'、'.join(entities)}")
        if linked:
            reasons.append(f"與相對量異動 {'、'.join(linked)} 同時出現")
        impacts = entities or (["台灣市場"] if primary["market"] == "TW" else ["美國／國際市場"])
        angle = "跨市場聯動" if len({item["market"] for item in items}) > 1 else "重要公司影響" if entities else "後續可持續追蹤"
        output.append({
            "primary": primary, "items": items, "source_count": independent_sources,
            "score": score, "reasons": reasons, "summary_zh": chinese_summary(primary["original_title"]),
            "entities": entities, "impacts": impacts, "linked_anomalies": linked,
            "what_happened": f"{primary['source_name']}發布題為「{primary['original_title']}」的報導；目前僅按抓取到的標題與公開摘要整理。",
            "why_watch": "；".join(reasons) + "。",
            "possible_impact": f"可能涉及{'、'.join(impacts)}；這是待驗證的影響範圍，不代表已確認發生價格影響。",
            "content_angle": f"適合從「{angle}」角度持續追蹤，並保留來源差異與未確認部分。",
            "questions": [
                f"原文提到的事件是否已由第二個獨立來源或公司／監管公告確認？",
                f"{('、'.join(entities) if entities else '相關市場')}下一交易時段是否出現成交量、價格或公告層面的同步變化？",
            ],
        })
    output.sort(key=lambda item: (item["score"], item["primary"]["published_at"]), reverse=True)
    return output[:20]
