"""Load data-driven test cases from test_data/*.json.

Each case is an object with an ``id`` and the arguments the test takes. A case
with a ``known_bug`` field becomes a strict xfail: it is reported as a known
failure, and it fails the run once the bug is fixed so the marker gets removed.
"""

import json
from pathlib import Path

import pytest

TEST_DATA = Path(__file__).parents[1] / "test_data"


def load_cases(file_name: str, *argnames: str, folder: Path = TEST_DATA) -> list:
    cases = json.loads((folder / file_name).read_text(encoding="utf-8"))
    return [
        pytest.param(
            *(case[name] for name in argnames),
            id=case["id"],
            marks=[pytest.mark.xfail(reason=case["known_bug"], strict=True)] if "known_bug" in case else [],
        )
        for case in cases
    ]
