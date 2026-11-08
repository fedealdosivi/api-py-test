import json

import pytest

from utilities.schema import assert_schema
from utilities.test_data import load_cases


@pytest.fixture
def cases_file(tmp_path):
    cases = [
        {"id": "works", "params": {"q": "a"}, "total": 1},
        {"id": "broken", "params": {"q": "b"}, "total": 2, "known_bug": "b is ignored"},
    ]
    (tmp_path / "cases.json").write_text(json.dumps(cases))
    return tmp_path


def test_cases_become_params_with_ids(cases_file):
    works, _ = load_cases("cases.json", "params", "total", folder=cases_file)

    assert works.id == "works"
    assert works.values == ({"q": "a"}, 1)
    assert works.marks == []


def test_known_bug_becomes_strict_xfail(cases_file):
    _, broken = load_cases("cases.json", "params", "total", folder=cases_file)

    (mark,) = broken.marks
    assert mark.name == "xfail"
    assert mark.kwargs == {"reason": "b is ignored", "strict": True}


@pytest.fixture
def schemas(tmp_path):
    (tmp_path / "item.json").write_text(
        json.dumps({"type": "object", "required": ["id"], "properties": {"id": {"type": "integer"}}})
    )
    (tmp_path / "list.json").write_text(json.dumps({"type": "array", "items": {"$ref": "item.json"}}))
    return tmp_path


def test_schema_accepts_matching_data(schemas):
    assert_schema([{"id": 1}], "list.json", folder=schemas)


def test_schema_error_names_the_failing_path(schemas):
    with pytest.raises(AssertionError, match=r"at 1/id: 'x' is not of type 'integer'"):
        assert_schema([{"id": 1}, {"id": "x"}], "list.json", folder=schemas)
