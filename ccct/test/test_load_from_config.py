# SPDX-License-Identifier: MIT

import argparse
import sys
import unittest

from . import args
from . import const
from .. import ccct

from pathlib import Path

class TestLoadFromConfig(unittest.TestCase):
    argv = sys.argv

    def setUp(self):
        sys.argv = sys.argv[0:1]
        ccct._args = None

    def tearDown(self):
        sys.argv = self.argv

    def test__load_from_config_missing(self):
        for i in const.MISSING_CONFIG_FILES:
            with self.subTest(i=i):
                args.set_all_required()
                self.assertTrue(ccct._parse_args())

                # Set config file after _parse_args() so _load_from_config()
                # handles the config file parsing.
                args.set_config_file(i)
                self.assertFalse(ccct._load_from_config(i))

                # Reset to prevent _parse_args() from seeing an invalid config.
                self.setUp()

    def test__load_from_config_invalid(self):
        for i in const.INVALID_CONFIG_FILES:
            with self.subTest(i=i):
                args.set_all_required()
                self.assertTrue(ccct._parse_args())

                # Set config file after _parse_args() so _load_from_config()
                # handles the config file parsing.
                args.set_config_file(i)
                self.assertRaises(argparse.ArgumentTypeError, ccct._load_from_config, i)

                # Reset to prevent _parse_args() from seeing an invalid config.
                self.setUp()

    def test__load_from_config_valid(self):
        args.set_all_required()

        # Set CLI values that differ from config file values.
        args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
        args.set_bank_id(const.VALID_BANK_IDS[0])
        args.set_document_id(const.VALID_DOCUMENT_ID)

        self.assertTrue(ccct._parse_args())
        self.assertTrue(ccct._load_from_config(const.VALID_CONFIG))

        # Ensure CLI values override config file values.
        self.assertTrue(ccct._args.credential_dir == Path(const.VALID_CREDENTIAL_DIRS[0]).expanduser())
        self.assertTrue(ccct._args.bank_id == const.VALID_BANK_IDS[0])
        self.assertTrue(ccct._args.document_id == const.VALID_DOCUMENT_ID)

        # Belt and suspenders to potentially catch changes to assets.
        self.assertFalse(ccct._args.credential_dir == Path("~/.google").expanduser())
        self.assertFalse(ccct._args.bank_id == "314074269")
        self.assertFalse(ccct._args.document_id == "2CZrPH3M-Lg-TmD5luXu7loG3svABgfGP23txXbar7dg")
