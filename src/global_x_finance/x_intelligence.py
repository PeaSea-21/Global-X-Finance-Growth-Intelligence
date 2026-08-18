from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import random
import re
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from opencc import OpenCC

from .ben_radar import NEWS_SOURCES, TOPIC_KEYWORDS, chinese_summary, detect_entities
from .errors import ValidationError
from .evidence import EvidenceStore
from .event_clustering import SAME_EVENT, decide_event_pair, event_fingerprint
from .realtime_radar import parse_datetime
from .translation_summary import TranslationSummaryAdapter


X_USER_AGENT = "GlobalXFinanceRadar/0.7 (read-only research demo)"
PRIORITY_MAP = {"核心关注": "CORE", "观察名单": "WATCH", "低置信观察": "LOW_CONFIDENCE"}
PRIORITY_INTERVAL = {"CORE": 10, "WATCH": 30, "LOW_CONFIDENCE": 60}
PRIORITY_LABEL = {value: key for key, value in PRIORITY_MAP.items()}
PUBLISHER_GROUPS = {
    "nvidia": "nvidia",
    "nvidiaai": "nvidia",
    "openaiNewsroom".lower(): "openai",
    "openaidevs": "openai",
    "anthropicai": "anthropic",
    "claudeai": "anthropic",
    "darioamodei": "anthropic",
}
YAHOO_FINANCE_ENDPOINTS = (
    "https://finance.yahoo.com/news/rssindex",
    "https://finance.yahoo.com/rss/topstories",
)
ACTION_KEYWORDS = {
    "earnings": ("earnings", "revenue", "profit", "guidance", "quarter results", "財報", "营收", "營收", "獲利", "获利", "展望"),
    "launch": ("launch", "release", "announce", "debut", "unveil", "roll out", "推出", "發布", "发布", "發表", "上线", "上線"),
    "investment": ("invest", "funding", "stake", "acquire", "acquisition", "buyback", "weighs", "in talks", "收購", "收购", "投資", "投资", "融資", "融资", "持股", "入股", "回購"),
    "partnership": ("partner", "deal", "agreement", "contract", "order", "supply", "data center", "合作", "協議", "协议", "訂單", "订单", "供應", "資料中心", "數據中心"),
    "policy": ("policy", "regulation", "tariff", "ban", "監管", "监管", "政策", "關稅", "关税", "禁令"),
    "security": ("outage", "breach", "attack", "strike", "fire", "漏洞", "中斷", "中断", "攻擊", "攻击", "襲擊", "起火"),
    "market_move": ("surge", "plunge", "rally", "selloff", "jumps", "slumps", "record high", "上漲", "上涨", "下跌", "暴跌", "大漲", "大涨", "創高", "新高"),
}

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
    "earnings": "財報與營運數據更新",
    "launch": "產品或技術發布",
    "investment": "投資與資本動作",
    "partnership": "合作、訂單或供應鏈進展",
    "policy": "政策與監管變化",
    "security": "安全或突發事件",
    "market_move": "價格與市場異動",
}

TOPIC_NAMES_ZH = {
    "半導體與AI": "AI 與半導體",
    "利率與宏觀": "利率與宏觀",
    "財報與公司": "公司與財報",
    "關稅與政策": "政策與關稅",
    "能源與原物料": "能源與原物料",
    "地緣政治": "地緣政治",
    "數位資產": "數位資產",
}


@dataclass(frozen=True)
class XAccount:
    handle: str
    display_name: str
    bio: str
    follower_snapshot: int | None
    region: str
    profile_url: str
    account_role: str
    market_scope: str
    impact_path: str
    priority: str
    usage_note: str
    publisher_group: str

    @property
    def expected_interval_minutes(self) -> int:
        return PRIORITY_INTERVAL[self.priority]


@dataclass(frozen=True)
class HttpResult:
    status_code: int
    body: bytes
    headers: dict[str, str]
    url: str


@dataclass(frozen=True)
class XCollectionResult:
    handle: str
    status: str
    http_status: int | None
    fetched_count: int
    kept_count: int
    new_count: int
    duplicate_count: int
    repost_count: int
    attempt_count: int
    retry_after: str | None
    error_reason: str | None


def utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _csv_int(value: str) -> int | None:
    cleaned = re.sub(r"[^0-9]", "", value or "")
    return int(cleaned) if cleaned else None


def publisher_group_for_handle(handle: str) -> str:
    normalized = handle.lower().lstrip("@")
    return PUBLISHER_GROUPS.get(normalized, f"x:{normalized}")


def load_x_accounts(path: str | Path, *, expected_count: int | None = 29) -> list[XAccount]:
    csv_path = Path(path)
    if not csv_path.exists():
        raise ValidationError(f"X account CSV not found: {csv_path}")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {
        "X账号", "账号名称", "简介", "粉丝数", "地区", "X链接", "账号角色",
        "主要市场", "影响股票行情的路径", "关注优先级", "可信度／使用提示",
    }
    missing = required - set(rows[0] if rows else ())
    if missing:
        raise ValidationError("X account CSV missing columns: " + ", ".join(sorted(missing)))
    if expected_count is not None and len(rows) != expected_count:
        raise ValidationError(f"X account CSV must contain {expected_count} accounts; got {len(rows)}")
    output: list[XAccount] = []
    seen: set[str] = set()
    for line, row in enumerate(rows, 2):
        handle = (row["X账号"] or "").strip().lstrip("@")
        priority_label = (row["关注优先级"] or "").strip()
        if not re.fullmatch(r"[A-Za-z0-9_]{1,30}", handle):
            raise ValidationError(f"X account CSV row {line}: invalid handle")
        if handle.lower() in seen:
            raise ValidationError(f"X account CSV row {line}: duplicate handle {handle}")
        if priority_label not in PRIORITY_MAP:
            raise ValidationError(f"X account CSV row {line}: unsupported priority {priority_label}")
        profile_url = (row["X链接"] or "").strip()
        if profile_url.rstrip("/").lower() not in {
            f"https://x.com/{handle}".lower(), f"https://twitter.com/{handle}".lower()
        }:
            raise ValidationError(f"X account CSV row {line}: profile URL does not match @{handle}")
        seen.add(handle.lower())
        output.append(XAccount(
            handle=handle,
            display_name=(row["账号名称"] or handle).strip(),
            bio=(row["简介"] or "").strip(),
            follower_snapshot=_csv_int(row["粉丝数"]),
            region=(row["地区"] or "").strip(),
            profile_url=profile_url,
            account_role=(row["账号角色"] or "UNKNOWN").strip(),
            market_scope=(row["主要市场"] or "UNKNOWN").strip(),
            impact_path=(row["影响股票行情的路径"] or "").strip(),
            priority=PRIORITY_MAP[priority_label],
            usage_note=(row["可信度／使用提示"] or "").strip(),
            publisher_group=publisher_group_for_handle(handle),
        ))
    return output


def account_counts(accounts: Iterable[XAccount]) -> dict[str, int]:
    rows = list(accounts)
    return {
        "total": len(rows),
        "core": sum(row.priority == "CORE" for row in rows),
        "watch": sum(row.priority == "WATCH" for row in rows),
        "low_confidence": sum(row.priority == "LOW_CONFIDENCE" for row in rows),
    }


def import_x_accounts(connection: sqlite3.Connection, accounts: Iterable[XAccount]) -> int:
    count = 0
    with connection:
        for account in accounts:
            existing = connection.execute(
                "SELECT id FROM ben_x_accounts WHERE handle = ? COLLATE NOCASE", (account.handle,)
            ).fetchone()
            account_id = existing["id"] if existing else str(uuid.uuid4())
            connection.execute(
                """INSERT INTO ben_x_accounts (
                       id, handle, display_name, bio, follower_snapshot, region, profile_url,
                       account_role, market_scope, impact_path, account_priority, usage_note,
                       publisher_group, expected_interval_minutes, enabled
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(handle) DO UPDATE SET
                       display_name=excluded.display_name, bio=excluded.bio,
                       follower_snapshot=excluded.follower_snapshot, region=excluded.region,
                       profile_url=excluded.profile_url, account_role=excluded.account_role,
                       market_scope=excluded.market_scope, impact_path=excluded.impact_path,
                       account_priority=excluded.account_priority, usage_note=excluded.usage_note,
                       publisher_group=excluded.publisher_group,
                       expected_interval_minutes=excluded.expected_interval_minutes,
                       enabled=excluded.enabled, updated_at=CURRENT_TIMESTAMP""",
                (
                    account_id, account.handle, account.display_name, account.bio,
                    account.follower_snapshot, account.region, account.profile_url,
                    account.account_role, account.market_scope, account.impact_path,
                    account.priority, account.usage_note, account.publisher_group,
                    account.expected_interval_minutes, 0 if account.priority == "LOW_CONFIDENCE" else 1,
                ),
            )
            count += 1
    return count


def _http_get(url: str, timeout: int = 25) -> HttpResult:
    request = urllib.request.Request(url, headers={
        "User-Agent": X_USER_AGENT,
        "Accept": "application/json,text/plain,*/*",
    })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return HttpResult(int(response.status), response.read(), dict(response.headers.items()), url)
    except urllib.error.HTTPError as error:
        return HttpResult(int(error.code), error.read(), dict(error.headers.items()) if error.headers else {}, url)


def fetch_x_page(account: XAccount, since: int | None) -> HttpResult:
    params: dict[str, Any] = {"count": 20}
    if since is not None:
        params["since"] = since
    url = (
        f"https://api.fxtwitter.com/2/profile/{urllib.parse.quote(account.handle)}/statuses?"
        + urllib.parse.urlencode(params)
    )
    return _http_get(url)


def _response_status(page: HttpResult) -> tuple[str, str | None]:
    if page.status_code == 204:
        return "NO_NEW", None
    if page.status_code == 429:
        return "RATE_LIMITED", "HTTP 429"
    if page.status_code == 404:
        text = page.body.decode("utf-8", errors="replace").lower()
        return ("PRIVATE", "private account") if "private" in text else ("NOT_FOUND", "HTTP 404")
    if page.status_code == 403:
        return "PRIVATE", "HTTP 403"
    if page.status_code != 200:
        return "FAILED", f"HTTP {page.status_code}"
    return "SUCCESS", None


def _fetch_account(
    account: XAccount,
    since: int | None,
    fetcher: Callable[[XAccount, int | None], HttpResult],
    sleeper: Callable[[float], None],
) -> tuple[HttpResult | None, str, int, str | None]:
    page: HttpResult | None = None
    error_reason: str | None = None
    attempts = 0
    for attempt in range(1, 3):
        attempts = attempt
        sleeper(random.uniform(0.05, 0.20))
        try:
            page = fetcher(account, since)
        except (OSError, TimeoutError, urllib.error.URLError) as error:
            error_reason = f"{type(error).__name__}: {error}"
            if attempt == 1:
                continue
            return None, "FAILED", attempts, error_reason
        status, error_reason = _response_status(page)
        if status in {"RATE_LIMITED", "FAILED"} and page.status_code >= 500 and attempt == 1:
            sleeper(random.uniform(0.2, 0.6))
            continue
        if status == "RATE_LIMITED" and attempt == 1:
            retry_after = page.headers.get("Retry-After") or page.headers.get("retry-after")
            try:
                wait_seconds = float(retry_after) if retry_after else 0
            except ValueError:
                wait_seconds = 0
            if 0 < wait_seconds <= 30:
                sleeper(wait_seconds)
                continue
        return page, status, attempts, error_reason
    return page, "FAILED", attempts, error_reason or "retry exhausted"


def _json_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted({str(item).strip() for item in value if str(item).strip()})


def _extract_external_urls(item: dict[str, Any]) -> list[str]:
    values: set[str] = set()
    card = item.get("card") if isinstance(item.get("card"), dict) else {}
    if isinstance(card.get("url"), str) and card["url"].startswith("http"):
        values.add(card["url"])
    raw_text = item.get("raw_text") if isinstance(item.get("raw_text"), dict) else {}
    for facet in raw_text.get("facets", []) if isinstance(raw_text.get("facets"), list) else []:
        if isinstance(facet, dict) and facet.get("type") == "url":
            value = str(facet.get("replacement") or facet.get("original") or "")
            if value.startswith("http"):
                values.add(value)
    return sorted(values)


def _metrics(item: dict[str, Any]) -> tuple[int, int, int, int, int | None]:
    def number(key: str) -> int:
        try:
            return max(0, int(item.get(key) or 0))
        except (TypeError, ValueError):
            return 0
    try:
        views = int(item.get("views")) if item.get("views") is not None else None
    except (TypeError, ValueError):
        views = None
    return number("likes"), number("reposts"), number("quotes"), number("replies"), views


def _normalize_post(account: XAccount, item: dict[str, Any], fetched_at: str) -> dict[str, Any] | None:
    post_id = str(item.get("id") or "").strip()
    text = str(item.get("text") or item.get("raw_text") or "").strip()
    created = parse_datetime(item.get("created_at"))
    if created is None and item.get("created_timestamp") is not None:
        try:
            created = datetime.fromtimestamp(float(item["created_timestamp"]), timezone.utc)
        except (TypeError, ValueError, OSError):
            created = None
    if not post_id or not text or created is None:
        return None
    author = item.get("author") if isinstance(item.get("author"), dict) else {}
    author_handle = str(author.get("screen_name") or account.handle).lstrip("@")
    url = str(item.get("url") or f"https://x.com/{author_handle}/status/{post_id}")
    reposted_by = item.get("reposted_by")
    is_repost = bool(reposted_by) or author_handle.lower() != account.handle.lower()
    quote = item.get("quote") if isinstance(item.get("quote"), dict) else None
    replying_to = item.get("replying_to")
    if replying_to:
        return None
    likes, reposts, quotes, replies, views = _metrics(item)
    follower_count = None
    try:
        follower_count = int(author.get("followers")) if author.get("followers") is not None else None
    except (TypeError, ValueError):
        follower_count = None
    mentions = sorted(set(re.findall(r"@([A-Za-z0-9_]{1,30})", text)))
    hashtags = sorted(set(re.findall(r"#([\w\u4e00-\u9fff]+)", text)))
    entities = detect_entities(text)
    return {
        "post_id": post_id,
        "author_handle": author_handle,
        "author_name": str(author.get("name") or account.display_name),
        "original_text": text,
        "original_language": str(item.get("lang") or "UNKNOWN"),
        "created_at": utc_iso(created),
        "fetched_at": fetched_at,
        "original_url": url,
        "likes": likes, "reposts": reposts, "quotes": quotes, "replies": replies, "views": views,
        "follower_count": follower_count or account.follower_snapshot,
        "follower_count_source": "FXTWITTER" if follower_count is not None else "CSV_SNAPSHOT" if account.follower_snapshot is not None else "UNKNOWN",
        "external_urls": _extract_external_urls(item),
        "mentioned_accounts": mentions,
        "hashtags": hashtags,
        "related_companies": entities,
        "related_tickers": entities,
        "is_repost": is_repost,
        "is_quote": quote is not None,
        "quoted_post_id": str(quote.get("id")) if quote and quote.get("id") else None,
        "raw_source": item,
        "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def _ensure_x_source(connection: sqlite3.Connection, account: XAccount, verified_at: str) -> None:
    market_code = "TW" if "台" in account.market_scope else "US"
    market = connection.execute("SELECT id FROM markets WHERE country_code = ?", (market_code,)).fetchone()
    if market is None:
        market = connection.execute("SELECT id FROM markets WHERE country_code = 'TW'").fetchone()
    source_id = f"BEN-X-{account.handle.upper()}"
    existing = connection.execute("SELECT id FROM sources WHERE source_id = ?", (source_id,)).fetchone()
    internal_id = existing["id"] if existing else str(uuid.uuid4())
    connection.execute(
        """INSERT INTO sources (
               id, source_id, source_url, publisher, publisher_group, market_id,
               source_type, signal_role, reliability_level, verified_at, evidence_url,
               registry_status, collection_status, metadata_json
           ) VALUES (?, ?, ?, ?, ?, ?, 'X_ACCOUNT', 'OPINION', 'D', ?, ?,
                     'ACTIVE', 'RADAR_VERIFIED', ?)
           ON CONFLICT(source_id) DO UPDATE SET
               publisher=excluded.publisher, publisher_group=excluded.publisher_group,
               verified_at=excluded.verified_at, evidence_url=excluded.evidence_url,
               metadata_json=excluded.metadata_json, updated_at=CURRENT_TIMESTAMP""",
        (
            internal_id, source_id, account.profile_url, account.display_name,
            account.publisher_group, market["id"], verified_at, account.profile_url,
            json.dumps({"adapter": "FXTWITTER_V2_READ_ONLY", "terms_status": "UNKNOWN", "automatic_publishing": False}, ensure_ascii=False),
        ),
    )


def _persist_posts(
    connection: sqlite3.Connection,
    account: XAccount,
    account_id: str,
    items: list[dict[str, Any]],
    fetched_at: str,
) -> tuple[int, int, int]:
    source_id = f"BEN-X-{account.handle.upper()}"
    new_count = duplicate_count = repost_count = 0
    store = EvidenceStore(connection)
    for post in items:
        repost_count += int(post["is_repost"])
        existing = connection.execute(
            "SELECT id FROM ben_x_posts WHERE platform='X' AND post_id=?", (post["post_id"],)
        ).fetchone()
        if existing:
            duplicate_count += 1
            connection.execute(
                """UPDATE ben_x_posts SET likes=?, reposts=?, quotes=?, replies=?, views=?,
                       follower_count=?, follower_count_source=?, fetched_at=?, last_engagement_at=?
                   WHERE id=?""",
                (
                    post["likes"], post["reposts"], post["quotes"], post["replies"], post["views"],
                    post["follower_count"], post["follower_count_source"], fetched_at, fetched_at, existing["id"],
                ),
            )
        else:
            evidence = store.save_raw_item(
                source_id=source_id,
                original_url=post["original_url"],
                original_content=post["original_text"],
                published_at=post["created_at"],
                fetched_at=fetched_at,
                mime_type="application/json",
                raw_payload=post["raw_source"],
                data_label="RAW_EVIDENCE",
                commit=False,
            )
            connection.execute(
                """INSERT INTO ben_x_posts (
                       id, raw_item_id, account_id, platform, post_id, author_handle,
                       author_name, publisher_group, account_role, account_priority,
                       original_text, original_language, created_at, fetched_at, original_url,
                       likes, reposts, quotes, replies, views, follower_count,
                       follower_count_source, external_urls_json, mentioned_accounts_json,
                       hashtags_json, related_companies_json, related_tickers_json,
                       is_repost, is_quote, quoted_post_id, raw_source_json, content_hash,
                       last_engagement_at
                   ) VALUES (?, ?, ?, 'X', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()), evidence.id, account_id, post["post_id"], post["author_handle"],
                    post["author_name"], account.publisher_group, account.account_role, account.priority,
                    post["original_text"], post["original_language"], post["created_at"], fetched_at,
                    post["original_url"], post["likes"], post["reposts"], post["quotes"], post["replies"],
                    post["views"], post["follower_count"], post["follower_count_source"],
                    json.dumps(post["external_urls"], ensure_ascii=False),
                    json.dumps(post["mentioned_accounts"], ensure_ascii=False),
                    json.dumps(post["hashtags"], ensure_ascii=False),
                    json.dumps(post["related_companies"], ensure_ascii=False),
                    json.dumps(post["related_tickers"], ensure_ascii=False), int(post["is_repost"]),
                    int(post["is_quote"]), post["quoted_post_id"],
                    json.dumps(post["raw_source"], ensure_ascii=False), post["content_hash"], fetched_at,
                ),
            )
            new_count += 1
        connection.execute(
            """INSERT OR IGNORE INTO ben_x_engagement_snapshots
               (id, post_id, fetched_at, likes, reposts, quotes, replies, views, follower_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()), post["post_id"], fetched_at, post["likes"], post["reposts"],
                post["quotes"], post["replies"], post["views"], post["follower_count"],
            ),
        )
    return new_count, duplicate_count, repost_count


def collect_x_accounts_once(
    connection: sqlite3.Connection,
    accounts: Iterable[XAccount],
    *,
    now: datetime | None = None,
    force: bool = False,
    include_low_confidence: bool = False,
    fetcher: Callable[[XAccount, int | None], HttpResult] = fetch_x_page,
    sleeper: Callable[[float], None] = time.sleep,
) -> list[XCollectionResult]:
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    account_rows = list(accounts)
    import_x_accounts(connection, account_rows)
    due: list[tuple[XAccount, sqlite3.Row, int | None]] = []
    results: list[XCollectionResult] = []
    for account in account_rows:
        row = connection.execute(
            "SELECT * FROM ben_x_accounts WHERE handle=? COLLATE NOCASE", (account.handle,)
        ).fetchone()
        if account.priority == "LOW_CONFIDENCE" and not include_low_confidence:
            if row["monitoring_status"] == "NOT_STARTED":
                with connection:
                    connection.execute(
                        "UPDATE ben_x_accounts SET monitoring_status='DISABLED', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                        (row["id"],),
                    )
            results.append(XCollectionResult(account.handle, "DISABLED", None, 0, 0, 0, 0, 0, 0, None, "low-confidence monitoring disabled"))
            continue
        last_run = parse_datetime(row["last_run_at"])
        if not force and last_run and current < last_run + timedelta(minutes=row["expected_interval_minutes"]):
            continue
        since = int(row["last_success_timestamp"] or (current - timedelta(hours=24)).timestamp()) - (120 if row["last_success_timestamp"] else 0)
        due.append((account, row, since))

    fetched: dict[str, tuple[HttpResult | None, str, int, str | None]] = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(_fetch_account, account, since, fetcher, sleeper): account.handle
            for account, _, since in due
        }
        for future in as_completed(futures):
            fetched[futures[future]] = future.result()

    cutoff = current - timedelta(hours=24)
    for account, row, _ in due:
        attempted = utc_iso(current)
        page, status, attempt_count, error = fetched[account.handle]
        fetched_count = kept_count = new_count = duplicate_count = repost_count = 0
        retry_after = None
        http_status = page.status_code if page else None
        items: list[dict[str, Any]] = []
        if page:
            retry_after = page.headers.get("Retry-After") or page.headers.get("retry-after")
        if status == "SUCCESS" and page:
            try:
                payload = json.loads(page.body.decode("utf-8"))
                raw_results = payload.get("results") if isinstance(payload, dict) else None
                if not isinstance(raw_results, list):
                    raise ValueError("FxTwitter response lacks results array")
                fetched_count = len(raw_results)
                fetched_at = utc_iso(current)
                for item in raw_results:
                    if not isinstance(item, dict):
                        continue
                    normalized = _normalize_post(account, item, fetched_at)
                    if normalized and parse_datetime(normalized["created_at"]) >= cutoff:
                        items.append(normalized)
                kept_count = len(items)
                if not items:
                    status = "NO_NEW"
                else:
                    with connection:
                        _ensure_x_source(connection, account, fetched_at)
                        new_count, duplicate_count, repost_count = _persist_posts(
                            connection, account, row["id"], items, fetched_at
                        )
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as parse_error:
                status = "FAILED"
                error = f"{type(parse_error).__name__}: {parse_error}"
        # A successful request advances the collection checkpoint even when it
        # returns no eligible post. Otherwise a quiet account would repeatedly
        # scan the same old window on every scheduled run.
        latest_timestamp = int(current.timestamp()) if status in {"SUCCESS", "NO_NEW"} else None
        finished = utc_iso(datetime.now(timezone.utc))
        failures = 0 if status in {"SUCCESS", "NO_NEW"} else int(row["consecutive_failures"] or 0) + 1
        with connection:
            connection.execute(
                """UPDATE ben_x_accounts SET last_run_at=?, monitoring_status=?,
                       last_http_status=?, last_error=?, consecutive_failures=?,
                       last_success_timestamp=CASE WHEN ? IN ('SUCCESS','NO_NEW')
                           THEN MAX(COALESCE(last_success_timestamp,0), COALESCE(?,last_success_timestamp,0))
                           ELSE last_success_timestamp END,
                       updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                (attempted, status, http_status, error, failures, status, latest_timestamp, row["id"]),
            )
            connection.execute(
                """INSERT INTO ben_x_runs (
                       id, account_id, attempted_at, finished_at, status, http_status,
                       retry_after, attempt_count, fetched_count, kept_count, new_count,
                       duplicate_count, repost_count, error_reason
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()), row["id"], attempted, finished, status, http_status,
                    retry_after, attempt_count, fetched_count, kept_count, new_count,
                    duplicate_count, repost_count, error,
                ),
            )
        results.append(XCollectionResult(
            account.handle, status, http_status, fetched_count, kept_count, new_count,
            duplicate_count, repost_count, attempt_count, retry_after, error,
        ))
    return sorted(results, key=lambda item: item.handle.lower())


def filter_time_window(rows: Iterable[dict[str, Any]], *, now: datetime, hours: int, field: str) -> list[dict[str, Any]]:
    cutoff = now.astimezone(timezone.utc) - timedelta(hours=hours)
    output = []
    for row in rows:
        published = parse_datetime(row.get(field))
        if published is not None and cutoff <= published <= now.astimezone(timezone.utc):
            output.append(row)
    return output


def _normalized_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return ""
    if parsed.scheme not in {"http", "https"}:
        return ""
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
    query = [(key, value) for key, value in query if not key.lower().startswith("utm_")]
    return urllib.parse.urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), urllib.parse.urlencode(query), ""))


def event_actions(text: str) -> set[str]:
    lowered = text.lower()
    return {name for name, words in ACTION_KEYWORDS.items() if any(word.lower() in lowered for word in words)}


def event_topics(text: str) -> set[str]:
    lowered = f" {text.lower()} "
    return {
        name for name, words in TOPIC_KEYWORDS.items()
        if any(word.lower() in lowered for word in words)
    }


def _looks_like_chinese(text: str) -> bool:
    if not text or "�" in text:
        return False
    chinese_count = len(re.findall(r"[\u4e00-\u9fff]", text))
    suspicious = len(re.findall(r"[ӍҪؑݲ]", text))
    return chinese_count >= 4 and suspicious == 0


def _display_title_zh(text: str, entities: list[str], actions: list[str], topics: list[str]) -> tuple[str, str]:
    if _looks_like_chinese(text):
        compact = re.sub(r"\s+", " ", text).strip()
        return compact[:72] + ("…" if len(compact) > 72 else ""), "原文中文"
    subjects = [ENTITY_NAMES_ZH.get(code, code) for code in entities[:2]]
    action = ACTION_NAMES_ZH.get(actions[0]) if actions else None
    topic = TOPIC_NAMES_ZH.get(topics[0]) if topics else None
    if subjects and action:
        return f"{'、'.join(subjects)}：{action}引發市場關注", "規則中文摘要"
    if subjects and topic:
        return f"{'、'.join(subjects)}相關{topic}討論升溫", "規則中文摘要"
    if subjects:
        return f"{'、'.join(subjects)}相關動態進入內容雷達", "規則中文摘要"
    if topic and action:
        return f"{topic}：{action}正在發酵", "規則中文摘要"
    if topic:
        return f"{topic}相關動態正在發酵", "規則中文摘要"
    return "中文摘要生成中", "待人工補充"


def _snapshot_acceleration(snapshots: list[dict[str, Any]]) -> tuple[float | None, float | None, int | None]:
    ordered = sorted(
        (row for row in snapshots if parse_datetime(row.get("fetched_at")) is not None),
        key=lambda row: row["fetched_at"],
    )
    if len(ordered) < 2:
        return None, None, None

    def metric(row: dict[str, Any]) -> float:
        if row.get("views") is not None:
            return float(row["views"])
        return float(row.get("likes") or 0) + 2 * float(row.get("reposts") or 0) + 2 * float(row.get("quotes") or 0) + .5 * float(row.get("replies") or 0)

    rates: list[float] = []
    for previous, current in zip(ordered, ordered[1:]):
        elapsed = (parse_datetime(current["fetched_at"]) - parse_datetime(previous["fetched_at"])).total_seconds() / 3600
        if elapsed > 0:
            rates.append(max(0.0, metric(current) - metric(previous)) / elapsed)
    if not rates:
        return None, None, None
    acceleration = None
    if len(rates) >= 2:
        acceleration = (rates[-1] - rates[-2]) / max(abs(rates[-2]), 1.0) * 100
    view_delta = None
    if ordered[-1].get("views") is not None and ordered[-2].get("views") is not None:
        view_delta = int(ordered[-1]["views"]) - int(ordered[-2]["views"])
    return rates[-1], acceleration, view_delta


def _tokens(text: str) -> set[str]:
    lowered = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", text.lower())
    words = {word for word in lowered.split() if len(word) > 1}
    chinese = "".join(re.findall(r"[\u4e00-\u9fff]", lowered))
    words.update(chinese[index:index + 2] for index in range(max(0, len(chinese) - 1)))
    return words


def _role_authority(role: str, priority: str) -> int:
    if any(key in role for key in ("官方", "通讯社", "通訊社", "主流财经媒体", "主流財經媒體")):
        return 20
    if any(key in role for key in ("研究机构", "研究機構", "券商分析师", "券商分析師")):
        return 17
    if "KOL" in role or "研究" in role or "高管" in role:
        return 14
    return {"CORE": 12, "WATCH": 9, "LOW_CONFIDENCE": 5}.get(priority, 5)


def score_x_posts(
    rows: list[dict[str, Any]],
    now: datetime,
    engagement_snapshots: dict[str, list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    scored = [dict(row) for row in rows]
    velocity_values: list[float] = []
    signatures: dict[str, set[str]] = {}
    for row in scored:
        age = max((now - parse_datetime(row["created_at"])).total_seconds() / 3600, 0)
        weighted = row["likes"] + 2 * row["reposts"] + 2 * row["quotes"] + 0.5 * row["replies"]
        velocity = weighted / max(age, 0.25)
        follower_count = max(int(row.get("follower_count") or 0), 1)
        normalized = velocity / follower_count * 10_000
        row.update(
            age_hours=age,
            weighted_engagement=weighted,
            engagement_velocity=velocity,
            normalized_velocity=normalized,
            view_velocity=(float(row["views"]) / max(age, .25)) if row.get("views") is not None else None,
        )
        velocity_values.append(normalized)
        entities = detect_entities(row["original_text"])
        actions = event_actions(row["original_text"])
        topics = event_topics(row["original_text"])
        row["entities"] = entities
        row["actions"] = sorted(actions)
        row["topics"] = sorted(topics)
        row["financial_relevance"] = bool(entities or actions or topics)
        snapshot_rate, acceleration_pct, view_delta = _snapshot_acceleration(
            (engagement_snapshots or {}).get(str(row["post_id"]), [])
        )
        row["snapshot_velocity"] = snapshot_rate
        row["acceleration_pct"] = acceleration_pct
        row["view_delta"] = view_delta
        signature_parts = entities[:2] + sorted(actions)[:1] + sorted(topics)[:1]
        signature = "|".join(signature_parts) if len(signature_parts) >= 2 else f"post:{row['post_id']}"
        row["event_signature"] = signature
        if not row["is_repost"]:
            signatures.setdefault(signature, set()).add(row["publisher_group"])
    ordered = sorted(velocity_values)
    for row in scored:
        rank = ordered.index(row["normalized_velocity"]) + 1 if ordered else 1
        percentile = rank / max(1, len(ordered))
        engagement = percentile * 25
        row["early_signal"] = row["age_hours"] < 0.25
        if row["early_signal"]:
            engagement = max(engagement, 12.5)
        recency = 20 if row["age_hours"] <= 2 else 15 if row["age_hours"] <= 6 else 10 if row["age_hours"] <= 12 else 5
        authority = _role_authority(row["account_role"], row["account_priority"])
        groups = len(signatures.get(row["event_signature"], set()))
        cross = 20 if groups >= 3 else 12 if groups == 2 else 0
        relevance = 15 if row["entities"] or row["actions"] else 8 if row["topics"] else 0
        row["x_hot_score"] = min(100, round(recency + authority + engagement + cross + relevance))
    scored.sort(key=lambda row: (row["x_hot_score"], row["created_at"]), reverse=True)
    return scored


def _news_rows(news_rows: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    source_map = {source["key"]: source for source in NEWS_SOURCES}
    output = []
    for row in news_rows:
        published = parse_datetime(row["published_at"])
        if published is None:
            continue
        age = max((now - published).total_seconds() / 3600, 0)
        entities = detect_entities(row["original_title"])
        actions = event_actions(row["original_title"])
        topics = event_topics(row["original_title"])
        if not (entities or actions or topics):
            continue
        importance = source_map.get(row["source_key"], {}).get("importance", 10)
        score = min(100, (30 if age <= 2 else 24 if age <= 6 else 18 if age <= 12 else 12) + importance + (20 if entities or actions else 8))
        publisher_group = source_map.get(row["source_key"], {}).get("publisher_group", row["source_key"])
        output.append({
            "kind": "NEWS", "id": row["id"], "text": row["original_title"],
            "published_at": row["published_at"], "url": row["original_url"],
            "publisher": row["source_name"], "publisher_group": publisher_group,
            "market": row["market"], "is_repost": False, "score": score,
            "entities": entities, "actions": sorted(actions), "topics": sorted(topics),
            "external_urls": [_normalized_url(row["original_url"])],
            "raw": row,
        })
    return output


def _x_rows(
    x_rows: list[dict[str, Any]],
    now: datetime,
    engagement_snapshots: dict[str, list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    output = []
    for row in score_x_posts(x_rows, now, engagement_snapshots):
        if not row["financial_relevance"]:
            continue
        external = json.loads(row.get("external_urls_json") or "[]")
        output.append({
            "kind": "X", "id": row["post_id"], "text": row["original_text"],
            "published_at": row["created_at"], "url": row["original_url"],
            "publisher": f"{row['author_name']} (@{row['author_handle']})",
            "publisher_group": row["publisher_group"], "market": "X",
            "is_repost": bool(row["is_repost"]), "score": row["x_hot_score"],
            "entities": row["entities"], "actions": row["actions"], "topics": row["topics"],
            "external_urls": [_normalized_url(value) for value in external if _normalized_url(value)],
            "raw": row,
        })
    return output


def _same_event(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return decide_event_pair(left, right).label == SAME_EVENT


def _event_categories(entities: list[str], topics: list[str]) -> list[str]:
    categories: list[str] = []
    if any(code.isdigit() for code in entities):
        categories.append("TW")
    if any(not code.isdigit() for code in entities):
        categories.append("US")
    if "半導體與AI" in topics:
        categories.append("AI")
    if "利率與宏觀" in topics:
        categories.append("MACRO")
    return categories or ["OTHER"]


def _possible_impact(entities: list[str], topics: list[str]) -> str:
    tickers = "、".join(entities[:4])
    if "半導體與AI" in topics:
        return f"可能改變 AI 供應鏈與半導體敘事{('，優先核對 ' + tickers) if tickers else ''}；實際訂單與財務影響仍待官方資料確認。"
    if "地緣政治" in topics:
        return "若事件持續，可能影響能源、避險需求與市場風險偏好；需先核對官方通報與事件規模。"
    if "利率與宏觀" in topics:
        return "可能影響利率預期、估值與資金風格；需核對官方數據及市場是否已有一致反應。"
    if "能源與原物料" in topics:
        return "可能影響能源或原物料價格敘事；需核對供給變化是否具規模與持續性。"
    if entities:
        return f"可能影響 {tickers} 的公司敘事或同業比較；尚不能由討論直接推導財務影響。"
    return "可能形成財經內容題材，但與可交易標的的關聯仍需編輯進一步核實。"


def _recommended_angle(entities: list[str], topics: list[str], actions: list[str]) -> str:
    subject = "、".join(ENTITY_NAMES_ZH.get(code, code) for code in entities[:2])
    if "半導體與AI" in topics:
        return f"這則變化真正影響的是誰？從{subject or 'AI 產業鏈'}的訂單、供應鏈與估值三層拆解。"
    if "地緣政治" in topics:
        return "事件本身之外，哪些能源、運輸與避險資產可能先被市場重新定價？"
    if "利率與宏觀" in topics:
        return "把官方數據、利率預期與股市反應分開，判斷市場究竟在交易哪一層。"
    action = ACTION_NAMES_ZH.get(actions[0], "最新動態") if actions else "最新動態"
    return f"{subject or '相關市場'}的{action}是否已有獨立證據，哪些影響仍只是市場推測？"


def _related_stock_relationships(entities: list[str], primary_entities: list[str], text: str) -> list[dict[str, str]]:
    """Only classify tickers explicitly present in Evidence; never add inferred symbols."""
    primary = primary_entities[0] if primary_entities else (entities[0] if entities else None)
    supply_context = any(term in text.lower() for term in ("supply chain", "supplier", "供應鏈", "供应链", "訂單", "订单"))
    comparison_context = any(term in text.lower() for term in ("compare", "versus", " vs ", "比", "同業", "同业"))
    macro_context = any(term in text.lower() for term in ("federal reserve", "interest rate", "inflation", "cpi", "gdp", "央行", "利率", "通膨", "通胀", "經濟", "经济"))
    rows = []
    for ticker in entities:
        if ticker == primary:
            relationship = "DIRECT"
            label = "直接提及"
        elif supply_context:
            relationship = "SUPPLY_CHAIN"
            label = "供應鏈關聯"
        elif comparison_context:
            relationship = "SECTOR"
            label = "同業比較"
        elif macro_context:
            relationship = "MACRO"
            label = "宏觀關聯"
        else:
            relationship = "POSSIBLE"
            label = "可能相關"
        rows.append({
            "ticker": ticker, "name": ENTITY_NAMES_ZH.get(ticker, ticker),
            "relationship": relationship, "relationship_label": label,
        })
    return rows


def build_unified_events(
    news_rows: list[dict[str, Any]],
    x_rows: list[dict[str, Any]],
    *,
    now: datetime,
    engagement_snapshots: dict[str, list[dict[str, Any]]] | None = None,
    translation_adapter: TranslationSummaryAdapter | None = None,
    target_language: str = "zh-tw",
) -> list[dict[str, Any]]:
    translator = translation_adapter or TranslationSummaryAdapter()
    items = _news_rows(news_rows, now) + _x_rows(x_rows, now, engagement_snapshots)
    items.sort(key=lambda item: item["published_at"])
    clusters: list[list[dict[str, Any]]] = []
    for item in items:
        target = next((cluster for cluster in clusters if any(_same_event(item, existing) for existing in cluster)), None)
        if target is None:
            clusters.append([item])
        else:
            target.append(item)
    events: list[dict[str, Any]] = []
    for cluster in clusters:
        cluster.sort(key=lambda item: item["published_at"])
        news = [item for item in cluster if item["kind"] == "NEWS"]
        x_items = [item for item in cluster if item["kind"] == "X"]
        independent_groups = {item["publisher_group"] for item in cluster if not item["is_repost"]}
        x_accounts = {item["raw"]["author_handle"].lower() for item in x_items if not item["is_repost"]}
        news_groups = {item["publisher_group"] for item in news}
        cross_platform = bool(news and x_items)
        primary = max(cluster, key=lambda item: (item["score"], item["published_at"]))
        entities = sorted({entity for item in cluster for entity in item["entities"]})
        actions = sorted({action for item in cluster for action in item["actions"]})
        topics = sorted({topic for item in cluster for topic in item.get("topics", ())})
        substantive: list[dict[str, Any]] = []
        seen_groups: set[str] = set()
        seen_hashes: set[str] = set()
        for item in cluster:
            content_hash = hashlib.sha256(item["text"].encode("utf-8")).hexdigest()
            if item["is_repost"]:
                continue
            if item["publisher_group"] not in seen_groups or content_hash not in seen_hashes:
                substantive.append(item)
                seen_groups.add(item["publisher_group"])
                seen_hashes.add(content_hash)
        event_type = "NEWS_X" if cross_platform else "X" if x_items else "NEWS"
        reasons = [
            f"{len(news_groups)}個新聞發布方",
            f"{len(x_accounts)}個X帳號討論",
            f"{len(independent_groups)}個獨立發布方組",
        ]
        if cross_platform:
            reasons.append("新聞與X在監控範圍內共同出現")
        if primary["kind"] == "X" and primary["raw"].get("early_signal"):
            reasons.append("發布不足15分鐘：早期信號")
        original_language = primary["raw"].get("original_language") if primary["kind"] == "X" else primary["raw"].get("language")
        translation = translator.summarize(
            primary["text"], entities=entities, actions=actions, topics=topics,
            source_language=original_language, target_language=target_language,
        )
        display_title = translation.title_zh
        title_method = {
            "ORIGINAL_CHINESE": "原文中文", "MODEL_TRANSLATED": "AI 翻譯",
            "RULE_FALLBACK": "規則中文摘要", "TRANSLATION_UNAVAILABLE": "規則中文摘要",
        }.get(translation.status, "規則中文摘要")
        summary = (
            f"{translation.summary_zh} 監控範圍內目前有{len(independent_groups)}個獨立發布方，"
            f"包括{len(news_groups)}家新聞來源與{len(x_accounts)}個 X 帳號。"
        )
        accelerations = [
            float(item["raw"]["acceleration_pct"])
            for item in x_items if item["raw"].get("acceleration_pct") is not None
        ]
        acceleration_pct = max(accelerations, key=abs) if accelerations else None
        velocities = [
            item["raw"].get("snapshot_velocity") or item["raw"].get("view_velocity") or item["raw"].get("engagement_velocity")
            for item in x_items
        ]
        velocity_per_hour = max((float(value) for value in velocities if value is not None), default=None)
        first_age = max(0.0, (now - parse_datetime(cluster[0]["published_at"])).total_seconds() / 3600)
        latest_age = max(0.0, (now - parse_datetime((substantive[-1] if substantive else cluster[0])["published_at"])).total_seconds() / 3600)
        if first_age <= 2:
            trend = "NEW"
        elif acceleration_pct is not None and acceleration_pct >= 20:
            trend = "HEATING"
        elif (acceleration_pct is not None and acceleration_pct <= -20) or latest_age >= 6:
            trend = "COOLING"
        else:
            trend = "STEADY"
        freshness_score = 20 if first_age <= 2 else 16 if first_age <= 6 else 10 if first_age <= 12 else 5
        acceleration_score = min(25, round(max(item["score"] for item in cluster) * .25))
        breadth_score = min(15, len(independent_groups) * 4 + (3 if cross_platform else 0))
        evidence_score = 25 if cross_platform else 21 if news else 16 if any(
            _role_authority(item["raw"].get("account_role", ""), item["raw"].get("account_priority", "")) >= 20
            for item in x_items
        ) else 9
        market_response_score = 0
        score = min(100, freshness_score + acceleration_score + breadth_score + evidence_score + market_response_score)
        content_score = min(100, round(score * .72 + evidence_score * .6 + min(10, len(entities) * 3) + (8 if topics else 0)))
        event_id = "evt_" + hashlib.sha256(min(f"{item['kind']}:{item['id']}" for item in cluster).encode("utf-8")).hexdigest()[:16]
        formats = ["快訊"]
        if independent_groups:
            formats.append("觀點帖")
        if entities:
            formats.append("數據圖")
        if score >= 65:
            formats.append("短視頻")
        categories = _event_categories(entities, topics)
        aggregate_item = {
            "text": " ".join(item["text"] for item in cluster),
            "entities": entities,
            "actions": actions,
            "topics": topics,
            "published_at": cluster[0]["published_at"],
            "kind": event_type,
        }
        fingerprint = event_fingerprint(aggregate_item)
        merge_diagnostics = [
            decide_event_pair(primary, item).to_dict()
            for item in cluster if item is not primary
        ]
        related_stocks = _related_stock_relationships(entities, primary.get("entities", []), primary["text"])
        possible_impact = _possible_impact(entities, topics)
        why_it_matters = (
            f"事實：監控池已捕捉到 {len(independent_groups)} 個獨立發布方，包含 {len(news_groups)} 家新聞與 {len(x_accounts)} 個 X 帳號。"
            f"市場解讀：{possible_impact}"
        )
        events.append({
            "event_id": event_id, "type": event_type, "score": score, "heat_score": score,
            "primary": primary, "items": cluster,
            "news_items": news, "x_items": x_items, "news_count": len(news_groups),
            "x_count": len(x_accounts), "independent_count": len(independent_groups),
            "first_seen_at": cluster[0]["published_at"],
            "latest_update_at": (substantive[-1] if substantive else cluster[0])["published_at"],
            "reasons": reasons, "summary_zh": summary, "display_title_zh": display_title,
            "title_method": title_method, "entities": entities, "topics": topics, "actions": actions,
            "fingerprint": fingerprint, "merge_diagnostics": merge_diagnostics,
            "translation_status": translation.status, "translation_method": translation.method,
            "translation_cache_key": translation.cache_key,
            "related_stocks": related_stocks,
            "categories": categories, "category": categories[0], "trend": trend,
            "acceleration_pct": acceleration_pct, "velocity_per_hour": velocity_per_hour,
            "score_dimensions": {
                "freshness": freshness_score, "acceleration": acceleration_score,
                "breadth": breadth_score, "evidence": evidence_score,
                "market_response": market_response_score,
            },
            "evidence_score": evidence_score, "content_score": content_score,
            "content_formats": formats,
            "what_happened": summary,
            "why_watch": "；".join(reasons) + "。",
            "possible_impact": possible_impact, "why_it_matters": why_it_matters,
            "content_angle": _recommended_angle(entities, topics, actions),
            "recommended_angle": _recommended_angle(entities, topics, actions),
            "questions": ["是否已有公司、監管機構或第二個獨立來源確認？", "後續是否出現新的實質資訊，而非普通轉發？"],
        })
    events.sort(key=lambda event: (event["score"], event["latest_update_at"]), reverse=True)
    return events


def cluster_quality_report(
    events: list[dict[str, Any]],
    *,
    raw_news_count: int,
    raw_x_count: int,
) -> dict[str, Any]:
    eligible_count = sum(len(event["items"]) for event in events)
    event_count = len(events)
    return {
        "raw_count": raw_news_count + raw_x_count,
        "eligible_count": eligible_count,
        "event_count": event_count,
        "compression_rate": round(1 - event_count / eligible_count, 4) if eligible_count else 0.0,
        "multi_item_events": sum(len(event["items"]) > 1 for event in events),
        "multi_publisher_events": sum(event["independent_count"] > 1 for event in events),
        "cross_platform_events": sum(event["type"] == "NEWS_X" for event in events),
        "singleton_events": sum(len(event["items"]) == 1 for event in events),
    }


def cluster_diagnostic_report(
    news_rows: list[dict[str, Any]],
    x_rows: list[dict[str, Any]],
    *,
    now: datetime,
    limit: int = 120,
) -> list[dict[str, Any]]:
    items = _news_rows(news_rows, now) + _x_rows(x_rows, now)
    rows = []
    for left, right in itertools.combinations(items, 2):
        decision = decide_event_pair(left, right)
        if not decision.candidate:
            continue
        pair_id = "pair_" + hashlib.sha256(
            "|".join(sorted((f"{left['kind']}:{left['id']}", f"{right['kind']}:{right['id']}"))).encode()
        ).hexdigest()[:14]
        rows.append({
            "event_id": pair_id, "left": left, "right": right,
            "left_fingerprint": event_fingerprint(left),
            "right_fingerprint": event_fingerprint(right),
            "decision": decision.to_dict(),
        })
    rows.sort(key=lambda row: (
        row["decision"]["label"] == SAME_EVENT,
        row["decision"]["similarity"],
    ), reverse=True)
    return rows[:limit]


def attach_market_response(events: list[dict[str, Any]], anomalies: list[dict[str, Any]]) -> None:
    anomaly_by_ticker = {str(row["stock_code"]): row for row in anomalies}
    for event in events:
        matched = [anomaly_by_ticker[code] for code in event["entities"] if code in anomaly_by_ticker]
        if not matched:
            event["market_response"] = []
            continue
        response_score = min(15, max(
            5 + (5 if abs(float(row.get("change_pct") or 0)) >= 2 else 0) + (5 if float(row.get("rvol") or 0) >= 2 else 0)
            for row in matched
        ))
        event["score_dimensions"]["market_response"] = response_score
        event["score"] = event["heat_score"] = min(100, event["score"] + response_score)
        event["content_score"] = min(100, event["content_score"] + round(response_score * .7))
        event["market_response"] = matched
    events.sort(key=lambda event: (event["score"], event["latest_update_at"]), reverse=True)


_CONVERTERS = {"zh-cn": OpenCC("tw2sp.json"), "zh-tw": OpenCC("s2twp.json")}


def localize_zh(value: Any, language: str) -> str:
    text = str(value or "")
    converter = _CONVERTERS.get(language, _CONVERTERS["zh-tw"])
    return converter.convert(text)


def taipei_time(value: Any, language: str = "zh-tw") -> str:
    parsed = parse_datetime(value)
    if parsed is None:
        return localize_zh("時間未知", language)
    return parsed.astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M") + " UTC+8"


def diagnose_yahoo_finance(
    connection: sqlite3.Connection,
    *,
    now: datetime | None = None,
    fetcher: Callable[[str, int], HttpResult] = lambda url, timeout: _http_get(url, timeout),
) -> list[dict[str, Any]]:
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    cutoff = utc_iso(current - timedelta(minutes=15))
    cached = connection.execute(
        """SELECT * FROM ben_endpoint_diagnostics
           WHERE source_key='yahoo_finance' AND attempted_at >= ?
           ORDER BY attempted_at, endpoint_url""", (cutoff,)
    ).fetchall()
    if len(cached) >= 2:
        return [dict(row) for row in cached[-2:]]
    output = []
    for url in YAHOO_FINANCE_ENDPOINTS:
        attempted = utc_iso(current)
        status_code = None
        headers: dict[str, str] = {}
        body = b""
        error_reason = None
        try:
            page = fetcher(url, 25)
            status_code, headers, body = page.status_code, page.headers, page.body
        except (OSError, TimeoutError, urllib.error.URLError) as error:
            error_reason = f"{type(error).__name__}: {error}"
        retry_after = headers.get("Retry-After") or headers.get("retry-after")
        limited_headers = {
            key: value for key, value in headers.items()
            if key.lower() in {"retry-after", "x-rate-limit-limit", "x-rate-limit-remaining", "x-rate-limit-reset", "server", "via", "cache-control"}
        }
        final_status = "SUCCESS" if status_code == 200 else "DEGRADED_RATE_LIMITED" if status_code == 429 else "FAILED"
        content_type = headers.get("Content-Type") or headers.get("content-type")
        row = {
            "id": str(uuid.uuid4()), "source_key": "yahoo_finance", "endpoint_url": url,
            "request_method": "GET", "attempted_at": attempted,
            "finished_at": utc_iso(datetime.now(timezone.utc)), "http_status": status_code,
            "retry_after": retry_after, "rate_limit_headers_json": json.dumps(limited_headers, ensure_ascii=False),
            "content_type": content_type, "attempt_count": 1, "final_status": final_status,
            "error_reason": error_reason or (f"HTTP {status_code}" if status_code not in {200, None} else None),
            "response_excerpt": body[:240].decode("utf-8", errors="replace"),
        }
        with connection:
            connection.execute(
                """INSERT INTO ben_endpoint_diagnostics
                   (id, source_key, endpoint_url, request_method, attempted_at, finished_at,
                    http_status, retry_after, rate_limit_headers_json, content_type,
                    attempt_count, final_status, error_reason, response_excerpt)
                   VALUES (:id,:source_key,:endpoint_url,:request_method,:attempted_at,:finished_at,
                           :http_status,:retry_after,:rate_limit_headers_json,:content_type,
                           :attempt_count,:final_status,:error_reason,:response_excerpt)""", row,
            )
        output.append(row)
    return output
