# SPDX-License-Identifier: MIT

import argparse
import os
import unittest

from . import const
from .. import ccct

class TestValidationAction(unittest.TestCase):
    def test__is_valid_credential_dir(self):
        for i in const.INVALID_CREDENTIAL_DIRS:
            with self.subTest(i=i):
                self.assertRaises(argparse.ArgumentTypeError, ccct._is_valid_credential_dir, i)
        for i in const.VALID_CREDENTIAL_DIRS:
            with self.subTest(i=i):
                self.assertTrue(os.path.exists(ccct._is_valid_credential_dir(i)))

    def test__is_valid_bank_id(self):
        for i in const.INVALID_BANK_ID_STRINGS:
            with self.subTest(i=i):
                self.assertRaises(argparse.ArgumentTypeError, ccct._is_valid_bank_id, i)
        for i in const.INVALID_BANK_ID_NUMBERS:
            with self.subTest(i=i):
                self.assertRaises(argparse.ArgumentTypeError, ccct._is_valid_bank_id, i)
        for i in const.VALID_BANK_IDS:
            with self.subTest(i=i):
                self.assertTrue(ccct._is_valid_bank_id(i) == i)

    def test__set_alloc_columns(self):
        for i in const.INVALID_ALLOC_COLUMNS:
            with self.subTest(i=i):
                self.assertRaises(argparse.ArgumentTypeError, ccct._set_alloc_columns, i)
        for i in const.VALID_ALLOC_COLUMNS:
            with self.subTest(i=i):
                self.assertTrue(ccct._set_alloc_columns(i) == i.split(":"))

    def test__is_valid_fx_file(self):
        for i in const.MISSING_FX_FILES:
            with self.subTest(i=i):
                self.assertRaises(argparse.ArgumentTypeError, ccct._is_valid_fx_file, i)
        for i in const.VALID_FX_FILES:
            with self.subTest(i=i):
                self.assertTrue(ccct._is_valid_fx_file(i))

    def test__is_valid_statement_date(self):
        for i in const.INVALID_STATEMENT_DATE_STRINGS:
            with self.subTest(i=i):
                self.assertRaises(argparse.ArgumentTypeError, ccct._is_valid_statement_date, i)
        for i in const.INVALID_STATEMENT_DATE_VALUES:
            with self.subTest(i=i):
                self.assertRaises(ValueError, ccct._is_valid_statement_date, i)
        for i in const.VALID_STATEMENT_DATES:
            with self.subTest(i=i):
                self.assertTrue(ccct._is_valid_statement_date(i))

    def test__is_valid_config_file(self):
        for i in const.MISSING_CONFIG_FILES:
            with self.subTest(i=i):
                self.assertRaises(argparse.ArgumentTypeError, ccct._is_valid_config_file, i)
        for i in const.INVALID_CONFIG_FILES:
            with self.subTest(i=i):
                self.assertRaises(argparse.ArgumentTypeError, ccct._is_valid_config_file, i)
        with self.subTest():
            self.assertIsInstance(ccct._is_valid_config_file(const.VALID_CONFIG), dict)
        for i in const.VALID_SCHEMA_FILES:
            with self.subTest(i=i):
                config = ccct._is_valid_config_file(const.VALID_CONFIG, i)
                self.assertTrue(config["credential_dir"] == "~/.google")
                self.assertTrue(config["bank_id"] == 314074269)
                self.assertTrue(config["document_id"] == "2CZrPH3M-Lg-TmD5luXu7loG3svABgfGP23txXbar7dg")
                self.assertTrue(config["alloc_columns"][0]["short"] == "ap")
                self.assertTrue(config["alloc_columns"][0]["long"] == "Amazon Purchases")
                self.assertTrue(config["alloc_columns"][1]["short"] == "pc")
                self.assertTrue(config["alloc_columns"][1]["long"] == "Petcare")
                self.assertTrue(config["alloc_columns"][2]["short"] == "af")
                self.assertTrue(config["alloc_columns"][2]["long"] == "Auto Fuel")

