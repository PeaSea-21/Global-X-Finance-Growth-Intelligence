#!/usr/bin/env python3
"""Extract non-reconstructive transcript features and compare draft overlap."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import sys
from pathlib import Path


MARKERS = {
    "evidence": ["根據", "資料", "數據", "財報", "官方", "顯示", "報告", "統計"],
    "uncertainty": ["可能", "或許", "仍需", "不確定", "如果", "假設", "情境", "風險"],
    "transition": ["但是", "不過", "接下來", "所以", "因此", "換句話說", "最後", "回到"],
    "cta": ["訂閱", "按讚", "留言", "分享", "追蹤", "開啟小鈴鐺"],
}


def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def normalize(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u3400-\u9fff]+", "", text).lower()


def sentences(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"[。！？!?\n]+", text) if item.strip()]


def marker_counts(text: str) -> dict[str, int]:
    return {name: sum(text.count(marker) for marker in markers) for name, markers in MARKERS.items()}


def features(path: str) -> dict[str, object]:
    text = read_text(path)
    units = sentences(text)
    lengths = [len(normalize(unit)) for unit in units]
    normalized = normalize(text)
    return {
        "schema_version": "1.0",
        "source_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "opening_sha256": hashlib.sha256(text[:180].encode("utf-8")).hexdigest(),
        "character_count": len(text),
        "normalized_character_count": len(normalized),
        "sentence_count": len(units),
        "paragraph_count": len([x for x in re.split(r"\n\s*\n", text) if x.strip()]),
        "average_sentence_characters": round(statistics.mean(lengths), 2) if lengths else 0.0,
        "median_sentence_characters": round(statistics.median(lengths), 2) if lengths else 0.0,
        "question_count": len(re.findall(r"[？?]", text)),
        "marker_counts": marker_counts(text),
        "source_body_persisted": False,
    }


def ngrams(text: str, n: int) -> set[str]:
    value = normalize(text)
    return {value[i:i+n] for i in range(max(0, len(value) - n + 1))}


def longest_match_length(a: str, b: str) -> int:
    a, b = normalize(a), normalize(b)
    if not a or not b:
        return 0
    previous = [0] * (len(b) + 1)
    best = 0
    for char_a in a:
        current = [0]
        for j, char_b in enumerate(b, 1):
            value = previous[j - 1] + 1 if char_a == char_b else 0
            current.append(value)
            best = max(best, value)
        previous = current
    return best


def compare(source_path: str, draft_path: str) -> dict[str, object]:
    source, draft = read_text(source_path), read_text(draft_path)
    source_grams, draft_grams = ngrams(source, 5), ngrams(draft, 5)
    union = source_grams | draft_grams
    overlap = source_grams & draft_grams
    longest = longest_match_length(source, draft)
    jaccard = len(overlap) / len(union) if union else 0.0
    return {
        "schema_version": "1.0",
        "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "draft_sha256": hashlib.sha256(draft.encode("utf-8")).hexdigest(),
        "character_5gram_jaccard": round(jaccard, 6),
        "longest_contiguous_normalized_match": longest,
        "review_required": longest >= 20 or jaccard >= 0.20,
        "matched_source_text_persisted": False,
        "notice": "Heuristic QA signal, not a legal safe harbor.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p_features = sub.add_parser("features")
    p_features.add_argument("text_file")
    p_compare = sub.add_parser("compare")
    p_compare.add_argument("source_file")
    p_compare.add_argument("draft_file")
    args = parser.parse_args()
    payload = features(args.text_file) if args.command == "features" else compare(args.source_file, args.draft_file)
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
