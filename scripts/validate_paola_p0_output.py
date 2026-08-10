import argparse
import json
import sys
from pathlib import Path

from validate_fixtures import load_schemas, validate_value


ROOT = Path(__file__).resolve().parents[1]


def validate_output(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    schemas = load_schemas()
    paola = data.get("paola_track_output")
    if not isinstance(paola, dict):
        raise ValueError("missing paola_track_output object")

    validate_value(paola["run_context"], schemas["run_context.schema.json"], schemas, "paola_track_output.run_context")
    for index, source in enumerate(paola.get("sources", [])):
        validate_value(source, schemas["source.schema.json"], schemas, f"paola_track_output.sources[{index}]")
    for index, evidence in enumerate(paola.get("evidence", [])):
        validate_value(evidence, schemas["evidence.schema.json"], schemas, f"paola_track_output.evidence[{index}]")
    for index, finding in enumerate(paola.get("findings", [])):
        validate_value(finding, schemas["finding.schema.json"], schemas, f"paola_track_output.findings[{index}]")

    if data.get("controlled_state") == "ok":
        if not paola.get("sources"):
            raise ValueError("happy path expected at least one normalized source")
        if not paola.get("evidence"):
            raise ValueError("happy path expected at least one evidence object")
        source_ids = {source["source_id"] for source in paola["sources"]}
        if not any(set(evidence["source_ids"]) & source_ids for evidence in paola["evidence"]):
            raise ValueError("expected at least one evidence object to reference a normalized source")
        if not data.get("rag_context", {}).get("contexts"):
            raise ValueError("expected at least one retrieved RAG context")
        if not paola.get("findings"):
            raise ValueError("expected at least one revenue finding")

    return data


def main():
    parser = argparse.ArgumentParser(description="Validate a saved Paola P0 vertical slice output.")
    parser.add_argument("path")
    args = parser.parse_args()
    try:
        data = validate_output(args.path)
    except Exception as exc:
        print("Paola P0 output validation FAILED")
        print(f"- {exc}")
        return 1
    print("Paola P0 output validation PASSED")
    print(f"- controlled_state: {data.get('controlled_state')}")
    print(f"- sources: {len(data.get('paola_track_output', {}).get('sources', []))}")
    print(f"- evidence: {len(data.get('paola_track_output', {}).get('evidence', []))}")
    print(f"- findings: {len(data.get('paola_track_output', {}).get('findings', []))}")
    print(f"- rag_contexts: {len(data.get('rag_context', {}).get('contexts', []))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

