# SPDX-License-Identifier: MIT

import argparse
import json
import sys
import tempfile
import unittest

from . import args
from . import const
from ccct.config.args import CCConsoleArgs
from ccct.config.config import CCConfig
from ccct.config.file import CCConfigFile

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
        with self.subTest(i=None):
            self.assertRaises(TypeError, CCConfigFile, None)
        for i in const.MISSING_CONFIG_FILES[1:]:
            with self.subTest(i=i):
                self.assertRaises(argparse.ArgumentTypeError, CCConfigFile, i)

    def test__load_from_config_invalid(self):
        for i in const.INVALID_CONFIG_FILES:
            with self.subTest(i=i):
                self.assertRaises(argparse.ArgumentTypeError, CCConfigFile, i)

    def test__load_from_config_valid(self):
        args.set_all_required()

        # Set CLI values that differ from config file values.
        args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
        args.set_bank_id(const.VALID_BANK_IDS[0])
        args.set_document_id(const.VALID_DOCUMENT_ID)

        config = CCConfig(self.parse(), file=CCConfigFile(const.VALID_CONFIG))
        self.assertIs(config.resolve(), config)

        # Ensure CLI scalar values override config file values, while file
        # columns remain when CLI columns are omitted.
        self.assertTrue(config.credential_dir == Path(const.VALID_CREDENTIAL_DIRS[0]).expanduser())
        self.assertTrue(config.bank_id == const.VALID_BANK_IDS[0])
        self.assertTrue(config.document_id == const.VALID_DOCUMENT_ID)
        self.assertTrue(config.alloc_columns == ["ap", "pc", "af"])
        self.assertTrue(config.alloc_columns_map["ap"] == "Amazon Purchases")

        # Belt and suspenders to potentially catch changes to assets.
        self.assertFalse(config.credential_dir == Path("~/.google").expanduser())
        self.assertFalse(config.bank_id == "314074269")
        self.assertFalse(config.document_id == "2CZrPH3M-Lg-TmD5luXu7loG3svABgfGP23txXbar7dg")

    def test__load_from_config_cli_alloc_columns_clear_file_map(self):
        args.set_all_required()
        args.set_alloc_columns(const.VALID_ALLOC_COLUMNS[0])

        config = CCConfig(self.parse(), file=CCConfigFile(const.VALID_CONFIG)).resolve()

        self.assertTrue(config.alloc_columns == const.VALID_ALLOC_COLUMNS[0].split(":"))
        self.assertIsNone(config.alloc_columns_map)

    def test__load_from_config_without_alloc_columns(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
            json.dump({
                "credential_dir": const.VALID_CREDENTIAL_DIRS[0],
                "bank_id": int(const.VALID_BANK_IDS[0]),
                "document_id": const.VALID_DOCUMENT_ID,
            }, f)
            f.flush()

            args.set_all_required()
            args.set_alloc_columns(const.VALID_ALLOC_COLUMNS[0])
            config = CCConfig(self.parse(), file=CCConfigFile(f.name)).resolve()

        self.assertTrue(config.credential_dir == Path(const.VALID_CREDENTIAL_DIRS[0]).expanduser())
        self.assertTrue(config.bank_id == const.VALID_BANK_IDS[0])
        self.assertTrue(config.document_id == const.VALID_DOCUMENT_ID)
        self.assertTrue(config.alloc_columns == const.VALID_ALLOC_COLUMNS[0].split(":"))
        self.assertIsNone(config.alloc_columns_map)
