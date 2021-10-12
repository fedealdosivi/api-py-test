"""Turns the HTTP calls a test made into readable text for test reports.

When a test fails, the conftest attaches this text to the report, so the HTML
report, the JUnit XML and the terminal all show exactly which requests were
sent and what came back, without re-running anything.
"""

import requests

MAX_BODY_CHARS = 2000
SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key"}


def format_calls(responses: list[requests.Response]) -> str:
    return "\n\n".join(_format_call(number, response) for number, response in enumerate(responses, 1))


def _format_call(number: int, response: requests.Response) -> str:
    request = response.request
    elapsed_ms = response.elapsed.total_seconds() * 1000
    return "\n".join(
        [
            f"#{number} {request.method} {request.url} -> {response.status_code} ({elapsed_ms:.0f} ms)",
            f"Request headers: {_mask(request.headers)}",
            f"Request body: {_truncate(request.body)}",
            f"Response headers: {_mask(response.headers)}",
            f"Response body: {_truncate(response.text)}",
        ]
    )


def _mask(headers) -> dict:
    return {key: "***" if key.lower() in SENSITIVE_HEADERS else value for key, value in headers.items()}


def _truncate(body) -> str:
    if not body:
        return "<empty>"
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    return body if len(body) <= MAX_BODY_CHARS else body[:MAX_BODY_CHARS] + "... <truncated>"
