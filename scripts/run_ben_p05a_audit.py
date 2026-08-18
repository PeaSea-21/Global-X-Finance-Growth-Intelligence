from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from global_x_finance.ben_radar import compute_anomalies, detect_entities  # noqa: E402
from global_x_finance.pipeline_trace import build_news_pipeline_trace  # noqa: E402
from global_x_finance.radar_analytics import select_snapshot_events, source_concentration  # noqa: E402
from global_x_finance.realtime_radar import parse_datetime  # noqa: E402
from global_x_finance.stock_signals import build_stock_detail, build_stock_signals  # noqa: E402
from global_x_finance.x_intelligence import (  # noqa: E402
    attach_market_response,
    build_unified_events,
    cluster_quality_report,
    event_actions,
    event_topics,
    filter_time_window,
)


TRACE_FIELDS = (
    "content_id", "source", "source_type", "source_item_id", "url", "published_at",
    "fetch_status", "normalize_status", "finance_gate_status", "entity_status",
    "ticker_mapping_status", "event_assignment_status", "ranking_status", "snapshot_status",
    "drop_stage", "drop_reason", "event_id", "related_tickers",
)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    output = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    output.extend("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |" for row in rows)
    return "\n".join(output)


def load_rows(connection: sqlite3.Connection) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    news = [dict(row) for row in connection.execute("SELECT * FROM ben_news_items ORDER BY published_at DESC")]
    x_rows = [dict(row) for row in connection.execute(
        """SELECT posts.*, accounts.market_scope, accounts.impact_path
           FROM ben_x_posts posts JOIN ben_x_accounts accounts ON accounts.id=posts.account_id
           ORDER BY posts.created_at DESC"""
    )]
    return news, x_rows


def snapshots(connection: sqlite3.Connection, cutoff: str) -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = {}
    for row in connection.execute(
        "SELECT * FROM ben_x_engagement_snapshots WHERE fetched_at>=? ORDER BY fetched_at", (cutoff,)
    ):
        output.setdefault(str(row["post_id"]), []).append(dict(row))
    return output


def source_integration(news: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for source_key in ("yahoo_tw", "cnbc", "investing"):
        candidates = [row for row in news if row["source_key"] == source_key]
        sample = next((
            row for row in candidates
            if parse_datetime(row.get("published_at"))
            and (detect_entities(row["original_title"]) or event_actions(row["original_title"]) or event_topics(row["original_title"]))
        ), None)
        if sample is None:
            results.append({"source": source_key, "status": "NO_ELIGIBLE_REAL_SAMPLE", "content_id": ""})
            continue
        as_of = parse_datetime(sample["published_at"]) + timedelta(minutes=10)
        events = build_unified_events([sample], [], now=as_of)
        results.append({
            "source": source_key,
            "status": "PASS" if events and events[0]["news_items"] else "FAIL",
            "content_id": sample["id"],
            "published_at": sample["published_at"],
            "audit_as_of": as_of.isoformat(),
            "event_id": events[0]["event_id"] if events else "",
            "title": sample["original_title"],
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(ROOT / "data" / "taiwan-demo.db"))
    parser.add_argument("--output", default=str(ROOT / "research" / "ben_radar_p05a"))
    args = parser.parse_args()
    output = Path(args.output)
    deliverables = ROOT / "deliverables"
    now = datetime.now(timezone.utc)

    connection = sqlite3.connect(args.db)
    connection.row_factory = sqlite3.Row
    news, x_rows = load_rows(connection)
    news_24 = filter_time_window(news, now=now, hours=24, field="published_at")
    x_24 = filter_time_window(x_rows, now=now, hours=24, field="created_at")
    engagement = snapshots(connection, (now - timedelta(hours=24)).isoformat())
    events = build_unified_events(news_24, x_24, now=now, engagement_snapshots=engagement)
    anomalies, pool_count, history_valid_count = compute_anomalies(connection, news_24)
    attach_market_response(events, anomalies)
    selected = select_snapshot_events(events, 16)
    selected_ids = {event["event_id"] for event in selected}
    traces = build_news_pipeline_trace(news, events, now=now, snapshot_event_ids=selected_ids)
    signals = build_stock_signals(connection, events)
    concentration_all = source_concentration(events)
    concentration_snapshot = source_concentration(selected)
    integration = source_integration(news)

    all_events = build_unified_events(news, x_rows, now=now, engagement_snapshots=engagement)
    natural_overlap = [event for event in all_events if event["type"] == "NEWS_X"]
    overlap_status = "NATURAL_OVERLAP_FOUND" if natural_overlap else "NO_NATURAL_OVERLAP_FOUND"
    quality = cluster_quality_report(events, raw_news_count=len(news_24), raw_x_count=len(x_24))
    drop_counts = Counter(row["drop_reason"] or "INCLUDED" for row in traces)
    source_counts = Counter(row["source"] for row in traces)
    trace_source_drop = Counter((row["source"], row["drop_reason"] or "INCLUDED") for row in traces)

    output.mkdir(parents=True, exist_ok=True)
    with (output / "news_pipeline_trace.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRACE_FIELDS)
        writer.writeheader()
        writer.writerows(traces)

    write_json(output / "hot_stocks.json", signals[:10])
    write_json(output / "abnormal_stocks.json", [row for row in signals if row["abnormal_flags"]])
    events_by_id = {event["event_id"]: event for event in events}
    if signals:
        write_json(output / f"stock_detail_{signals[0]['ticker']}.json", build_stock_detail(signals[0], events_by_id))
    source_coverage = {
        "generated_at": now.isoformat(),
        "window_hours": 24,
        "raw_news_total": len(news),
        "raw_x_total": len(x_rows),
        "news_in_window": len(news_24),
        "x_in_window": len(x_24),
        "events_in_window": len(events),
        "news_events": sum(bool(event["news_items"]) for event in events),
        "x_events": sum(bool(event["x_items"]) for event in events),
        "cross_platform_events": sum(event["type"] == "NEWS_X" for event in events),
        "stock_linked_events": sum(bool(event["entities"]) for event in events),
        "snapshot": concentration_snapshot,
        "full_window": concentration_all,
        "natural_overlap_audit": overlap_status,
    }
    write_json(output / "source_coverage.json", source_coverage)
    write_json(output / "integration_results.json", integration)

    baseline = f"""# BEN Radar P05-A baseline

- Frozen at: `{now.isoformat()}`
- Database: `{Path(args.db).resolve()}`
- Persisted news: **{len(news)}** ({', '.join(f'{key} {value}' for key, value in source_counts.items())})
- Persisted X posts: **{len(x_rows)}**
- Current 24h input: news **{len(news_24)}**, X **{len(x_24)}**
- Current unified events: **{len(events)}**; public selection: **{len(selected)}**
- Stock history pool: **{pool_count}**; >=21 sessions on official date: **{history_valid_count}**
- P04 cluster benchmark remains the pre-existing benchmark; P05-A does not change its gold labels.

## Pre-fix public snapshot (frozen evidence)

The prior public JSON contained 16 events / 18 Evidence, with 0 news Evidence, 18 X Evidence,
3 publisher groups and 1 ticker-linked event. This is retained as the before-state and is not
recomputed after the fix.
"""
    write_text(output / "00_baseline.md", baseline)

    architecture = """# Pipeline architecture

```text
RSS/X fetch -> immutable Evidence -> source adapter -> finance gate
            -> entity + market-qualified security mapping
            -> stable event assignment -> opportunity ranking
            -> diversity-aware read-only snapshot
TWSE daily OHLCV -> prior-20-session baseline -> StockSignal
StockSignal <-> event IDs <-> Evidence links -> content opportunity
```

The public exporter now reads event Evidence, stock signals, source coverage and snapshot metadata.
No paid API, minute bar, model-generated draft or server write endpoint is introduced.
"""
    write_text(output / "01_pipeline_architecture.md", architecture)

    root_rows = [
        ["A fetch", "Not root cause", f"80 persisted news rows"],
        ["B persist", "Not root cause", "Every audited item has a ben_news_items row"],
        ["C normalize", "Not primary", "Required title/time/URL are present for stored rows"],
        ["D finance gate", "Secondary", f"Non-finance count: {drop_counts.get('NON_FINANCE', 0)}"],
        ["E entity", "Coverage limitation", "Entity absence does not automatically reject topic/action matches"],
        ["F ranking", "Confirmed", f"Current eligible news excluded by snapshot: {drop_counts.get('SNAPSHOT_LIMIT', 0)}"],
        ["G snapshot limit", "Confirmed", "Route and exporter previously sliced the same Top 16"],
        ["H time window", "Primary", f"Outside 24h: {drop_counts.get('OUTSIDE_TIME_WINDOW', 0)} / {len(news)}"],
        ["I source filter", "Not root cause", "Default source=all"],
        ["J public builder", "Confirmed", "Old exporter only serialized template-selected events"],
        ["K duplicate pipeline", "Confirmed design debt", "Public payload omitted StockSignal/source coverage despite DB availability"],
    ]
    news_audit = f"""# News pipeline audit

All **{len(traces)}** persisted news rows are present in `news_pipeline_trace.csv`.

{md_table(["Stage", "Finding", "Evidence"], root_rows)}

## Terminal outcomes

{md_table(["drop_reason", "count"], [[key, value] for key, value in drop_counts.most_common()])}

## Source x terminal outcome

{md_table(["source", "outcome", "count"], [[key[0], key[1], value] for key, value in sorted(trace_source_drop.items())])}

Old news is validated at its own historical audit time in integration tests; it is never relabeled as current.
"""
    write_text(output / "02_news_pipeline_audit.md", news_audit)

    concentration_doc = f"""# Source concentration audit

## Current full 24h event set

```json
{json.dumps(concentration_all, ensure_ascii=False, indent=2)}
```

## Selected public snapshot

```json
{json.dumps(concentration_snapshot, ensure_ascii=False, indent=2)}
```

Warning policy: Top 1 > 50%, Top 3 > 80%, or fewer than 5 publishers. These thresholds flag
editorial fragility; they do not delete Bloomberg or force low-quality sources into the feed.
"""
    write_text(output / "03_source_concentration_audit.md", concentration_doc)

    signal_doc = f"""# Stock signal model

- Universe actually available in `ben_stock_history`: **{pool_count}** securities.
- Valid prior-20-session baselines on the latest official date: **{history_valid_count}**.
- Produced signals: **{len(signals)}**; abnormal: **{sum(bool(row['abnormal_flags']) for row in signals)}**.
- Market IDs are qualified (`TWSE:2330` != `NYSE:TSM`).
- Relationships are carried from event Evidence (`DIRECT`, `SUPPLY_CHAIN`, `SECTOR`, `MACRO`, `POSSIBLE`).
- Missing price/turnover/baseline fields remain null and lower `data_quality`; they are never converted to zero.

Outputs: `hot_stocks.json`, `abnormal_stocks.json`, and one `stock_detail_*.json` payload.
"""
    write_text(output / "04_stock_signal_model.md", signal_doc)

    score_doc = """# HotScore method

`HotScore = price(25) + volume(25) + catalyst(30) + publisher breadth(20)`.

- Price uses absolute latest-session change versus the immediately prior close.
- Volume uses latest volume divided by the median of the prior 20 completed sessions.
- Catalyst counts linked news/X Evidence and linked events.
- Breadth counts independent publisher groups; reposts do not add breadth.
- Every component is capped and the total is capped at 100.
- No future row can enter the baseline: only rows before the current completed session are used.
- This score ranks editorial investigation opportunities; it is not a buy/sell score.
"""
    write_text(output / "05_hot_score_method.md", score_doc)

    integration_doc = f"""# Integration test

## Real stored news samples

{md_table(["source", "status", "content_id", "audit_as_of", "event_id"], [[row['source'], row['status'], row.get('content_id',''), row.get('audit_as_of',''), row.get('event_id','')] for row in integration])}

- Current real X rows in 24h: **{len(x_24)}**.
- Unified 24h quality: `{json.dumps(quality, ensure_ascii=False)}`.
- Natural news/X overlap audit across stored corpus: **{overlap_status}**.
- If no overlap exists, no synthetic cross-platform event is promoted to production output.
- Browser and full project checks are recorded separately after this generator completes.
"""
    write_text(output / "06_integration_test.md", integration_doc)

    data_report = f"""# BEN RADAR P05-A 数据链路审计

## 结论

80 条新闻并未丢失。当前公开页缺新闻的主因是 **24 小时时间窗（{drop_counts.get('OUTSIDE_TIME_WINDOW', 0)}/{len(news)}）**，
其次是旧版 Top 16 + 静态导出双重截断（当前被快照截断 {drop_counts.get('SNAPSHOT_LIMIT', 0)} 条）。
本次已增加逐条 Trace、结构化 drop_reason、来源集中度元数据和多源边际惩罚选择；没有把旧闻伪装成实时新闻。

## 修复前后

| 项目 | 修复前 | P05-A 后 |
|---|---:|---:|
| 新闻逐条可追踪 | 0/80 | {len(traces)}/{len(news)} |
| 公网 JSON 股票信号 | 0 | {min(10, len(signals))} |
| 来源集中度状态 | 无 | {concentration_snapshot['status']} |
| 公开构建数据路径 | 模板 Top 16 | 事件 + 股票信号 + source coverage |

最终 READY 状态需等待测试、静态构建与浏览器验收完成后确认。
"""
    write_text(deliverables / "BEN_RADAR_P05A_数据链路审计.md", data_report)

    signal_report = f"""# BEN RADAR P05-A 股票信号层验证报告

## 当前产出

- 监测池：{pool_count}；有效 21 日历史：{history_valid_count}。
- StockSignal：{len(signals)}；Top 10 已写入 JSON；异常股票：{sum(bool(row['abnormal_flags']) for row in signals)}。
- 事件关联股票：{sum(bool(event.get('entities')) for event in events)} / {len(events)} 个当前事件。
- 热度分完全规则化、可解释、无未来数据泄漏。
- 数据质量为 COMPLETE / PARTIAL / UNAVAILABLE；缺失值保持 null。

## 当前状态

`BEN RADAR P05-A VALIDATION PENDING`

尚需完成全套测试、静态站构建、浏览器回归及项目记忆检查，才能升级为 READY。
"""
    write_text(deliverables / "BEN_RADAR_P05A_股票信号层验证报告.md", signal_report)
    connection.close()
    print(json.dumps({
        "trace_rows": len(traces), "drop_counts": dict(drop_counts), "signals": len(signals),
        "abnormal": sum(bool(row["abnormal_flags"]) for row in signals),
        "selected_news_events": sum(bool(event["news_items"]) for event in selected),
        "snapshot_concentration": concentration_snapshot,
        "integration": integration, "natural_overlap": overlap_status,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

