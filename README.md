# GitHub Actions Log Parser

`gha-run-parser` turns a GitHub Actions run URL into a small JSON failure report that is useful for CI triage systems and human debugging.

## What it reports

- the last workflow step associated with an error;
- the most useful explicit error line;
- a Python traceback or compact surrounding context;
- a suggested fix category: `test`, `build`, `lint`, `dependency`, `configuration`, or `unknown`.

It recognizes common pytest/Jest failures, TypeScript/compilation failures, and pylint/ESLint/flake8 failures. It uses only the Python standard library.

## Install and run

```bash
python -m pip install -e .
gha-run-parser https://github.com/OWNER/REPO/actions/runs/RUN_ID --pretty
```

For private repositories or higher GitHub API limits:

```bash
gha-run-parser https://github.com/OWNER/REPO/actions/runs/RUN_ID --token "$GITHUB_TOKEN"
```

Offline parsing is supported for saved logs:

```bash
gha-run-parser https://github.com/OWNER/REPO/actions/runs/RUN_ID --log-file ./run.log
```

Example output:

```json
{
  "failing_step": "Run pytest",
  "error_message": "Process completed with exit code 1.",
  "stack_trace": [
    "Traceback (most recent call last):",
    "File \"tests/test_api.py\", line 8, in test_login",
    "assert response.status_code == 200",
    "AssertionError: assert 500 == 200"
  ],
  "suggested_fix_category": "test",
  "run": {"owner": "OWNER", "repo": "REPO", "run_id": "123"}
}
```

## Test and quality checks

```bash
python -m unittest discover -v
python -m compileall -q gha_parser tests
pylint gha_parser tests
```

The standard-library tests cover URL parsing, pytest tracebacks, build errors, lint errors, context extraction, unknown logs, and the CLI's offline path. The current pylint run scores 8.75/10. No third-party test runner is required.

## Design notes

The GitHub Actions logs endpoint returns a ZIP archive. The client combines the named job logs in sorted order, keeps authentication optional for public runs, and never writes the downloaded logs to disk. The parser is deterministic and easy to embed because its core function accepts plain text and returns a typed dataclass.
