"""GitHub Actions log parsing utilities."""

from .parser import FailureReport, parse_failure_logs

__all__ = ["FailureReport", "parse_failure_logs"]
