# SPDX-License-Identifier: MIT

import argparse
import sys
import unittest

from . import args
from . import const
from ccct.config.args import CCConsoleArgs

from pathlib import Path

class TestCommandLineInterface(unittest.TestCase):
    argv = sys.argv

    def setUp(self):
        sys.argv = sys.argv[0:1]

    def tearDown(self):
        sys.argv = self.argv

    def parse(self, exit_on_error=True):
        return CCConsoleArgs(exit_on_error=exit_on_error).parse()

    def test_cli_none(self):
        console_args = self.parse(False)
        self.assertIsNone(console_args.ofx_file)
        self.assertIsNone(console_args.statement_date)

    def test_cli_required(self):
        args.set_all_required()
        self.assertTrue(self.parse())

    def test_cli_credential_dir(self):
        args.set_all_required()
        for i in const.INVALID_CREDENTIAL_DIRS:
            with self.subTest(i=i):
                args.set_credential_dir(i)
                self.assertRaises(argparse.ArgumentError, self.parse, False)
        for i in const.VALID_CREDENTIAL_DIRS:
            with self.subTest(i=i):
                args.set_credential_dir(i)
                console_args = self.parse()
                self.assertIsInstance(console_args.credential_dir, Path)

    def test_cli_bank_id(self):
        args.set_all_required()
        for i in const.INVALID_BANK_IDS:
            with self.subTest(i=i):
                args.set_bank_id(custom=i)
                self.assertRaises(argparse.ArgumentError, self.parse, False)
        for i in const.VALID_BANK_IDS:
            with self.subTest(i=i):
                args.set_bank_id(i)
                self.assertTrue(self.parse())

    def test_cli_alloc_columns(self):
        args.set_all_required()
        for i in const.INVALID_ALLOC_COLUMNS:
            with self.subTest(i=i):
                args.set_alloc_columns(custom=i)
                self.assertRaises(argparse.ArgumentError, self.parse, False)
        for i in const.VALID_ALLOC_COLUMNS:
            with self.subTest(i=i):
                args.set_alloc_columns(i)
                self.assertTrue(self.parse())

    def test_cli_ofx_file(self):
        args.set_all_required()
        for i in const.MISSING_OFX_FILES:
            with self.subTest(i=i):
                args.set_ofx_file(i)
                self.assertRaises(argparse.ArgumentError, self.parse, False)
        for i in const.VALID_OFX_FILES:
            with self.subTest(i=i):
                args.set_ofx_file(i)
                self.assertTrue(self.parse())

    def test_cli_statement_date(self):
        args.set_all_required()
        for i in const.INVALID_STATEMENT_DATES:
            with self.subTest(i=i):
                args.set_statement_date(custom=i)
                self.assertRaises(argparse.ArgumentError, self.parse, False)
        for i in const.VALID_STATEMENT_DATES:
            with self.subTest(i=i):
                args.set_statement_date(i)
                self.assertTrue(self.parse())

    def test_cli_config_file(self):
        args.set_all_required()
        with self.subTest(i=None):
            args.set_config_file(None)
            self.assertRaises(argparse.ArgumentError, self.parse, False)
            self.setUp()

        for i in const.MISSING_CONFIG_FILES[1:] + const.INVALID_CONFIG_FILES:
            with self.subTest(i=i):
                args.set_config_file(i)
                console_args = self.parse()
                self.assertIsInstance(console_args.config_file, Path)
                self.setUp()

        with self.subTest():
            args.set_all_required()
            args.set_config_file(const.VALID_CONFIG)
            console_args = self.parse()
            self.assertIsInstance(console_args.config_file, Path)
