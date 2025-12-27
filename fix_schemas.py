import json
from pathlib import Path

def _is_object_type(schema: dict) -> bool:
    schema_type = schema.get("type")
    if schema_type == "object":
        return True
    if isinstance(schema_type, list):
        return "object" in schema_type
    return False


def fix_schema(schema):
    if isinstance(schema, dict):
        if _is_object_type(schema):
            if "additionalProperties" not in schema:
                schema["additionalProperties"] = False
            if "properties" in schema:
                all_props = list(schema["properties"].keys())
                schema["required"] = all_props
        for key, value in list(schema.items()):
            if isinstance(value, (dict, list)):
                schema[key] = fix_schema(value)
        return schema
    if isinstance(schema, list):
        return [fix_schema(item) for item in schema]
    return schema

schema_dir = Path("agent/llm/schemas")
for schema_file in schema_dir.glob("*.json"):
    print(f"Fixing {schema_file.name}...")
    with schema_file.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    fixed = fix_schema(schema)
    with schema_file.open("w", encoding="utf-8") as f:
        json.dump(fixed, f, indent=2)
    print(f"  ? Fixed {schema_file.name}")

print(f"\n? Fixed all schemas in {schema_dir}")
