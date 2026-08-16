from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from .errors import ValidationError


def load_market_pack(path: str | Path) -> dict:
    pack_path = Path(path)
    data = yaml.safe_load(pack_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValidationError(f"{pack_path}: Market Pack root must be an object")
    return data


def validate_market_pack(pack: dict, schema_path: str | Path) -> None:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(pack), key=lambda item: list(item.absolute_path))
    if errors:
        details = []
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            details.append(f"{location}: {error.message}")
        raise ValidationError("Invalid Market Pack:\n" + "\n".join(details))


def load_and_validate_market_pack(path: str | Path, schema_path: str | Path) -> dict:
    pack = load_market_pack(path)
    validate_market_pack(pack, schema_path)
    return pack

