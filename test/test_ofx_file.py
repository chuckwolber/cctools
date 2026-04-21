# SPDX-License-Identifier: MIT

import sys
import unittest

from . import args
from . import const
from ccct import ccct
from ccct.config.args import CCConsoleArgs
from ccct.config.config import CCConfig
from ccct.config.file import CCConfigFile

class TestFXFile(unittest.TestCase):
    argv = sys.argv

    def setUp(self):
        sys.argv = sys.argv[0:1]

    def tearDown(self):
        sys.argv = self.argv

    def _categorizer(self):
        console_args = CCConsoleArgs().parse()
        config_file = None
        if console_args.config_file is not None:
            config_file = CCConfigFile(console_args.config_file)
        config = CCConfig(args=console_args, file=config_file)
        return ccct.CCTransactionCategorizer(config)

    def test__parse_ofx_file(self):
        for i in const.VALID_OFX_FILES:
            with self.subTest(i=i):
                args.set_ofx_file(i)
                args.set_statement_date(const.VALID_STATEMENT_DATES[0])
                args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
                args.set_bank_id("314074269")
                args.set_alloc_columns(const.VALID_ALLOC_COLUMNS[0])
                categorizer = self._categorizer()
                self.assertTrue(categorizer._parse_ofx_file())
                self.setUp()

    def test__parse_ofx_file_invalid_bank_id(self):
        args.set_ofx_file(const.ASSETS_DIR + "/export.valid.qfx")
        args.set_statement_date(const.VALID_STATEMENT_DATES[0])
        args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
        args.set_bank_id("325081403")
        args.set_alloc_columns(const.VALID_ALLOC_COLUMNS[0])
        categorizer = self._categorizer()
        self.assertRaises(Exception, categorizer._parse_ofx_file)

    def test__parse_ofx_file_invalid_accttype(self):
        args.set_ofx_file(const.ASSETS_DIR + "/export.invalid-1.qfx")
        args.set_statement_date(const.VALID_STATEMENT_DATES[0])
        args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
        args.set_bank_id("314074269")
        args.set_alloc_columns(const.VALID_ALLOC_COLUMNS[0])
        categorizer = self._categorizer()
        self.assertRaises(Exception, categorizer._parse_ofx_file)

    def test__parse_ofx_file_invalid_accttype(self):
        args.set_ofx_file(const.ASSETS_DIR + "/export.invalid-2.qfx")
        args.set_statement_date(const.VALID_STATEMENT_DATES[0])
        args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
        args.set_bank_id("314074269")
        args.set_alloc_columns(const.VALID_ALLOC_COLUMNS[0])
        categorizer = self._categorizer()
        self.assertRaises(Exception, categorizer._parse_ofx_file)

    def test__parse_ofx_file_invalid_format(self):
        args.set_ofx_file(const.ASSETS_DIR + "/export.invalid-3.qfx")
        args.set_statement_date(const.VALID_STATEMENT_DATES[0])
        args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
        args.set_bank_id("314074269")
        args.set_alloc_columns(const.VALID_ALLOC_COLUMNS[0])
        categorizer = self._categorizer()
        self.assertRaises(Exception, categorizer._parse_ofx_file)

    def test__parse_ofx_file_missing_fields(self):
        args.set_all_required()
        args.set_ofx_file(const.ASSETS_DIR + "/export.invalid-4.qfx")
        args.set_config_file(const.VALID_CONFIG)
        categorizer = self._categorizer()
        self.assertRaises(ValueError, categorizer._parse_ofx_file)
