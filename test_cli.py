from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from gha_parser.cli import main


class CliTests(unittest.TestCase):
    def test_cli_reads_offline_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "run.log"
            log_file.write_text("##[group]Run pytest\n##[error]pytest failed", encoding="utf-8")
            output_buffer = io.StringIO()
            with redirect_stdout(output_buffer):
                exit_code = main([
                    "https://github.com/acme/api/actions/runs/123",
                    "--log-file",
                    str(log_file),
                ])
        self.assertEqual(exit_code, 0)
        output = json.loads(output_buffer.getvalue())
        self.assertEqual(output["failing_step"], "Run pytest")
        self.assertEqual(output["run"]["run_id"], "123")


if __name__ == "__main__":
    unittest.main()
