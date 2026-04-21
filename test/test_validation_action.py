# SPDX-License-Identifier: MIT

import argparse
import os
import unittest

from . import const
from ccct.config.args import CCConsoleArgs
from ccct.config.file import CCConfigFile

class TestValidationAction(unittest.TestCase):
    def test__is_valid_credential_dir(self):
        for i in const.INVALID_CREDENTIAL_DIRS:
            with self.subTest(i=i):
                self.assertRaises(argparse.ArgumentTypeError, CCConsoleArgs._is_valid_credential_dir, i)
        for i in const.VALID_CREDENTIAL_DIRS:
            with self.subTest(i=i):
                self.assertTrue(os.path.exists(CCConsoleArgs._is_valid_credential_dir(i)))

    def test__is_valid_bank_id(self):
        for i in const.INVALID_BANK_ID_STRINGS:
            with self.subTest(i=i):
                self.assertRaises(argparse.ArgumentTypeError, CCConsoleArgs._is_valid_bank_id, i)
        for i in const.INVALID_BANK_ID_NUMBERS:
            with self.subTest(i=i):
                self.assertRaises(argparse.ArgumentTypeError, CCConsoleArgs._is_valid_bank_id, i)
        for i in const.VALID_BANK_IDS:
            with self.subTest(i=i):
                self.assertTrue(CCConsoleArgs._is_valid_bank_id(i) == i)

    def test__set_alloc_columns(self):
        for i in const.INVALID_ALLOC_COLUMNS:
            with self.subTest(i=i):
                self.assertRaises(argparse.ArgumentTypeError, CCConsoleArgs._set_alloc_columns, i)
        for i in const.VALID_ALLOC_COLUMNS:
            with self.subTest(i=i):
                self.assertTrue(CCConsoleArgs._set_alloc_columns(i) == i.split(":"))

    def test__is_valid_ofx_file(self):
        for i in const.MISSING_OFX_FILES:
            with self.subTest(i=i):
                self.assertRaises(argparse.ArgumentTypeError, CCConsoleArgs._is_valid_ofx_file, i)
        for i in const.VALID_OFX_FILES:
            with self.subTest(i=i):
                self.assertTrue(CCConsoleArgs._is_valid_ofx_file(i))

    def test__is_valid_statement_date(self):
        for i in const.INVALID_STATEMENT_DATE_STRINGS:
            with self.subTest(i=i):
                self.assertRaises(argparse.ArgumentTypeError, CCConsoleArgs._is_valid_statement_date, i)
        for i in const.INVALID_STATEMENT_DATE_VALUES:
            with self.subTest(i=i):
                self.assertRaises(ValueError, CCConsoleArgs._is_valid_statement_date, i)
        for i in const.VALID_STATEMENT_DATES:
            with self.subTest(i=i):
                self.assertTrue(CCConsoleArgs._is_valid_statement_date(i))

    def test__is_valid_config_file(self):
        with self.subTest(i=None):
            self.assertRaises(argparse.ArgumentTypeError, CCConsoleArgs._is_valid_config_file, None)
        for i in const.MISSING_CONFIG_FILES[1:] + const.INVALID_CONFIG_FILES + [const.VALID_CONFIG]:
            with self.subTest(i=i):
                self.assertTrue(CCConsoleArgs._is_valid_config_file(i))

    def test_config_file_load(self):
        with self.subTest(i=None):
            self.assertRaises(TypeError, CCConfigFile, None)
        for i in const.MISSING_CONFIG_FILES[1:]:
            with self.subTest(i=i):
                self.assertRaises(argparse.ArgumentTypeError, CCConfigFile, i)
        for i in const.INVALID_CONFIG_FILES:
            with self.subTest(i=i):
                self.assertRaises(argparse.ArgumentTypeError, CCConfigFile, i)
        with self.subTest():
            self.assertIsInstance(CCConfigFile(const.VALID_CONFIG).to_dict(), dict)
        for i in const.VALID_SCHEMA_FILES:
            with self.subTest(i=i):
                config = CCConfigFile(const.VALID_CONFIG, schema_file=i)
                config_dict = config.to_dict()
                self.assertTrue(config_dict["credential_dir"] == "~/.google")
                self.assertTrue(config_dict["bank_id"] == 314074269)
                self.assertTrue(config_dict["document_id"] == "2CZrPH3M-Lg-TmD5luXu7loG3svABgfGP23txXbar7dg")
                self.assertTrue(config.alloc_columns == ["ap", "pc", "af"])
                self.assertTrue(config.alloc_columns_map["ap"] == "Amazon Purchases")
                self.assertTrue(config.alloc_columns_map["pc"] == "Petcare")
                self.assertTrue(config.alloc_columns_map["af"] == "Auto Fuel")
