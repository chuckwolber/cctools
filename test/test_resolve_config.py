# SPDX-License-Identifier: MIT

import argparse
import sys
import unittest

from . import args
from . import const
from ccct import ccct
from ccct.config.args import CCConsoleArgs
from ccct.config.config import CCConfig

class TestResolveConfig(unittest.TestCase):
    argv = sys.argv

    def setUp(self):
        sys.argv = sys.argv[0:1]

    def tearDown(self):
        sys.argv = self.argv

    def _config(self, exit_on_error=True):
        return CCConfig(args=CCConsoleArgs(exit_on_error=exit_on_error).parse())

    def test__resolve_config_all_missing(self):
        config = self._config(exit_on_error=False)
        self.assertRaises(argparse.ArgumentTypeError, config.resolve)

    def test__resolve_config_only_required(self):
        args.set_all_required()
        config = self._config()
        self.assertRaises(argparse.ArgumentTypeError, config.resolve)

    def test__resolve_config_add_credential_dir(self):
        args.set_all_required()
        args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
        config = self._config()
        self.assertRaises(argparse.ArgumentTypeError, config.resolve)

    def test__resolve_config_add_bank_id(self):
        args.set_all_required()
        args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
        args.set_bank_id(const.VALID_BANK_IDS[0])
        config = self._config()
        self.assertRaises(argparse.ArgumentTypeError, config.resolve)

    def test__resolve_config_add_alloc_columns(self):
        args.set_all_required()
        args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
        args.set_bank_id(const.VALID_BANK_IDS[0])
        args.set_alloc_columns(const.VALID_ALLOC_COLUMNS[0])
        config = self._config().resolve()
        categorizer = ccct.CCTransactionCategorizer(config)
        self.assertIs(categorizer._config, config)

    def test__resolve_config_idempotent(self):
        args.set_all_required()
        args.set_credential_dir(const.VALID_CREDENTIAL_DIRS[0])
        args.set_bank_id(const.VALID_BANK_IDS[0])
        args.set_alloc_columns(const.VALID_ALLOC_COLUMNS[0])
        config = self._config()
        self.assertIs(config.resolve(), config)
        self.assertIs(config.resolve(), config)
