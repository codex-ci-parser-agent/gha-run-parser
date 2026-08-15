"""Extract a useful, deterministic failure summary from Actions logs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class FailureReport:
    """Structured result returned by the parser."""

    failing_step: str
    error_message: str
    stack_trace: List[str]
    suggested_fix_category: str

    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serializable representation."""
        return asdict(self)


_STEP_RE = re.compile(r"##\[group\](.+?)\s*$")
_ERROR_RE = re.compile(r"##\[error\]\s*(.*)$")
_TRACE_START = "Traceback (most recent call last):"


def _strip_runner_prefix(line: str) -> str:
    """Remove the timestamp and GitHub workflow annotations from a line."""
    without_timestamp = re.sub(r"^\d{4}-\d{2}-\d{2}T[^ ]+\s+", "", line)
    return re.sub(r"^\s*##\[[^]]+\]\s*", "", without_timestamp).strip()


def _classify_failure(message: str, log_text: str) -> str:
    """Classify the failure using stable, human-readable categories."""
    haystack = f"{message}\n{log_text}".lower()
    if any(
        word in haystack for word in ("pylint", "eslint", "flake8", "lint error")
    ):
        return "lint"
    if any(
        word in haystack
        for word in ("tsc", "typescript", "compile", "compilation", "build failed")
    ):
        return "build"
    if any(
        word in haystack
        for word in ("pytest", "jest", "assertionerror", "test failed", "tests failed")
    ):
        return "test"
    if any(
        word in haystack
        for word in ("modulenotfounderror", "cannot find module", "dependency")
    ):
        return "dependency"
    if any(word in haystack for word in ("permission denied", "environment variable", "secret", "configuration")):
        return "configuration"
    return "unknown"


def _find_step(lines: List[str], error_index: int) -> str:
    """Find the latest named workflow step before an error."""
    for index in range(error_index, -1, -1):
        match = _STEP_RE.search(lines[index])
        if match:
            return _strip_runner_prefix(match.group(1))
    return "Unknown step"


def _extract_error(lines: List[str]) -> Tuple[str, int]:
    """Return the best error message and its source line index."""
    candidates: List[Tuple[str, int]] = []
    for index, line in enumerate(lines):
        match = _ERROR_RE.search(line)
        if match and match.group(1).strip():
            candidates.append((_strip_runner_prefix(match.group(1)), index))
    if candidates:
        return candidates[-1]

    for index in range(len(lines) - 1, -1, -1):
        cleaned = _strip_runner_prefix(lines[index])
        lowered = cleaned.lower()
        if cleaned and ("failed" in lowered or "error" in lowered or "exception" in lowered):
            return cleaned, index
    return "No explicit error message found", max(len(lines) - 1, 0)


def _extract_trace(lines: List[str], error_index: int) -> List[str]:
    """Extract the nearest Python-like traceback or a compact error context."""
    trace_start: Optional[int] = None
    for index in range(error_index, -1, -1):
        if _TRACE_START in lines[index]:
            trace_start = index
            break
    if trace_start is not None:
        trace: List[str] = []
        for line in lines[trace_start:]:
            cleaned = _strip_runner_prefix(line)
            if cleaned:
                trace.append(cleaned)
            if len(trace) >= 40:
                break
        return trace

    start = max(0, error_index - 2)
    context = [_strip_runner_prefix(line) for line in lines[start : error_index + 3]]
    return [line for line in context if line]


def parse_failure_logs(log_text: str) -> FailureReport:
    """Parse raw GitHub Actions log text into a failure report."""
    lines = log_text.splitlines()
    message, error_index = _extract_error(lines)
    step = _find_step(lines, error_index)
    return FailureReport(
        failing_step=step,
        error_message=message,
        stack_trace=_extract_trace(lines, error_index),
        suggested_fix_category=_classify_failure(message, log_text),
    )
