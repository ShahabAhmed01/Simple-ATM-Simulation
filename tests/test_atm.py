"""Scripted integration tests for the Simple ATM Simulation.

The suite compiles the single source file into a temporary directory, then
drives the executable with scripted stdin. It uses the program's --fast flag
so animation delays do not slow down CI.

Requirements: Python 3.8+ and a C++17 compiler on PATH (g++ by default).
Set the CXX environment variable to use a different compiler command.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Atm Simulation.cpp"
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


def compiler_command():
    return shlex.split(os.environ.get("CXX", "g++"))


class AtmIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SOURCE.is_file():
            raise unittest.SkipTest(f"source file not found: {SOURCE}")
        cls.temp_dir = tempfile.TemporaryDirectory(prefix="atm-tests-")
        cls.exe = Path(cls.temp_dir.name) / ("atm.exe" if os.name == "nt" else "atm")
        cmd = compiler_command() + [
            "-std=c++17",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Wpedantic",
            str(SOURCE),
            "-o",
            str(cls.exe),
        ]
        result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                "compilation failed\n"
                f"command: {' '.join(cmd)}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def run_atm(self, lines, *, timeout=30):
        payload = "\n".join(lines) + "\n"
        result = subprocess.run(
            [str(self.exe), "--fast"],
            input=payload,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return result.returncode, self.clean(result.stdout + result.stderr)

    def run_raw(self, payload, *, timeout=30):
        result = subprocess.run(
            [str(self.exe), "--fast"],
            input=payload,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return result.returncode, self.clean(result.stdout + result.stderr)

    @staticmethod
    def clean(output):
        return ANSI_RE.sub("", output).replace("\r\n", "\n").replace("\r", "")

    def test_quit_from_main_menu(self):
        code, out = self.run_atm(["3"])
        self.assertEqual(code, 0)
        self.assertIn("Thank you for banking with us.", out)
        self.assertIn("Goodbye.", out)

    def test_login_and_balance(self):
        code, out = self.run_atm(["1", "1001", "1234", "1", "", "5", "3"])
        self.assertEqual(code, 0)
        self.assertIn("ACCESS GRANTED", out)
        self.assertIn("Welcome, Shahab Ahmed", out)
        self.assertIn("available balance", out)
        self.assertIn("$5000.00", out)

    def test_deposit_and_history(self):
        code, out = self.run_atm(["1", "1001", "1234", "2", "250", "", "4", "", "5", "3"])
        self.assertEqual(code, 0)
        self.assertIn("+ $250.00  deposited", out)
        self.assertIn("New balance: $5250.00", out)
        self.assertIn("DEPOSIT", out)
        self.assertIn("+$250.00", out)
        self.assertIn("$5250.00", out)

    def test_withdraw_success(self):
        code, out = self.run_atm(["1", "1002", "4321", "3", "200", "", "4", "", "5", "3"])
        self.assertEqual(code, 0)
        self.assertIn("- $200.00  withdrawn", out)
        self.assertIn("New balance: $3000.50", out)
        self.assertIn("WITHDRAW", out)
        self.assertIn("-$200.00", out)

    def test_withdraw_insufficient_funds(self):
        code, out = self.run_atm(["1", "1001", "1234", "3", "999999", "", "5", "3"])
        self.assertEqual(code, 0)
        self.assertIn("INSUFFICIENT FUNDS", out)
        self.assertIn("Available: $5000.00", out)

    def test_wrong_pin_locks_card(self):
        code, out = self.run_atm(["1", "1001", "0000", "1111", "2222", "", "3"])
        self.assertEqual(code, 0)
        self.assertIn("Incorrect. 2 attempt(s) left.", out)
        self.assertIn("Incorrect. 1 attempt(s) left.", out)
        self.assertIn("CARD BLOCKED", out)

    def test_admin_creates_account(self):
        code, out = self.run_atm(
            ["2", "9999", "1", "Test User", "5678", "1000", "", "3", "3"]
        )
        self.assertEqual(code, 0)
        self.assertIn("Account created for Test User", out)
        self.assertIn("1004", out)
        self.assertIn("Test User", out)

    def test_invalid_menu_input_reprompts(self):
        code, out = self.run_atm(["abc", "4", "3"])
        self.assertEqual(code, 0)
        self.assertIn("enter 1-3.", out)

    def test_non_numeric_account_id_reprompts(self):
        code, out = self.run_atm(["1", "abc", "1001", "1234", "5", "3"])
        self.assertEqual(code, 0)
        self.assertIn("enter a numeric account ID.", out)
        self.assertIn("Welcome, Shahab Ahmed", out)

    def test_non_finite_amount_is_rejected(self):
        code, out = self.run_atm(["1", "1001", "1234", "2", "inf", "250", "", "5", "3"])
        self.assertEqual(code, 0)
        self.assertIn("invalid — enter a positive number.", out)
        self.assertIn("New balance: $5250.00", out)

    def test_eof_exits_cleanly(self):
        code, out = self.run_raw("1\n", timeout=10)
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
