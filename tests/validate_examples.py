"""Validate all WODIS example files against wodis.schema.json."""

import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "wodis.schema.json"
EXAMPLE_DIRS = [
    ROOT / "examples",
    ROOT / "examples" / "real-world",
]


def main():
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)

    examples = []
    for d in EXAMPLE_DIRS:
        if d.is_dir():
            examples.extend(sorted(d.glob("*.json")))

    if not examples:
        print("No example files found.")
        sys.exit(1)

    print("Validating WODIS examples against schema...")

    passed = 0
    failed = 0

    for path in examples:
        rel = path.relative_to(ROOT)
        with open(path) as f:
            data = json.load(f)
        try:
            jsonschema.validate(data, schema)
            print(f"  {rel}: PASS")
            passed += 1
        except jsonschema.ValidationError as e:
            print(f"  {rel}: FAIL")
            print(f"    {e.message}")
            failed += 1

    total = passed + failed
    print()
    if failed:
        print(f"{passed}/{total} examples valid, {failed} failed.")
        sys.exit(1)
    else:
        print(f"{total}/{total} examples valid.")


if __name__ == "__main__":
    main()
