import contextlib
import io
import sys
import unittest
from types import SimpleNamespace
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
        args = SimpleNamespace(workers=1, chunk_size=0, target_address=app.DEFAULT_TARGET_ADDRESS,
                               update_interval=0.01, show_passphrase=False)
        with app.Manager() as manager, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(app.run_checks(args, ["example"], "invalid synthetic input", manager), 2)
        self.assertIn("Run incomplete", err.getvalue())
        self.assertNotIn("not found", out.getvalue())
        self.assertNotIn("invalid synthetic input", out.getvalue() + err.getvalue())

    def test_checksum_typo_rejected_before_secret_prompt(self):
        bad = app.DEFAULT_TARGET_ADDRESS[:-1] + "q"
        err = io.StringIO()
        with patch.object(sys, "argv", ["tool", "--target-address", bad]), \
                patch.object(app, "read_mnemonic") as prompt, contextlib.redirect_stderr(err):
            self.assertEqual(app.main(), 2)
            prompt.assert_not_called()
        self.assertIn("Invalid target address", err.getvalue())
        self.assertNotIn(bad, err.getvalue())

    def test_invalid_mnemonic_not_echoed_or_sent_to_workers(self):
        err = io.StringIO()
        with patch.object(sys, "argv", ["tool", "--target-address", app.DEFAULT_TARGET_ADDRESS]), \
                patch.object(app, "read_mnemonic", return_value="synthetic invalid input"), \
                patch.object(app, "Manager") as manager, contextlib.redirect_stderr(err):
            self.assertEqual(app.main(), 2)
            manager.assert_not_called()
        self.assertIn("Invalid BIP39 mnemonic", err.getvalue())
        self.assertNotIn("synthetic invalid input", err.getvalue())


if __name__ == "__main__":
    unittest.main()
