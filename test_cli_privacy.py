import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from threading import Lock
from unittest.mock import patch

import Bech32PassHunter as app


class ResultPrivacyTests(unittest.TestCase):
    def test_hidden_match_records_only_status(self):
        state = {"found": False, "lock": Lock()}
        with patch.object(app, "generate_address", return_value="example"):
            app.worker(["synthetic sample"], state, "unused", "example", False)
        self.assertIs(state["found"], True)
        self.assertNotIn("match_text", state)

    def test_revealed_text_cannot_control_terminal(self):
        out = io.StringIO()
        state = {"match_text": "example\x1b[2J"}
        with contextlib.redirect_stdout(out), patch.object(out, "isatty", return_value=True):
            app.report_match(state)
        self.assertIn(r"\x1b", out.getvalue())
        self.assertNotIn("\x1b", out.getvalue())
        self.assertNotIn("match_text", state)

    def test_failed_worker_never_reports_no_match_or_echoes_input(self):
        out, err = io.StringIO(), io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text("example\n", encoding="utf-8")
            argv = ["tool", "--wordlist-path", str(path), "--workers", "1",
                    "--target-address", "example", "--update-interval", "0.01"]
            with patch.object(sys, "argv", argv), patch.object(
                app, "read_mnemonic", return_value="invalid synthetic input"
            ), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(app.main(), 2)
        self.assertIn("Run incomplete", err.getvalue())
        self.assertNotIn("not found", out.getvalue())
        self.assertNotIn("invalid synthetic input", out.getvalue() + err.getvalue())


if __name__ == "__main__":
    unittest.main()
