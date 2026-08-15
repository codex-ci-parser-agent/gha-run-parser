"""Command-line interface for the GitHub Actions run parser."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Optional

from .github import GithubApiError, download_run_logs, report_metadata
from .parser import parse_failure_logs


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Extract failing-step, error, traceback, and fix category "
            "from a GitHub Actions run."
        )
    )
    parser.add_argument("run_url", help="GitHub Actions run URL")
    parser.add_argument(
        "--token", help="Optional GitHub token for private repos or higher rate limits"
    )
    parser.add_argument(
        "--log-file", type=Path, help="Read a saved log file instead of calling GitHub"
    )
    parser.add_argument("--pretty", action="store_true", help="Indent the JSON output")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Run the CLI and return a process exit code."""
    args = build_parser().parse_args(argv)
    try:
        log_text = (
            args.log_file.read_text(encoding="utf-8")
            if args.log_file
            else download_run_logs(args.run_url, args.token)
        )
        report = parse_failure_logs(log_text).to_dict()
        report["run"] = report_metadata(args.run_url)
        print(json.dumps(report, indent=2 if args.pretty else None, ensure_ascii=False))
        return 0
    except (OSError, ValueError, GithubApiError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
