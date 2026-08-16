from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


SKIP_DIRECTORIES = {
    ".git", ".venv", "__pycache__", ".pytest_cache", ".pytest-tmp", "node_modules",
    "build", "dist",
}
TEXT_SUFFIXES = {
    ".py", ".toml", ".yaml", ".yml", ".json", ".md", ".txt", ".csv",
    ".ini", ".cfg", ".conf", ".env", ".sql", ".sh", ".ps1",
}
KNOWN_SECRET_PATTERNS = (
    ("OpenAI-style key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("GitHub token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{15,}\b")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
)
ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|cookie|secret)\b"
    r"\s*[:=]\s*[\"']([^\"']{8,})[\"']"
)
PLACEHOLDER_WORDS = {"example", "placeholder", "changeme", "redacted", "dummy", "synthetic"}


@dataclass(frozen=True)
class SecretFinding:
    path: Path
    line: int
    kind: str


def _is_candidate(path: Path) -> bool:
    return path.name.startswith(".env") or path.suffix.lower() in TEXT_SUFFIXES


def scan_credentials(root: str | Path) -> list[SecretFinding]:
    base = Path(root).resolve()
    findings: list[SecretFinding] = []
    for path in base.rglob("*"):
        relative_path = path.relative_to(base)
        if not path.is_file() or any(
            part in SKIP_DIRECTORIES for part in relative_path.parts[:-1]
        ):
            continue
        if not _is_candidate(path):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for number, line in enumerate(lines, start=1):
            for kind, pattern in KNOWN_SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(SecretFinding(relative_path, number, kind))
            assignment = ASSIGNMENT_PATTERN.search(line)
            if assignment:
                candidate = assignment.group(1).lower()
                if not any(word in candidate for word in PLACEHOLDER_WORDS):
                    findings.append(SecretFinding(relative_path, number, "credential assignment"))
    return findings
