# SPDX-License-Identifier: MIT

import argparse
import sys
import unittest

from . import args
from . import const
from .. import ccct

from pathlib import Path

class TestFXFile(unittest.TestCase):
    argv = sys.argv

    def setUp(self):
        sys.argv = sys.argv[0:1]
        ccct._args = None
        ccct._ofx = None

    def tearDown(self):
        sys.argv = self.argv

    def test__parse_ofx_file(self):
        for i in const.VALID_OFX_FILES:
            with self.subTest(i=i):
                args.set_ofx_file(i)
                args.set_statement_date(const.VALID_STATEMENT_DATES[0])
                args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
                args.set_bank_id("314074269")
                args.set_alloc_columns(const.VALID_ALLOC_COLUMNS[0])
                self.assertTrue(ccct._resolve_config(default_config_file=None))
                self.assertTrue(ccct._parse_ofx_file())
                self.setUp()

    def test__parse_ofx_file_invalid_bank_id(self):
        args.set_ofx_file(const.ASSETS_DIR + "/export.valid.qfx")
        args.set_statement_date(const.VALID_STATEMENT_DATES[0])
        args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
        args.set_bank_id("325081403")
        args.set_alloc_columns(const.VALID_ALLOC_COLUMNS[0])
        self.assertTrue(ccct._resolve_config(default_config_file=None))
        self.assertRaises(Exception, ccct._parse_ofx_file)

    def test__parse_ofx_file_invalid_accttype(self):
        args.set_ofx_file(const.ASSETS_DIR + "/export.invalid-1.qfx")
        args.set_statement_date(const.VALID_STATEMENT_DATES[0])
        args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
        args.set_bank_id("314074269")
        args.set_alloc_columns(const.VALID_ALLOC_COLUMNS[0])
        self.assertTrue(ccct._resolve_config(default_config_file=None))
        self.assertRaises(Exception, ccct._parse_ofx_file)

    def test__parse_ofx_file_invalid_accttype(self):
        args.set_ofx_file(const.ASSETS_DIR + "/export.invalid-2.qfx")
        args.set_statement_date(const.VALID_STATEMENT_DATES[0])
        args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
        args.set_bank_id("314074269")
        args.set_alloc_columns(const.VALID_ALLOC_COLUMNS[0])
        self.assertTrue(ccct._resolve_config(default_config_file=None))
        self.assertRaises(Exception, ccct._parse_ofx_file)

    def test__parse_ofx_file_invalid_format(self):
        args.set_ofx_file(const.ASSETS_DIR + "/export.invalid-3.qfx")
        args.set_statement_date(const.VALID_STATEMENT_DATES[0])
        args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
        args.set_bank_id("314074269")
        args.set_alloc_columns(const.VALID_ALLOC_COLUMNS[0])
        self.assertTrue(ccct._resolve_config(default_config_file=None))
        self.assertRaises(Exception, ccct._parse_ofx_file)

    def test__parse_ofx_file_missing_fields(self):
        args.set_all_required()
        args.set_ofx_file(const.ASSETS_DIR + "/export.invalid-4.qfx")
        args.set_config_file(const.VALID_CONFIG)
        self.assertTrue(ccct._resolve_config(None))
        self.assertRaises(ValueError, ccct._parse_ofx_file)