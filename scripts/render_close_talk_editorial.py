from __future__ import annotations

import argparse
import json
from pathlib import Path


def render(payload: dict) -> str:
    lines = [
        f"# {payload['channel_name']}｜{payload['market_session_date']}",
        "",
        f"資料截至：{payload['data_as_of']}  ",
        f"狀態：{payload['status']}  ",
        "",
        "> 這是 FactPack 驅動的原創初稿，供人工核稿；YouTube/X 只作結構或注意度參考，不作當日財經事實。",
        "",
        "## 今日已知缺口",
        "",
    ]
    lines.extend(f"- {item}" for item in payload.get("known_data_gaps", []))
    for angle in payload.get("angles", []):
        rank = angle["rank"]
        lines.extend(
            [
                "",
                f"## {rank}. {angle['episode_question']}",
                "",
                "### 標題候選",
                "",
            ]
        )
        lines.extend(f"{index}. {title}" for index, title in enumerate(angle["title_options"], 1))
        lines.extend(
            [
                "",
                f"**為什麼今天：** {angle['why_today']}",
                "",
                f"**為什麼適合收盤夜話：** {angle['why_this_channel']}",
                "",
                "### 已核實事實",
                "",
            ]
        )
        for fact in angle.get("confirmed_facts", []):
            lines.append(f"- {fact['text']}（證據：{', '.join(fact['evidence_ids'])}）")
        lines.extend(
            [
                "",
                f"**判讀：** {angle['interpretation']}",
                "",
                "### 尚未確認",
                "",
            ]
        )
        lines.extend(f"- {item}" for item in angle.get("unknowns", []))
        lines.extend(["", "### 明日檢查點", ""])
        for checkpoint in angle.get("tomorrow_checkpoints", []):
            lines.append(
                f"- **{checkpoint['metric']}**：偏多條件：{checkpoint['positive_if']}；"
                f"需留意：{checkpoint['caution_if']}"
            )
        lines.extend(["", "### 排名理由", ""])
        lines.extend(f"- {item}" for item in angle.get("ranking_reasons", []))
        lines.extend(["", "### 來源", ""])
        for card in angle.get("source_cards", []):
            lines.append(
                f"- [{card['source_name']}｜{card['title']}]({card['url']}) "
                f"`{card['epistemic_status']}` · {card['published_at']} · `{card['evidence_id']}`"
            )
        if angle.get("script"):
            script_text = angle["script"]["full_text"]
            character_count = angle["script"].get("character_count") or len(
                "".join(script_text.split())
            )
            lines.extend([
                "",
                "### 完整文稿（人工核稿版）",
                "",
                f"**正文字符数：{character_count:,}（不含空白）**",
                "",
                script_text,
            ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render 收盤夜話 editorial JSON as readable Markdown.")
    parser.add_argument("--editorial", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = json.loads(Path(args.editorial).read_text(encoding="utf-8"))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(payload), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
