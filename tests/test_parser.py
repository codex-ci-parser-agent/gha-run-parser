import json
import unittest

from gha_parser.github import parse_run_url
from gha_parser.parser import parse_failure_logs


class ParserTests(unittest.TestCase):
    def test_extracts_pytest_failure_and_traceback(self) -> None:
        logs = """
2026-04-01T10:00:00Z ##[group]Run pytest
============================= test session starts =============================
Traceback (most recent call last):
  File "tests/test_api.py", line 8, in test_login
    assert response.status_code == 200
AssertionError: assert 500 == 200
##[error]Process completed with exit code 1.
##[endgroup]
"""
        report = parse_failure_logs(logs)
        self.assertEqual(report.failing_step, "Run pytest")
        self.assertIn("Process completed", report.error_message)
        self.assertEqual(report.stack_trace[0], "Traceback (most recent call last):")
        self.assertEqual(report.suggested_fix_category, "test")


    def test_classifies_typescript_build_failure(self) -> None:
        report = parse_failure_logs("##[group]Run npm run build\nTypeScript compilation error: TS2322\n##[error]build failed")
        self.assertEqual(report.failing_step, "Run npm run build")
        self.assertEqual(report.suggested_fix_category, "build")


    def test_classifies_lint_failure(self) -> None:
        report = parse_failure_logs("##[group]Run pylint src\n************* Module app\n##[error]pylint found 2 errors")
        self.assertEqual(report.suggested_fix_category, "lint")


    def test_returns_context_when_no_traceback_exists(self) -> None:
        report = parse_failure_logs("##[group]Run npm test\n2 tests failed\n##[error]exit code 1")
        self.assertTrue(report.stack_trace)
        self.assertEqual(report.failing_step, "Run npm test")


    def test_unknown_logs_are_still_json_serializable(self) -> None:
        report = parse_failure_logs("##[group]Run custom check\n##[endgroup]")
        payload = json.dumps(report.to_dict())
        self.assertIn('"suggested_fix_category": "unknown"', payload)


    def test_parses_run_url(self) -> None:
        self.assertEqual(parse_run_url("https://github.com/acme/api/actions/runs/12345"), {
            "owner": "acme",
            "repo": "api",
            "run_id": "12345",
        })


if __name__ == "__main__":
    unittest.main()
