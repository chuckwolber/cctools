# SPDX-License-Identifier: MIT

import argparse
import sys
import unittest

from . import args
from . import const
from .. import ccct

from pathlib import Path

class TestCommandLineInterface(unittest.TestCase):
    argv = sys.argv

    def setUp(self):
        sys.argv = sys.argv[0:1]

    def tearDown(self):
        sys.argv = self.argv

    def test_cli_none(self):
        self.assertRaises(argparse.ArgumentError, ccct._parse_args, False)

    def test_cli_required(self):
        args.set_all_required()
        self.assertTrue(ccct._parse_args())

    def test_cli_credential_dir(self):
        args.set_all_required()
        for i in const.INVALID_CREDENTIAL_DIRS:
            with self.subTest(i=i):
                args.set_credential_dir(i)
                self.assertRaises(argparse.ArgumentError, ccct._parse_args, False)
        for i in const.VALID_CREDENTIAL_DIRS:
            with self.subTest(i=i):
                args.set_credential_dir(i)
                self.assertTrue(ccct._parse_args())
                self.assertIsInstance(ccct.args.credential_dir, Path)

    def test_cli_bank_id(self):
        args.set_all_required()
        for i in const.INVALID_BANK_IDS:
            with self.subTest(i=i):
                args.set_bank_id(custom=i)
                self.assertRaises(argparse.ArgumentError, ccct._parse_args, False)
        for i in const.VALID_BANK_IDS:
            with self.subTest(i=i):
                args.set_bank_id(i)
                self.assertTrue(ccct._parse_args())

    def test_cli_alloc_columns(self):
        args.set_all_required()
        for i in const.INVALID_ALLOC_COLUMNS:
            with self.subTest(i=i):
                args.set_alloc_columns(custom=i)
                self.assertRaises(argparse.ArgumentError, ccct._parse_args, False)
        for i in const.VALID_ALLOC_COLUMNS:
            with self.subTest(i=i):
                args.set_alloc_columns(i)
                self.assertTrue(ccct._parse_args())

    def test_cli_ofx_file(self):
        args.set_all_required()
        for i in const.MISSING_OFX_FILES:
            with self.subTest(i=i):
                args.set_ofx_file(i)
                self.assertRaises(argparse.ArgumentError, ccct._parse_args, False)
        for i in const.VALID_OFX_FILES:
            with self.subTest(i=i):
                args.set_ofx_file(i)
                self.assertTrue(ccct._parse_args())

    def test_cli_statement_date(self):
        args.set_all_required()
        for i in const.INVALID_STATEMENT_DATES:
            with self.subTest(i=i):
                args.set_statement_date(custom=i)
                self.assertRaises(argparse.ArgumentError, ccct._parse_args, False)
        for i in const.VALID_STATEMENT_DATES:
            with self.subTest(i=i):
                args.set_statement_date(i)
                self.assertTrue(ccct._parse_args())

    def test_cli_config_file(self):
        args.set_all_required()
        for i in const.INVALID_CONFIGS:
            with self.subTest(i=i):
                args.set_config_file(i)
                self.assertRaises(argparse.ArgumentError, ccct._parse_args, False)
        with self.subTest():
            args.set_config_file(const.VALID_CONFIG)
            self.assertTrue(ccct._parse_args())
