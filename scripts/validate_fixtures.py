import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DIR = ROOT / "contracts"
FIXTURE_DIR = ROOT / "fixtures"


FIXTURE_SCHEMA_MAP = {
    "organization_input.json": "run_context.schema.json",
    "source_example.json": "source.schema.json",
    "evidence_example.json": "evidence.schema.json",
    "finding_example.json": "finding.schema.json",
    "final_package_example.json": "final_package.schema.json",
}

PAOLA_COLLECTIONS = {
    "run_context": "run_context.schema.json",
    "sources": "source.schema.json",
    "evidence": "evidence.schema.json",
    "findings": "finding.schema.json",
}

GRETEL_COLLECTIONS = {
    "hypotheses": "hypothesis.schema.json",
    "diagnoses": "diagnosis.schema.json",
    "recommendations": "recommendation.schema.json",
    "kpis": "kpi.schema.json",
    "validation_questions": "validation_question.schema.json",
    "roadmap_actions": "roadmap_action.schema.json",
}

REQUIRED_FIXTURES = sorted(
    set(FIXTURE_SCHEMA_MAP)
    | {
        "paola_track_output.json",
        "paola_track_insufficient_evidence.json",
        "gretel_track_output.json",
    }
)


class ValidationError(Exception):
    pass


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{path.name}: invalid JSON: {exc}") from exc


def load_schemas():
    schemas = {}
    for path in CONTRACT_DIR.glob("*.schema.json"):
        schemas[path.name] = load_json(path)
    return schemas


def resolve_ref(ref, schemas):
    filename = ref.split("#", 1)[0]
    if filename not in schemas:
        raise ValidationError(f"schema ref not found: {ref}")
    return schemas[filename]


def type_matches(value, expected):
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def validate_value(value, schema, schemas, path="$"):
    if "$ref" in schema:
        validate_value(value, resolve_ref(schema["$ref"], schemas), schemas, path)
        return

    if "const" in schema and value != schema["const"]:
        raise ValidationError(f"{path}: expected const {schema['const']!r}, got {value!r}")

    expected_type = schema.get("type")
    if isinstance(expected_type, list):
        if not any(type_matches(value, option) for option in expected_type):
            raise ValidationError(f"{path}: expected one of {expected_type}, got {type(value).__name__}")
    elif expected_type and not type_matches(value, expected_type):
        raise ValidationError(f"{path}: expected {expected_type}, got {type(value).__name__}")

    if "enum" in schema and value not in schema["enum"]:
        raise ValidationError(f"{path}: expected enum value from {schema['enum']}, got {value!r}")

    if isinstance(value, str) and "pattern" in schema:
        if not re.search(schema["pattern"], value):
            raise ValidationError(f"{path}: value {value!r} does not match {schema['pattern']}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValidationError(f"{path}: {value} is below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise ValidationError(f"{path}: {value} is above maximum {schema['maximum']}")

    if isinstance(value, dict):
        for required_key in schema.get("required", []):
            if required_key not in value:
                raise ValidationError(f"{path}: missing required key {required_key}")
        for key, child_schema in schema.get("properties", {}).items():
            if key in value:
                validate_value(value[key], child_schema, schemas, f"{path}.{key}")

    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            validate_value(item, schema["items"], schemas, f"{path}[{index}]")


def validate_fixture_against_schema(fixture_name, schema_name, schemas):
    fixture = load_json(FIXTURE_DIR / fixture_name)
    validate_value(fixture, schemas[schema_name], schemas, fixture_name)


def validate_paola_output(schemas, fixture_name="paola_track_output.json"):
    data = load_json(FIXTURE_DIR / fixture_name)
    for key, schema_name in PAOLA_COLLECTIONS.items():
        if key not in data:
            raise ValidationError(f"{fixture_name}: missing {key}")
        if isinstance(data[key], list):
            for index, item in enumerate(data[key]):
                validate_value(item, schemas[schema_name], schemas, f"{fixture_name}.{key}[{index}]")
        else:
            validate_value(data[key], schemas[schema_name], schemas, f"{fixture_name}.{key}")
    for key in ["unknowns", "contradictions", "rag_metadata"]:
        if key not in data:
            raise ValidationError(f"{fixture_name}: missing {key}")


def validate_gretel_output(schemas):
    data = load_json(FIXTURE_DIR / "gretel_track_output.json")
    for key, schema_name in GRETEL_COLLECTIONS.items():
        if key not in data:
            raise ValidationError(f"gretel_track_output.json: missing {key}")
        if not isinstance(data[key], list):
            raise ValidationError(f"gretel_track_output.json.{key}: expected array")
        for index, item in enumerate(data[key]):
            validate_value(item, schemas[schema_name], schemas, f"gretel_track_output.json.{key}[{index}]")


def main():
    errors = []
    for filename in REQUIRED_FIXTURES:
        if not (FIXTURE_DIR / filename).exists():
            errors.append(f"missing fixture: {filename}")

    try:
        schemas = load_schemas()
    except ValidationError as exc:
        errors.append(str(exc))
        schemas = {}

    if schemas:
        for fixture_name, schema_name in FIXTURE_SCHEMA_MAP.items():
            if (FIXTURE_DIR / fixture_name).exists():
                try:
                    validate_fixture_against_schema(fixture_name, schema_name, schemas)
                except ValidationError as exc:
                    errors.append(str(exc))

        for fixture_name in ["paola_track_output.json", "paola_track_insufficient_evidence.json"]:
            try:
                validate_paola_output(schemas, fixture_name)
            except ValidationError as exc:
                errors.append(str(exc))

        try:
            validate_gretel_output(schemas)
        except ValidationError as exc:
            errors.append(str(exc))

    if errors:
        print("fixture validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("fixture validation PASSED")
    print(f"- fixtures checked: {len(REQUIRED_FIXTURES)}")
    print(f"- schemas loaded: {len(schemas)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
