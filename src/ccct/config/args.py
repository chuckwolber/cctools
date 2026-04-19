# SPDX-License-Identifier: MIT

import argparse
import json
import os.path
import re

from datetime import datetime
from importlib.resources import files
from pathlib import Path

from jsonschema import validate
from jsonschema.exceptions import ValidationError

DEFAULT_CONFIG_FILE = Path("~/.config/cctools/ccct.config.json").expanduser()
SCHEMA_FILE = files("ccct.config").joinpath("ccct.config.schema.json")


class CCConsoleArgs:
    """Parse and validate command line arguments for the ccct console."""

    def __init__(self, exit_on_error=True):
        self._parser = argparse.ArgumentParser(
            description="Categorize Credit Card Transactions",
            exit_on_error=exit_on_error)
        self._add_arguments()

    @staticmethod
    def _is_valid_credential_dir(credential_dir):
        try:
            credential_dir = Path(credential_dir).expanduser()
        except TypeError:
            raise argparse.ArgumentTypeError("ERROR: Credential dir missing!")
        if not os.path.exists(credential_dir):
            raise argparse.ArgumentTypeError(f"ERROR: Credential directory not found: {(credential_dir)}")
        return credential_dir

    @staticmethod
    def _is_valid_bank_id(bank_id):
        error_msg = "ERROR: Invalid bank ID {}".format(bank_id)
        try:
            if not re.match('^[0-9]{9}$', bank_id):
                raise argparse.ArgumentTypeError(error_msg)
        except TypeError:
            raise argparse.ArgumentTypeError("ERROR: Bank ID missing!")
        if sum(w * int(n) for w, n in zip([3, 7, 1] * 3, bank_id)) % 10 != 0:
            raise argparse.ArgumentTypeError(error_msg)
        return bank_id

    @staticmethod
    def _set_alloc_columns(alloc_columns):
        try:
            cols = alloc_columns.split(":")
        except AttributeError:
            raise argparse.ArgumentTypeError("ERROR: alloc columns string missing!")
        if len(cols) <= 1:
            raise argparse.ArgumentTypeError("ERROR: Two or more allocation columns are required.")
        return cols

    @staticmethod
    def _is_valid_ofx_file(ofx_file):
        try:
            ofx_file = Path(ofx_file).expanduser()
        except TypeError:
            raise argparse.ArgumentTypeError("ERROR: OFX file argument missing!")
        if not os.path.exists(ofx_file):
            raise argparse.ArgumentTypeError(f"ERROR: OFX file not found: {(ofx_file)}")
        return ofx_file

    @staticmethod
    def _is_valid_statement_date(statement_date):
        error_msg = "ERROR: Invalid statement date {}".format(statement_date)
        try:
            if not re.match('^[0-9]{8}$', statement_date):
                raise argparse.ArgumentTypeError(error_msg)
        except TypeError:
            raise argparse.ArgumentTypeError("ERROR: Statement date missing!")
        if not datetime.strptime(statement_date, '%Y%m%d'):
            raise argparse.ArgumentTypeError(error_msg)
        return statement_date

    @staticmethod
    def _is_valid_config_file(config_file, schema_file=SCHEMA_FILE):
        error_msg = "ERROR: Invalid config file {}".format(config_file)
        try:
            config_file = Path(config_file).expanduser()
            with open(schema_file, "r") as json_schema:
                schema = json.load(json_schema)
            with open(config_file, "r") as json_config:
                config = json.load(json_config)
        except json.decoder.JSONDecodeError as e:
            raise argparse.ArgumentTypeError(str(e))
        except FileNotFoundError as e:
            raise argparse.ArgumentTypeError(str(e))
        except TypeError:
            raise argparse.ArgumentTypeError("ERROR: Invalid config file!")

        try:
            validate(instance=config, schema=schema)
        except ValidationError as e:
            raise argparse.ArgumentTypeError(error_msg + "\n" + str(e))
        return config

    def parse(self, args=None):
        namespace = self._parser.parse_args(args=args)
        for key, value in vars(namespace).items():
            setattr(self, key, value)
        return self

    def to_dict(self):
        return {
            action.dest: getattr(self, action.dest, None)
            for action in self._parser._actions
            if action.dest not in (argparse.SUPPRESS, "help")
        }

    def _add_arguments(self):
        self._parser.add_argument('--credential-dir',
                                  required=False,
                                  type=self._is_valid_credential_dir,
                                  help="Google API credential directory.")
        self._parser.add_argument('--bank-id',
                                  required=False,
                                  type=self._is_valid_bank_id,
                                  help="The bank routing number. Used to validate the OFX file.")
        self._parser.add_argument('--document-id',
                                  required=False,
                                  default=None,
                                  help="The Google document ID to write transactions. A new spreadsheet is created if this is omitted.")
        self._parser.add_argument('--alloc-columns',
                                  required=False,
                                  type=self._set_alloc_columns,
                                  help="Colon delimited list of categories to allocate transactions.")
        self._parser.add_argument('--ofx-file',
                                  required=False,
                                  type=self._is_valid_ofx_file,
                                  help="The OFX file to parse for transactions.")
        self._parser.add_argument('--statement-date',
                                  required=False,
                                  type=self._is_valid_statement_date,
                                  help="This is the worksheet that accumulates transactions.")
        self._parser.add_argument('--config-file',
                                  required=False,
                                  default=DEFAULT_CONFIG_FILE,
                                  type=self._is_valid_config_file,
                                  help="JSON formatted config file. See docs for details.")
