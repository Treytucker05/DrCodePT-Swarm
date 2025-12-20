#!/usr/bin/env python
import json
from pathlib import Path
import sys


SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "agent" / "llm" / "schemas"


def _check_schema(obj, path, issues):
    if isinstance(obj, dict):
        if obj.get("type") == "object":
            props = obj.get("properties") or {}
            required = obj.get("required")
            if props:
                if not isinstance(required, list):
                    issues.append(f"{path}: required must list every property key")
                else:
                    missing = [k for k in props.keys() if k not in required]
                    if missing:
                        issues.append(f"{path}: required missing {missing}")
            if obj.get("additionalProperties") is not False:
                issues.append(f"{path}: additionalProperties must be false")

        for key, value in obj.items():
            _check_schema(value, f"{path}.{key}", issues)
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            _check_schema(value, f"{path}[{idx}]", issues)


def main() -> int:
    if not SCHEMAS_DIR.is_dir():
        print(f"Schema directory not found: {SCHEMAS_DIR}")
        return 2

    issues = []
    for schema_path in sorted(SCHEMAS_DIR.glob("*.json")):
        try:
            data = json.loads(schema_path.read_text(encoding="utf-8"))
        except Exception as exc:
            issues.append(f"{schema_path.name}: failed to read JSON ({exc})")
            continue
        _check_schema(data, schema_path.name, issues)

    if issues:
        print("Schema lint failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Schemas OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
