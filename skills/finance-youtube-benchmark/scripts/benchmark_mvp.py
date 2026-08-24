#!/usr/bin/env python3
"""Dependency-free utilities for the finance-youtube-benchmark MVP."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


UNKNOWN = "UNKNOWN"
USER_AGENT = "finance-youtube-benchmark-mvp/0.1 (+bounded research; no login)"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_text(text: str) -> str:
    return "".join(re.findall(r"[\w\u3400-\u9fff]", text.lower(), flags=re.UNICODE))


def text_features(text: str) -> dict[str, Any]:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    sentences = [part.strip() for part in re.split(r"(?<=[。！？!?])|\n+", text) if part.strip()]
    lengths = [len(normalize_text(part)) for part in sentences]
    transition_terms = ("但是", "不過", "因此", "所以", "同時", "接下來", "換句話說", "問題是", "然而")
    transition_count = sum(text.count(term) for term in transition_terms)
    question_count = text.count("?") + text.count("？")
    number_count = len(re.findall(r"(?<!\w)[+-]?\d+(?:[.,]\d+)?%?", text))
    avg_length = round(sum(lengths) / len(lengths), 2) if lengths else 0.0
    return {
        "adapter": "local_text",
        "backend_status": "AVAILABLE",
        "actual_run_status": "SUCCESS",
        "endpoint_verified": "VERIFIED",
        "extraction_method_verified": "VERIFIED",
        "terms_status": "APPROVED",
        "commercial_use_status": "UNKNOWN",
        "cache_hit": False,
        "external_calls": 0,
        "estimated_cost_usd": 0.0,
        "transcript": {
            "status": "AVAILABLE",
            "sha256": digest,
            "body_persisted": False,
            "character_count": len(text),
            "sentence_count": len(sentences),
        },
        "rhythm": {
            "average_sentence_characters": avg_length,
            "short_sentence_ratio": round(sum(1 for length in lengths if length <= 15) / len(lengths), 4) if lengths else 0.0,
            "question_count": question_count,
            "transition_count": transition_count,
            "number_mention_count": number_count,
        },
        "limitations": ["Automated metrics do not replace human narrative analysis."],
    }


def _resolve_ref(root_schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"Only local schema references are supported: {ref}")
    value: Any = root_schema
    for component in ref[2:].split("/"):
        value = value[component.replace("~1", "/").replace("~0", "~")]
    return value


def validate_value(value: Any, schema: dict[str, Any], root_schema: dict[str, Any] | None = None, path: str = "$") -> list[str]:
    root_schema = root_schema or schema
    if "$ref" in schema:
        return validate_value(value, _resolve_ref(root_schema, schema["$ref"]), root_schema, path)
    errors: list[str] = []
    expected = schema.get("type")
    type_map = {
        "object": dict,
        "array": list,
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "null": type(None),
    }
    if expected is not None:
        expected_values = expected if isinstance(expected, list) else [expected]
        valid_type = any(isinstance(value, type_map[item]) and not (item in {"integer", "number"} and isinstance(value, bool)) for item in expected_values)
        if not valid_type:
            return [f"{path}: expected {expected}, got {type(value).__name__}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in enum")
    if isinstance(value, dict):
        for required in schema.get("required", []):
            if required not in value:
                errors.append(f"{path}: missing required property {required}")
        for key, child in value.items():
            child_schema = schema.get("properties", {}).get(key)
            if child_schema:
                errors.extend(validate_value(child, child_schema, root_schema, f"{path}.{key}"))
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: fewer than minItems")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: more than maxItems")
        item_schema = schema.get("items")
        if item_schema:
            for index, child in enumerate(value):
                errors.extend(validate_value(child, item_schema, root_schema, f"{path}[{index}]"))
    elif isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: shorter than minLength")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: does not match pattern")
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: above maximum")
    return errors


def validate_document(schema_path: Path, input_path: Path) -> dict[str, Any]:
    schema = read_json(schema_path)
    data = read_json(input_path)
    errors = validate_value(data, schema)
    return {"status": "PASS" if not errors else "FAIL", "schema": str(schema_path), "input": str(input_path), "errors": errors}


def validate_list(schema_path: Path, input_path: Path) -> dict[str, Any]:
    schema = read_json(schema_path)
    data = read_json(input_path)
    if not isinstance(data, list):
        return {"status": "FAIL", "schema": str(schema_path), "input": str(input_path), "errors": ["$: expected list"]}
    errors: list[str] = []
    for index, item in enumerate(data):
        errors.extend(validate_value(item, schema, schema, f"$[{index}]"))
    return {"status": "PASS" if not errors else "FAIL", "schema": str(schema_path), "input": str(input_path), "item_count": len(data), "errors": errors}


def ngrams(text: str, size: int = 8) -> set[str]:
    cleaned = normalize_text(text)
    if len(cleaned) < size:
        return {cleaned} if cleaned else set()
    return {cleaned[index : index + size] for index in range(len(cleaned) - size + 1)}


def compare_text(candidate: str, source: str, ngram_size: int = 8, comparison_type: str = "source") -> dict[str, Any]:
    a, b = normalize_text(candidate), normalize_text(source)
    match = SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b))
    a_grams, b_grams = ngrams(candidate, ngram_size), ngrams(source, ngram_size)
    union = a_grams | b_grams
    jaccard = len(a_grams & b_grams) / len(union) if union else 0.0
    source_blocked = match.size >= 24 or jaccard >= 0.15
    peer_blocked = match.size >= 80 or jaccard >= 0.15 or (SequenceMatcher(None, a, b, autojunk=False).ratio() >= 0.70 if a and b else False)
    return {
        "longest_match_characters": match.size,
        "longest_match_candidate_offset": match.a,
        "longest_match_source_offset": match.b,
        "ngram_size": ngram_size,
        "ngram_jaccard": round(jaccard, 6),
        "sequence_ratio": round(SequenceMatcher(None, a, b, autojunk=False).ratio(), 6) if a and b else 0.0,
        "comparison_type": comparison_type,
        "status": "BLOCKED" if (source_blocked if comparison_type == "source" else peer_blocked) else "PASS",
    }


def originality_report(candidate_path: Path, source_paths: list[Path], comparison_type: str = "source") -> dict[str, Any]:
    candidate = candidate_path.read_text(encoding="utf-8")
    comparisons = []
    for source_path in source_paths:
        result = compare_text(candidate, source_path.read_text(encoding="utf-8"), comparison_type=comparison_type)
        result["source"] = str(source_path)
        comparisons.append(result)
    return {
        "candidate": str(candidate_path),
        "comparison_type": comparison_type,
        "source_count": len(source_paths),
        "status": "BLOCKED" if any(item["status"] == "BLOCKED" for item in comparisons) else ("NOT_RUN" if not source_paths else "PASS"),
        "comparisons": comparisons,
        "limitations": ["Heuristic overlap thresholds are review signals, not legal safe harbors."],
    }


REQUIRED_STRUCTURE = {
    "SKILL.md",
    "agents/openai.yaml",
    "references/governance.md",
    "references/adapters.md",
    "references/workflow.md",
    "references/analysis.md",
    "templates/research_brief.yaml",
    "templates/channel_record.json",
    "templates/video_analysis_card.json",
    "templates/acceptance_manifest.json",
    "schemas/channel.schema.json",
    "schemas/video.schema.json",
    "schemas/video_analysis.schema.json",
    "schemas/channel_profile.schema.json",
    "schemas/factpack.schema.json",
    "schemas/content_package.schema.json",
    "schemas/run_manifest.schema.json",
    "scripts/benchmark_mvp.py",
    "tests/test_benchmark_mvp.py",
}


def check_structure(root: Path) -> dict[str, Any]:
    missing = sorted(item for item in REQUIRED_STRUCTURE if not (root / item).is_file())
    errors: list[str] = []
    skill_file = root / "SKILL.md"
    if skill_file.is_file():
        text = skill_file.read_text(encoding="utf-8")
        frontmatter = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, flags=re.DOTALL)
        if not frontmatter:
            errors.append("SKILL.md frontmatter is missing or malformed")
        else:
            metadata = frontmatter.group(1)
            name_match = re.search(r"^name:\s*(.+)$", metadata, flags=re.MULTILINE)
            description_match = re.search(r"^description:\s*(.+)$", metadata, flags=re.MULTILINE)
            if not name_match or name_match.group(1).strip() != root.name:
                errors.append("frontmatter name must equal the skill directory name")
            if not description_match or len(description_match.group(1).strip()) < 40:
                errors.append("frontmatter description is missing or too short")
            keys = re.findall(r"^([A-Za-z0-9_-]+):", metadata, flags=re.MULTILINE)
            if set(keys) != {"name", "description"}:
                errors.append("frontmatter must contain only name and description")
    return {"status": "PASS" if not missing and not errors else "FAIL", "root": str(root), "missing": missing, "errors": errors}


SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "assigned_secret": re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-\.]{20,}"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    "google_api_key": re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),
}


def credential_scan(root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    allowed_suffixes = {".md", ".json", ".jsonl", ".yaml", ".yml", ".csv", ".txt", ".py"}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in allowed_suffixes or "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append({"file": str(path), "pattern": name})
    return {"status": "PASS" if not findings else "FAIL", "findings": findings}


def adapter_status() -> dict[str, Any]:
    return {
        "local_text": {
            "backend_status": "AVAILABLE",
            "actual_run_status": "NOT_RUN",
            "endpoint_verified": "VERIFIED",
            "extraction_method_verified": "VERIFIED",
            "terms_status": "APPROVED",
            "commercial_use_status": "UNKNOWN",
        },
        "public_youtube_feed": {
            "backend_status": "AVAILABLE",
            "actual_run_status": "NOT_RUN",
            "endpoint_verified": "UNVERIFIED",
            "extraction_method_verified": "UNVERIFIED",
            "terms_status": "UNKNOWN",
            "commercial_use_status": "UNKNOWN",
        },
        "transcriptapi": {
            "backend_status": "DISABLED",
            "actual_run_status": "NOT_RUN",
            "endpoint_verified": "NOT_RUN",
            "extraction_method_verified": "DISABLED",
            "terms_status": "UNKNOWN",
            "commercial_use_status": "UNKNOWN",
            "reason": "No key is configured or requested in this MVP.",
        },
    }


def parse_youtube_atom(xml_text: str) -> dict[str, Any]:
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }
    root = ET.fromstring(xml_text)
    channel_id = root.findtext("yt:channelId", default=UNKNOWN, namespaces=ns)
    channel_title = root.findtext("atom:title", default=UNKNOWN, namespaces=ns)
    videos = []
    for entry in root.findall("atom:entry", ns):
        video_id = entry.findtext("yt:videoId", default=UNKNOWN, namespaces=ns)
        statistics = entry.find("media:group/media:community/media:statistics", ns)
        thumbnail = entry.find("media:group/media:thumbnail", ns)
        description = entry.findtext("media:group/media:description", default="", namespaces=ns)
        view_count = int(statistics.attrib["views"]) if statistics is not None and statistics.attrib.get("views", "").isdigit() else UNKNOWN
        description_result = text_features(description) if description else None
        videos.append(
            {
                "video_id": video_id,
                "video_url": f"https://www.youtube.com/watch?v={video_id}" if video_id != UNKNOWN else UNKNOWN,
                "title": entry.findtext("atom:title", default=UNKNOWN, namespaces=ns),
                "published_at": entry.findtext("atom:published", default=UNKNOWN, namespaces=ns),
                "updated_at": entry.findtext("atom:updated", default=UNKNOWN, namespaces=ns),
                "view_count": view_count,
                "thumbnail_url": thumbnail.attrib.get("url", UNKNOWN) if thumbnail is not None else UNKNOWN,
                "description_text_status": "AVAILABLE" if description else "UNAVAILABLE",
                "description_features": description_result["transcript"] | description_result["rhythm"] if description_result else {},
                "description_chapter_marker_count": len(re.findall(r"(?m)^\s*\d{1,2}:\d{2}(?::\d{2})?\b", description)),
                "description_url_count": len(re.findall(r"https?://", description)),
            }
        )
    return {"channel_id": channel_id, "channel_title": channel_title, "videos": videos}


def _append_ledger(path: Path | None, record: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def fetch_public_feed(channel_id: str, cache_dir: Path, ledger: Path | None = None, timeout: int = 15) -> dict[str, Any]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"youtube_feed_{channel_id}.xml"
    cache_hit = cache_path.exists()
    external_calls = 0
    error = None
    if cache_hit:
        xml_text = cache_path.read_text(encoding="utf-8")
    else:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        external_calls = 1
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                xml_text = response.read().decode("utf-8")
            cache_path.write_text(xml_text, encoding="utf-8")
        except (urllib.error.URLError, TimeoutError, UnicodeDecodeError) as exc:
            xml_text = ""
            error = type(exc).__name__
    captured_at = utc_now()
    if error:
        result = {
            "adapter": "public_youtube_feed",
            "backend_status": "DEGRADED",
            "actual_run_status": "FAILED",
            "endpoint_verified": "UNVERIFIED",
            "extraction_method_verified": "UNVERIFIED",
            "terms_status": "UNKNOWN",
            "commercial_use_status": "UNKNOWN",
            "cache_hit": cache_hit,
            "external_calls": external_calls,
            "estimated_cost_usd": 0.0,
            "captured_at": captured_at,
            "error": error,
            "videos": [],
        }
    else:
        parsed = parse_youtube_atom(xml_text)
        parsed["feed_channel_id"] = parsed.get("channel_id", UNKNOWN)
        parsed["channel_id"] = channel_id
        result = {
            "adapter": "public_youtube_feed",
            "backend_status": "AVAILABLE",
            "actual_run_status": "SUCCESS",
            "endpoint_verified": "VERIFIED",
            "extraction_method_verified": "VERIFIED",
            "terms_status": "UNKNOWN",
            "commercial_use_status": "UNKNOWN",
            "cache_hit": cache_hit,
            "external_calls": external_calls,
            "estimated_cost_usd": 0.0,
            "captured_at": captured_at,
            **parsed,
            "limitations": ["The Atom feed has no duration, verified format, thumbnail text, or transcripts."],
        }
    _append_ledger(
        ledger,
        {
            "captured_at": captured_at,
            "provider": "YouTube public Atom feed",
            "endpoint_class": "channel_feed",
            "channel_id": channel_id,
            "cache_hit": cache_hit,
            "external_calls": external_calls,
            "estimated_cost_usd": 0.0,
            "status": result["actual_run_status"],
        },
    )
    return result


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def select_feed_samples(feed: dict[str, Any]) -> dict[str, Any]:
    captured = _parse_datetime(feed["captured_at"])
    candidates: list[dict[str, Any]] = []
    for video in feed.get("videos", []):
        if not isinstance(video.get("view_count"), int) or video.get("published_at") in {None, UNKNOWN}:
            continue
        published = _parse_datetime(video["published_at"])
        age_days = max((captured - published.astimezone(timezone.utc)).total_seconds() / 86400, 1.0)
        item = dict(video)
        item["age_days_at_capture"] = round(age_days, 4)
        item["views_per_day"] = round(video["view_count"] / age_days, 4)
        candidates.append(item)
    if len(candidates) < 8:
        return {"status": "FAIL", "reason": "fewer than 8 comparable feed records", "samples": []}
    candidates.sort(key=lambda item: item["published_at"], reverse=True)
    recent = candidates[0]
    remaining = [item for item in candidates[1:]]
    high = max(remaining, key=lambda item: item["views_per_day"])
    typical_pool = [item for item in remaining if item["video_id"] != high["video_id"]]
    velocities = sorted(item["views_per_day"] for item in typical_pool)
    mid = len(velocities) // 2
    median = velocities[mid] if len(velocities) % 2 else (velocities[mid - 1] + velocities[mid]) / 2
    typical = min(typical_pool, key=lambda item: abs(item["views_per_day"] - median))
    samples = []
    for role, item in (("RECENT", recent), ("HIGH_PERFORMANCE_CANDIDATE", high), ("TYPICAL", typical)):
        selected = dict(item)
        selected.update(
            {
                "channel_id": feed["channel_id"],
                "captured_at": feed["captured_at"],
                "selection_role": role,
                "selection_method": "PUBLIC_METADATA",
                "baseline_status": "PROVISIONAL",
                "baseline_count": len(candidates),
                "baseline_metric": "views_per_day_with_24h_floor",
                "baseline_median": round(median, 4),
                "format_type": "UNKNOWN",
                "transcript_status": "NOT_RUN",
                "transcript_request_count": 0,
                "limitations": [
                    "Public Atom metadata has no duration or format classification.",
                    "Views-per-day is an age-adjusted candidate signal, not quality or factual accuracy.",
                ],
            }
        )
        samples.append(selected)
    return {"status": "PASS", "channel_id": feed["channel_id"], "baseline_count": len(candidates), "samples": samples}


def pilot_check(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    channels = read_json(root / "data" / "channels.json")
    videos = read_json(root / "data" / "videos.json")
    analyses = read_json(root / "analysis" / "video_analysis_cards.json")
    profiles = read_json(root / "analysis" / "channel_profiles.json")
    packages = read_json(root / "generation" / "content_packages.json")
    if len(channels) != 3:
        errors.append(f"expected 3 channels, got {len(channels)}")
    if len(videos) != 9:
        errors.append(f"expected 9 videos, got {len(videos)}")
    if len(analyses) != 9:
        errors.append(f"expected 9 analysis cards, got {len(analyses)}")
    if len(profiles) != 3:
        errors.append(f"expected 3 channel profiles, got {len(profiles)}")
    if len(packages) != 3:
        errors.append(f"expected 3 content packages, got {len(packages)}")
    if any(item.get("transcript_request_count", 0) > 1 for item in videos):
        errors.append("transcript request limit exceeded")
    channel_ids = {item["channel_id"] for item in channels}
    roles_by_channel = {channel_id: set() for channel_id in channel_ids}
    for item in videos:
        roles_by_channel.setdefault(item["channel_id"], set()).add(item["selection_role"])
        if item.get("text_body_persisted") is not False:
            errors.append(f"text persistence boundary failed for {item['video_id']}")
    required_roles = {"RECENT", "HIGH_PERFORMANCE_CANDIDATE", "TYPICAL"}
    if any(roles != required_roles for roles in roles_by_channel.values()):
        errors.append("each channel must contain recent, high-performance candidate, and typical roles")
    fact_sets = [set(item.get("fact_ids", [])) for item in packages]
    if not fact_sets or any(fact_set != fact_sets[0] for fact_set in fact_sets[1:]):
        errors.append("content packages do not share one identical fact set")
    if any(item.get("named_creator_emulation") is not False for item in packages):
        errors.append("named creator emulation must be false")
    if len(channel_ids) != 3 or any(item.get("identity_verified") != "VERIFIED" for item in channels):
        errors.append("channel identity verification incomplete")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def _emit(result: dict[str, Any], output: Path | None = None) -> int:
    if output:
        write_json(output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") not in {"FAIL", "BLOCKED"} else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest-text")
    ingest.add_argument("--input", required=True, type=Path)
    ingest.add_argument("--output", type=Path)
    validate = sub.add_parser("validate")
    validate.add_argument("--schema", required=True, type=Path)
    validate.add_argument("--input", required=True, type=Path)
    validate.add_argument("--output", type=Path)
    validate_many = sub.add_parser("validate-list")
    validate_many.add_argument("--schema", required=True, type=Path)
    validate_many.add_argument("--input", required=True, type=Path)
    validate_many.add_argument("--output", type=Path)
    originality = sub.add_parser("originality")
    originality.add_argument("--candidate", required=True, type=Path)
    originality.add_argument("--sources", nargs="*", default=[], type=Path)
    originality.add_argument("--comparison-type", choices=["source", "peer"], default="source")
    originality.add_argument("--output", type=Path)
    structure = sub.add_parser("check-structure")
    structure.add_argument("--skill-root", required=True, type=Path)
    structure.add_argument("--output", type=Path)
    scan = sub.add_parser("credential-scan")
    scan.add_argument("--path", required=True, type=Path)
    scan.add_argument("--output", type=Path)
    status = sub.add_parser("adapter-status")
    status.add_argument("--output", type=Path)
    feed = sub.add_parser("public-feed")
    feed.add_argument("--channel-id", required=True)
    feed.add_argument("--cache-dir", required=True, type=Path)
    feed.add_argument("--ledger", type=Path)
    feed.add_argument("--output", type=Path)
    select_feed = sub.add_parser("select-feed")
    select_feed.add_argument("--input", required=True, type=Path)
    select_feed.add_argument("--output", type=Path)
    pilot = sub.add_parser("pilot-check")
    pilot.add_argument("--root", required=True, type=Path)
    pilot.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "ingest-text":
        return _emit(text_features(args.input.read_text(encoding="utf-8")), args.output)
    if args.command == "validate":
        return _emit(validate_document(args.schema, args.input), args.output)
    if args.command == "validate-list":
        return _emit(validate_list(args.schema, args.input), args.output)
    if args.command == "originality":
        return _emit(originality_report(args.candidate, args.sources, args.comparison_type), args.output)
    if args.command == "check-structure":
        return _emit(check_structure(args.skill_root), args.output)
    if args.command == "credential-scan":
        return _emit(credential_scan(args.path), args.output)
    if args.command == "adapter-status":
        result = adapter_status()
        if args.output:
            write_json(args.output, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "public-feed":
        result = fetch_public_feed(args.channel_id, args.cache_dir, args.ledger)
        if args.output:
            write_json(args.output, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["actual_run_status"] == "SUCCESS" else 1
    if args.command == "select-feed":
        return _emit(select_feed_samples(read_json(args.input)), args.output)
    if args.command == "pilot-check":
        return _emit(pilot_check(args.root), args.output)
    raise AssertionError(args.command)


if __name__ == "__main__":
    sys.exit(main())
