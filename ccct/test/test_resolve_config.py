# SPDX-License-Identifier: MIT

import argparse
import sys
import unittest

from . import args
from . import const
from .. import ccct

class TestResolveConfig(unittest.TestCase):
    argv = sys.argv

    def setUp(self):
        sys.argv = sys.argv[0:1]
        ccct.args = None

    def tearDown(self):
        sys.argv = self.argv

    def test__resolve_config_all_missing(self):
        self.assertRaises(argparse.ArgumentError, ccct._resolve_config, False)

    def test__resolve_config_only_required(self):
        args.set_all_required()
        self.assertRaises(argparse.ArgumentTypeError, ccct._resolve_config, default_config_file=None)

    def test__resolve_config_add_credential_dir(self):
        args.set_all_required()
        args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
        self.assertRaises(argparse.ArgumentTypeError, ccct._resolve_config, default_config_file=None)

    def test__resolve_config_add_bank_id(self):
        args.set_all_required()
        args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
        args.set_bank_id(const.VALID_BANK_IDS[0])
        self.assertRaises(argparse.ArgumentTypeError, ccct._resolve_config, default_config_file=None)

    def test__resolve_config_add_alloc_columns(self):
        args.set_all_required()
        args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
        args.set_bank_id(const.VALID_BANK_IDS[0])
        args.set_alloc_columns(const.VALID_ALLOC_COLUMNS[0])
        self.assertTrue(ccct._resolve_config(None))
