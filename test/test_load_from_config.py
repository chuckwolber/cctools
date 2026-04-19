# SPDX-License-Identifier: MIT

import argparse
import sys
import unittest

from . import args
from . import const
from ccct.config.args import CCConsoleArgs
from ccct.config.config import CCConfig

from pathlib import Path

class TestLoadFromConfig(unittest.TestCase):
    argv = sys.argv

    def setUp(self):
        sys.argv = sys.argv[0:1]

    def tearDown(self):
        sys.argv = self.argv

    def parse(self):
        return CCConsoleArgs().parse()

    def test__load_from_config_missing(self):
        for i in const.MISSING_CONFIG_FILES:
            with self.subTest(i=i):
                args.set_all_required()
                config = CCConfig(self.parse(), default_config_file=i)
                self.assertFalse(config.load_from_config())

                # Reset to prevent _parse_args() from seeing an invalid config.
                self.setUp()

    def test__load_from_config_invalid(self):
        for i in const.INVALID_CONFIG_FILES:
            with self.subTest(i=i):
                args.set_all_required()
                config = CCConfig(self.parse(), default_config_file=i)
                self.assertRaises(argparse.ArgumentTypeError, config.load_from_config)

                # Reset to prevent _parse_args() from seeing an invalid config.
                self.setUp()

    def test__load_from_config_valid(self):
        args.set_all_required()

        # Set CLI values that differ from config file values.
        args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
        args.set_bank_id(const.VALID_BANK_IDS[0])
        args.set_document_id(const.VALID_DOCUMENT_ID)

        config = CCConfig(self.parse(), default_config_file=const.VALID_CONFIG)
        self.assertTrue(config.load_from_config())

        # Ensure CLI values override config file values.
        self.assertTrue(config.credential_dir == Path(const.VALID_CREDENTIAL_DIRS[0]).expanduser())
        self.assertTrue(config.bank_id == const.VALID_BANK_IDS[0])
        self.assertTrue(config.document_id == const.VALID_DOCUMENT_ID)
        self.assertTrue(config.alloc_columns == ["ap", "pc", "af"])
        self.assertTrue(config.alloc_columns_map["ap"] == "Amazon Purchases")

        # Belt and suspenders to potentially catch changes to assets.
        self.assertFalse(config.credential_dir == Path("~/.google").expanduser())
        self.assertFalse(config.bank_id == "314074269")
        self.assertFalse(config.document_id == "2CZrPH3M-Lg-TmD5luXu7loG3svABgfGP23txXbar7dg")
