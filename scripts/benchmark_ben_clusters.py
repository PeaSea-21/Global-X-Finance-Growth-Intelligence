from __future__ import annotations

import argparse
import itertools
import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from global_x_finance.event_clustering import (
    DIFFERENT_EVENT,
    RELATED_BUT_DISTINCT,
    SAME_EVENT,
    decide_event_pair,
)
from global_x_finance.x_intelligence import _news_rows, _x_rows


LABELS = (SAME_EVENT, DIFFERENT_EVENT, RELATED_BUT_DISTINCT)

GOLD_PAIR_SPECS = (
    ("gold-001", SAME_EVENT, "same_event_reprint", "NEWS:3b94b500-f14d-4b9c-81ee-ced277b85430", "NEWS:73ee926c-471d-4aa5-9653-0c4a5ec0ba04", "同一台积电联合征才消息的标题改写。"),
    ("gold-002", SAME_EVENT, "same_event_reprint", "NEWS:f6daa806-fd37-4add-af02-3a963c897f21", "NEWS:00c3b6ff-84ac-4511-b40d-211d364f8ce5", "同一英伟达拟向 SB Energy 投资 30 亿美元的数据中心消息。"),
    ("gold-003", SAME_EVENT, "same_event_reprint", "NEWS:04512e0d-e191-43a0-a0df-c566a0144086", "NEWS:d2eda5c4-3aa5-4e7e-8c01-f4a81e901dac", "同一 Peter Thiel 买入 Vista Energy 约 1% 股份的申报消息。"),
    ("gold-004", SAME_EVENT, "news_x_same_event", "NEWS:04512e0d-e191-43a0-a0df-c566a0144086", "X:2088761442203775449", "新闻标题与 Bloomberg X 帖均指向 Peter Thiel/Vista 持股披露。"),
    ("gold-005", SAME_EVENT, "news_x_same_event", "NEWS:d2eda5c4-3aa5-4e7e-8c01-f4a81e901dac", "X:2088761442203775449", "新闻标题与 Bloomberg X 帖均指向 Peter Thiel/Vista 持股披露。"),
    ("gold-006", SAME_EVENT, "news_x_commentary", "NEWS:dfe8bbd1-e262-4817-836b-383a9cf06abc", "X:2088895208255873103", "新闻与中文 X 评论都围绕英伟达 Q2 披露的 SpaceX 等持股；X 含额外解读。"),
    ("gold-007", RELATED_BUT_DISTINCT, "same_product_different_milestone", "X:2088891548507492646", "X:2088876951041941792", "同为 Qwen3.8-27B，但分别是笔电运行展示与 Hugging Face 榜首里程碑。"),
    ("gold-008", RELATED_BUT_DISTINCT, "same_series_different_story", "NEWS:31daf013-6fe7-4cb6-9d67-170d61deb8dc", "NEWS:d974caab-fbea-4bc1-97ad-27cbc9b8ed71", "同一手机晶片专题系列，但一篇讲存储短缺，一篇讲 2nm/WMCM 与涨价。"),
    ("gold-009", RELATED_BUT_DISTINCT, "same_company_different_investment", "NEWS:98089e17-42e5-40c8-90f0-d732262f39a0", "NEWS:f6daa806-fd37-4add-af02-3a963c897f21", "都涉及英伟达投资，但 5000 亿美元动员分析不等于 SB Energy 30 亿美元洽谈。"),
    ("gold-010", RELATED_BUT_DISTINCT, "same_company_different_target", "NEWS:f6daa806-fd37-4add-af02-3a963c897f21", "NEWS:dfe8bbd1-e262-4817-836b-383a9cf06abc", "英伟达投资动作相近，但目标分别是 SB Energy 与 SpaceX。"),
    ("gold-011", RELATED_BUT_DISTINCT, "same_company_different_target", "NEWS:98089e17-42e5-40c8-90f0-d732262f39a0", "NEWS:dfe8bbd1-e262-4817-836b-383a9cf06abc", "同属英伟达资本叙事，但金额、对象与事实阶段不同。"),
    ("gold-012", RELATED_BUT_DISTINCT, "same_company_different_event", "NEWS:ad1d0192-6f95-49ce-993f-2925f43d9996", "NEWS:86fca6f5-f6c0-4825-9f7a-68e77fffeb2b", "都涉及 Alphabet，但一条是伯克希尔增持，一条是 AI 战略分析。"),
    ("gold-013", RELATED_BUT_DISTINCT, "same_company_market_commentary", "NEWS:466bd475-8d8b-435e-ac25-6a2d6822fc9e", "NEWS:7cc370ac-4b3e-4c42-9e2b-772486390f43", "都讨论台积电估值/股价，但不是同一篇事实披露。"),
    ("gold-014", RELATED_BUT_DISTINCT, "same_theme_different_story", "NEWS:e1f6d96e-4c78-4324-ae41-020e4b585b80", "NEWS:20286cb6-a9fc-487e-960c-250bcc69cf6f", "都谈台湾 AI 交易主题，但一个比较台积电与美股，一个讨论台股与通胀。"),
    ("gold-015", RELATED_BUT_DISTINCT, "rolling_digest", "X:2088797936368996616", "X:2088775288347914267", "Bloomberg News Now 的滚动音频摘要有共同主线，但属于不同更新时间的节目对象。"),
    ("gold-016", RELATED_BUT_DISTINCT, "rolling_digest", "X:2088784091231433013", "X:2088774043549729216", "两条滚动音频摘要都含美国对伊朗施压与飓风，但 URL 和节目版本不同。"),
    ("gold-017", RELATED_BUT_DISTINCT, "same_product_different_feature", "X:2088624755913982302", "X:2088598175074377849", "同属 Claude 产品爆料，但分别是模型比较界面与桌面浏览器功能。"),
    ("gold-018", RELATED_BUT_DISTINCT, "same_company_results_vs_policy", "NEWS:e18e69df-7890-4c31-a325-78daee60343a", "X:2088758816376807762", "都涉及 Anthropic，但一条是营收报道，一条是监管立场长文。"),
    ("gold-019", RELATED_BUT_DISTINCT, "same_company_supply_chain", "NEWS:3b94b500-f14d-4b9c-81ee-ced277b85430", "NEWS:e6240731-f554-49ff-ad62-4a664c9a7817", "都提台积电供应链，但联合征才与 iPhone/DRAM 到货是两个事件。"),
    ("gold-020", RELATED_BUT_DISTINCT, "same_asset_different_story", "NEWS:dfe8bbd1-e262-4817-836b-383a9cf06abc", "NEWS:b90d0852-a359-47ed-a601-f6f4c662e819", "都提 SpaceX/AI，但一条是英伟达持股披露，一条是 SpaceX AI 题材分析。"),
    ("gold-021", RELATED_BUT_DISTINCT, "same_company_policy_vs_people", "X:2088919317257556359", "NEWS:40bcef62-606d-4a46-835f-fbe37d6d9733", "都涉及 OpenAI，但广告隐私政策更新与 IPO 前人才流失是不同事件。"),
    ("gold-022", RELATED_BUT_DISTINCT, "same_sector_market_commentary", "NEWS:6f5951af-9856-4c8c-9a54-63a34ad1ad9e", "NEWS:35822011-2e10-43e9-9dc1-678d2c4121a6", "都讨论台股 AI 供应链行情，但属于不同评论内容。"),
    ("gold-023", RELATED_BUT_DISTINCT, "same_company_transaction_vs_valuation", "NEWS:5700ea40-1492-4ab0-9461-bf80ebc2bf66", "NEWS:7cc370ac-4b3e-4c42-9e2b-772486390f43", "软银减持台积电 ADR 与台积电估值评论相关但不是同一事件。"),
    ("gold-024", RELATED_BUT_DISTINCT, "same_company_macro_vs_deal", "NEWS:22b625dc-a729-471e-a7dd-4bc2a294404e", "NEWS:f6daa806-fd37-4add-af02-3a963c897f21", "都提英伟达与 AI 交易，但宏观周评和 SB Energy 洽谈不同。"),
    ("gold-025", RELATED_BUT_DISTINCT, "same_industry_different_company", "NEWS:c9ab090d-e90b-4d0d-8690-37e3a893eea3", "NEWS:a2858aaf-866f-4a5d-9f90-2eb149cf42a6", "同属汽车软件主题，但行业寿命问题与 Tesla/Rivian 驾驶体验不同。"),
    ("gold-026", DIFFERENT_EVENT, "same_action_different_geography", "X:2088940104526000493", "X:2088916194501722351", "比利时野火与莫斯科无人机导致仓库起火，地点、主体和原因均不同。"),
    ("gold-027", DIFFERENT_EVENT, "same_action_different_company", "NEWS:e18e69df-7890-4c31-a325-78daee60343a", "NEWS:e2944e3d-7ca1-45af-8f48-e9eb81e41648", "Anthropic 季度营收与台湾服务器导轨公司月度获利不同。"),
    ("gold-028", DIFFERENT_EVENT, "keyword_collision", "X:2088919317257556359", "X:2088880984158613804", "OpenAI 广告隐私政策与哥伦比亚地震后的关税请求无关。"),
    ("gold-029", DIFFERENT_EVENT, "same_action_different_target", "NEWS:ad1d0192-6f95-49ce-993f-2925f43d9996", "NEWS:04512e0d-e191-43a0-a0df-c566a0144086", "伯克希尔增持 Alphabet 与 Peter Thiel 买 Vista 股份是不同交易。"),
    ("gold-030", DIFFERENT_EVENT, "same_theme_different_event", "X:2088879468978778194", "X:2088823148649009498", "印度 AI 电网讨论与尼日尔炼化项目仅同属能源大类。"),
    ("gold-031", DIFFERENT_EVENT, "same_source_unrelated", "X:2088922484741472349", "X:2088940104526000493", "马来西亚内阁政治与比利时野火无关。"),
    ("gold-032", DIFFERENT_EVENT, "same_source_unrelated", "X:2088951430719717808", "X:2088868435228791292", "瑞典核武讨论与香港机场客流无关。"),
    ("gold-033", DIFFERENT_EVENT, "same_source_unrelated", "X:2088891056511242254", "X:2088729985074754003", "印度 LPG 增产与秘鲁经济受渔农业拖累无关。"),
    ("gold-034", DIFFERENT_EVENT, "same_theme_different_event", "NEWS:16cbffd1-4a4f-4f00-9126-b5d37decbfcc", "NEWS:6d925e9f-0c38-42fc-b626-e814396956c7", "美国战略石油储备与铜交易观察关税没有共同事件。"),
    ("gold-035", DIFFERENT_EVENT, "same_company_collision", "NEWS:1e0ca3d6-8106-4260-84f6-e2cbf530fead", "NEWS:3b94b500-f14d-4b9c-81ee-ced277b85430", "台湾产业风险评论与台积电联合征才不是同一事件。"),
    ("gold-036", DIFFERENT_EVENT, "same_market_different_event", "NEWS:18fea897-5681-416f-818e-9b12ad8a1044", "NEWS:644eeeb8-cff0-456f-bf0a-225a86ce9bb1", "台股年度涨幅排名与 TISA/0050 扣款数据是不同事件。"),
    ("gold-037", DIFFERENT_EVENT, "same_theme_different_event", "NEWS:4aafa167-efd2-4fa4-bbcb-bc2557ad100b", "NEWS:131b7861-bcdd-4225-bfba-275b9410531a", "加密公司银行牌照与预测市场监管审查并非同一事件。"),
    ("gold-038", DIFFERENT_EVENT, "same_company_different_event", "NEWS:8987e6f7-d0c5-4160-95cf-4cbbda935e93", "NEWS:b939dcc0-e5b2-438a-b80a-82c98b69d0e3", "鸿海法说后股价与另一家大厂订单评论不是同一事件。"),
    ("gold-039", DIFFERENT_EVENT, "same_ai_theme_unrelated", "X:2088701564881891831", "X:2088670774299099214", "Codex 视频编辑用例与 Gemini Notebook 查询 Drive 功能无关。"),
    ("gold-040", DIFFERENT_EVENT, "same_ai_theme_unrelated", "X:2088622675606561165", "X:2088567338329067921", "GLM/ZCode token 活动与 Gemini 水印设置无关。"),
    ("gold-041", DIFFERENT_EVENT, "same_country_unrelated", "X:2088951408204623960", "X:2088943856503198163", "星宇 A350 彩绘客机与工研院数字疗法无共同事件。"),
    ("gold-042", DIFFERENT_EVENT, "same_country_unrelated", "X:2088928756618653934", "X:2088581468562002326", "台湾个人所得数据与中油油价维持不变无共同事件。"),
    ("gold-043", DIFFERENT_EVENT, "same_source_unrelated", "X:2088824358718325072", "X:2088855817436991631", "澳洲枪枝回购与中国新能源设备回收规则无关。"),
    ("gold-044", DIFFERENT_EVENT, "same_market_different_event", "NEWS:eef00e5d-9f18-480a-8f2a-1824d90ffd13", "NEWS:caf3baff-6323-4ccc-89f9-23f242b02a37", "标普成分表现分化与台湾经济警讯评论不是同一事件。"),
    ("gold-045", DIFFERENT_EVENT, "same_geopolitics_unrelated", "NEWS:2583e183-5fdd-43c1-b4ed-29ac5b5c1f86", "NEWS:6f9fcea7-d38d-42c2-99bf-c1d5f3b2fc03", "霍尔木兹海峡船只遇袭与俄罗斯经济结构问题不是同一事件。"),
)


def load_items(database_path: Path, hours: int) -> list[dict[str, Any]]:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=hours)).isoformat()
    try:
        news = [dict(row) for row in connection.execute(
            "SELECT * FROM ben_news_items WHERE published_at >= ? ORDER BY published_at DESC", (cutoff,)
        )]
        x_rows = [dict(row) for row in connection.execute(
            """SELECT posts.*, accounts.market_scope, accounts.impact_path
               FROM ben_x_posts posts JOIN ben_x_accounts accounts ON accounts.id=posts.account_id
               WHERE posts.created_at >= ? ORDER BY posts.created_at DESC""", (cutoff,)
        )]
    finally:
        connection.close()
    return _news_rows(news, now) + _x_rows(x_rows, now)


def print_candidates(database_path: Path, hours: int, limit: int, system_label: str | None = None) -> None:
    items = load_items(database_path, hours)
    rows = []
    for left, right in itertools.combinations(items, 2):
        decision = decide_event_pair(left, right)
        if decision.candidate:
            rank = (
                decision.similarity
                + 0.25 * bool(decision.common_entities)
                + 0.20 * bool(decision.common_actions)
                + 0.15 * bool(decision.common_targets)
                + 0.10 * bool(decision.common_topics)
            )
            rows.append((rank, decision, left, right))
    if system_label:
        rows = [row for row in rows if row[1].label == system_label]
    rows.sort(key=lambda row: row[0], reverse=True)
    print(json.dumps({"hours": hours, "eligible_items": len(items), "candidate_pairs": len(rows)}, ensure_ascii=False))
    for index, (rank, decision, left, right) in enumerate(rows[:limit], 1):
        print(
            f"\nPAIR {index:03d} rank={rank:.3f} system={decision.label} "
            f"sim={decision.similarity:.3f} dt={decision.time_delta_hours} "
            f"E={list(decision.common_entities)} A={list(decision.common_actions)} "
            f"N={list(decision.common_numbers)} T={list(decision.common_topics)}"
        )
        print(f"L {left['kind']}:{left['id']} [{left['publisher_group']}] {left['published_at']}\n  {left['text']}")
        print(f"R {right['kind']}:{right['id']} [{right['publisher_group']}] {right['published_at']}\n  {right['text']}")
        print(f"WHY {decision.merge_reason or decision.reject_reason}")


def print_items(database_path: Path, hours: int) -> None:
    items = sorted(load_items(database_path, hours), key=lambda item: item["published_at"], reverse=True)
    print(json.dumps({"hours": hours, "eligible_items": len(items)}, ensure_ascii=False))
    for item in items:
        compact = " ".join(str(item["text"]).split())
        print(f"{item['kind']}:{item['id']} [{item['publisher_group']}] {item['published_at']} | {compact}")


def build_gold(database_path: Path, output_path: Path, hours: int) -> None:
    items = load_items(database_path, hours)
    item_map = {f"{item['kind']}:{item['id']}": item for item in items}
    missing = sorted({key for spec in GOLD_PAIR_SPECS for key in (spec[3], spec[4]) if key not in item_map})
    if missing:
        raise ValueError("Gold source Evidence missing: " + ", ".join(missing))

    def snapshot(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"], "kind": item["kind"], "text": item["text"],
            "published_at": item["published_at"], "url": item["url"],
            "publisher": item["publisher"], "publisher_group": item["publisher_group"],
            "is_repost": bool(item["is_repost"]), "entities": item["entities"],
            "actions": item["actions"], "topics": item["topics"],
            "external_urls": item["external_urls"],
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for sample_id, label, case_type, left_key, right_key, rationale in GOLD_PAIR_SPECS:
            row = {
                "id": sample_id, "label": label, "case_type": case_type,
                "rationale": rationale, "left": snapshot(item_map[left_key]),
                "right": snapshot(item_map[right_key]),
            }
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(json.dumps({"output": str(output_path), "samples": len(GOLD_PAIR_SPECS)}, ensure_ascii=False))


def load_gold(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                row = json.loads(line)
                if row.get("label") not in LABELS:
                    raise ValueError(f"{path}:{line_number}: unsupported label {row.get('label')}")
                rows.append(row)
    return rows


def benchmark(path: Path) -> dict[str, Any]:
    rows = load_gold(path)
    confusion = Counter()
    errors = []
    for row in rows:
        decision = decide_event_pair(row["left"], row["right"])
        gold, predicted = row["label"], decision.label
        confusion[(gold, predicted)] += 1
        if gold != predicted:
            errors.append({
                "id": row["id"], "gold": gold, "predicted": predicted,
                "case_type": row.get("case_type"), "rationale": row.get("rationale"),
                "decision": decision.to_dict(), "left": row["left"], "right": row["right"],
            })
    tp = confusion[(SAME_EVENT, SAME_EVENT)]
    fp = sum(confusion[(gold, SAME_EVENT)] for gold in LABELS if gold != SAME_EVENT)
    fn = sum(confusion[(SAME_EVENT, predicted)] for predicted in LABELS if predicted != SAME_EVENT)
    tn = len(rows) - tp - fp - fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    label_accuracy = {
        label: sum(count for (gold, predicted), count in confusion.items() if gold == label and predicted == label)
        / max(1, sum(count for (gold, _), count in confusion.items() if gold == label))
        for label in LABELS
    }
    return {
        "gold_samples": len(rows), "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4),
        "same_accuracy": round(label_accuracy[SAME_EVENT], 4),
        "different_accuracy": round(label_accuracy[DIFFERENT_EVENT], 4),
        "related_accuracy": round(label_accuracy[RELATED_BUT_DISTINCT], 4),
        "confusion": {f"{gold}->{predicted}": count for (gold, predicted), count in sorted(confusion.items())},
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="BEN Radar P04 clustering benchmark")
    subparsers = parser.add_subparsers(dest="command", required=True)
    candidates = subparsers.add_parser("candidates")
    candidates.add_argument("--db", type=Path, default=Path("data/taiwan-demo.db"))
    candidates.add_argument("--hours", type=int, default=72)
    candidates.add_argument("--limit", type=int, default=100)
    candidates.add_argument("--system-label", choices=LABELS)
    run = subparsers.add_parser("run")
    run.add_argument("--gold", type=Path, default=Path("research/ben_radar_p04/event_cluster_gold.jsonl"))
    run.add_argument("--json", action="store_true")
    items = subparsers.add_parser("items")
    items.add_argument("--db", type=Path, default=Path("data/taiwan-demo.db"))
    items.add_argument("--hours", type=int, default=168)
    gold = subparsers.add_parser("build-gold")
    gold.add_argument("--db", type=Path, default=Path("data/taiwan-demo.db"))
    gold.add_argument("--output", type=Path, default=Path("research/ben_radar_p04/event_cluster_gold.jsonl"))
    gold.add_argument("--hours", type=int, default=168)
    args = parser.parse_args()
    if args.command == "candidates":
        print_candidates(args.db, args.hours, args.limit, args.system_label)
    elif args.command == "items":
        print_items(args.db, args.hours)
    elif args.command == "build-gold":
        build_gold(args.db, args.output, args.hours)
    else:
        result = benchmark(args.gold)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
