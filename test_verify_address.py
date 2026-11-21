import contextlib
import io
import sys
import unittest
from unittest.mock import patch

from bip_utils import Bip44Changes, Bip84, Bip84Coins

import Bech32PassHunter as app


class PublicExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.account = Bip84.FromSeed(bytes(range(32)), Bip84Coins.BITCOIN).Purpose().Coin().Account(1)
        cls.export = cls.account.PublicKey().ToExtended()
        cls.branch = cls.account.Change(Bip44Changes.CHAIN_EXT)

    def verify(self, address, export, args=()):
        out = io.StringIO()
        with patch.object(app, "read_hidden", side_effect=[address, export]), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = app.verify_address(list(args))
        text = out.getvalue()
        self.assertNotIn(address, text)
        self.assertNotIn(export, text)
        return code, text

    def test_range_boundaries(self):
        for index in (0, 19, 20):
            with self.subTest(index=index):
                address = self.branch.AddressIndex(index).PublicKey().ToAddress()
                code, text = self.verify(address, self.export)
                self.assertEqual(code, int(index == 20))
                self.assertIn("0 through 19" if index == 20 else f"index {index}.", text)

    def test_rejects_private_or_non_account_exports(self):
        address = self.branch.AddressIndex(0).PublicKey().ToAddress()
        for value in (self.account.PrivateKey().ToExtended(), self.branch.PublicKey().ToExtended()):
            self.assertEqual(self.verify(address, value)[0], 2)

    def test_count_one(self):
        address = self.branch.AddressIndex(1).PublicKey().ToAddress()
        self.assertEqual(self.verify(address, self.export, ["--count", "1"])[0], 1)

    def test_first_address_disclosure(self):
        account = Bip84.FromSeed(bytes(range(32)), Bip84Coins.BITCOIN).Purpose().Coin().Account(0)
        export = account.PublicKey().ToExtended()
        branch = account.Change(Bip44Changes.CHAIN_EXT)
        first = branch.AddressIndex(0).PublicKey().ToAddress()
        for index, tty, answer, should_prompt, should_show in [
            (7, True, "yes", True, True), (7, True, "", True, False),
            (7, False, "yes", False, False), (0, True, "yes", False, False),
            (20, True, "yes", False, False),
        ]:
            with self.subTest(index=index, tty=tty, answer=answer):
                address = branch.AddressIndex(index).PublicKey().ToAddress()
                out = io.StringIO()
                with patch.object(sys.stdin, "isatty", return_value=True), \
                        patch.object(out, "isatty", return_value=tty), contextlib.redirect_stdout(out), \
                        patch.object(app, "read_hidden", side_effect=[address, export]), \
                        patch("builtins.input", return_value=answer) as prompt:
                    self.assertEqual(app.verify_address([]), int(index == 20))
                self.assertEqual(prompt.called, should_prompt)
                self.assertEqual(first in out.getvalue(), should_show)
                self.assertNotIn(export, out.getvalue())
