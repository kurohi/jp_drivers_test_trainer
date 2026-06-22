"""Validate all skill module JSON files against the JSON Schema."""

import json
import sys
from pathlib import Path

import jsonschema
from jsonschema import Draft7Validator


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "docs" / "skill_module.schema.json"
MODULES_DIR = PROJECT_ROOT / "data" / "skill_modules"
FRONTEND_ASSETS = PROJECT_ROOT / "frontend" / "public"


def load_schema() -> dict:
    """Load the JSON Schema file."""
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def validate_svg_exists(module_data: dict, module_file: Path) -> list[str]:
    """Check that the referenced SVG file exists on disk."""
    errors = []
    svg_path = module_data.get("svg_path", "")
    if svg_path:
        full_path = FRONTEND_ASSETS / svg_path
        if not full_path.exists():
            errors.append(f"  SVG not found: {full_path}")
        elif full_path.stat().st_size > 5120:
            errors.append(f"  SVG too large: {full_path.name} ({full_path.stat().st_size} bytes, max 5kB)")
    return errors


def validate_module(data: dict, validator: Draft7Validator, module_file: Path) -> list[str]:
    """Validate a single module against the schema and check SVG existence."""
    errors = []

    # Schema validation
    for error in validator.iter_errors(data):
        path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "(root)"
        errors.append(f"  {path}: {error.message}")

    # SVG existence check
    errors.extend(validate_svg_exists(data, module_file))

    # Bilingual completeness: every text field must have both en and pt
    def check_bilingual(obj: dict, prefix: str) -> list[str]:
        issues = []
        for key, value in obj.items():
            if isinstance(value, dict):
                if "en" in value and "pt" not in value:
                    issues.append(f"  {prefix}.{key}: missing 'pt' translation")
                elif "pt" in value and "en" not in value:
                    issues.append(f"  {prefix}.{key}: missing 'en' translation")
                else:
                    issues.extend(check_bilingual(value, f"{prefix}.{key}"))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        issues.extend(check_bilingual(item, f"{prefix}.{key}[{i}]"))
        return issues

    errors.extend(check_bilingual(data, module_file.stem))

    return errors


def main() -> int:
    """Run validation on all skill modules. Returns 0 on success, 1 on failure."""
    schema = load_schema()
    validator = Draft7Validator(schema)

    module_files = sorted(MODULES_DIR.glob("*.json"))
    if not module_files:
        print(f"ERROR: No JSON files found in {MODULES_DIR}")
        return 1

    print(f"Validating {len(module_files)} skill modules against schema...")
    print(f"Schema: {SCHEMA_PATH}")
    print(f"Modules: {MODULES_DIR}")
    print()

    all_passed = True
    for module_file in module_files:
        with open(module_file) as f:
            data = json.load(f)

        errors = validate_module(data, validator, module_file)

        if errors:
            all_passed = False
            print(f"FAIL: {module_file.name}")
            for error in errors:
                print(error)
            print()
        else:
            print(f"PASS: {module_file.name} ({data.get('name_en', 'unknown')})")

    print()
    if all_passed:
        print(f"All {len(module_files)} modules validated successfully.")
        return 0
    else:
        print("Validation failed. Fix the errors above and re-run.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
