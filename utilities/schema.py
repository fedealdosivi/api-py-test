"""Validate JSON responses against the schemas in test_data/schemas.

A schema can point to another one by file name, e.g. ``{"$ref": "salon.json"}``.
"""

import json
from functools import cache
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.jsonschema import DRAFT202012

SCHEMAS = Path(__file__).parents[1] / "test_data" / "schemas"


@cache
def _registry(folder: Path) -> Registry:
    resources = [
        (path.name, DRAFT202012.create_resource(json.loads(path.read_text(encoding="utf-8"))))
        for path in folder.glob("*.json")
    ]
    return Registry().with_resources(resources)


def assert_schema(data, schema_name: str, folder: Path = SCHEMAS) -> None:
    registry = _registry(folder)
    validator = Draft202012Validator(registry[schema_name].contents, registry=registry)
    errors = sorted(validator.iter_errors(data), key=lambda error: list(error.absolute_path))
    assert not errors, f"response does not match {schema_name}:\n" + "\n".join(
        f"  at {'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}" for error in errors
    )
