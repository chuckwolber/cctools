# SPDX-License-Identifier: MIT

import argparse
import os.path

from ccct.config.args import CCConsoleArgs
from ccct.config.args import DEFAULT_CONFIG_FILE


class CCConfig:
    """Resolved ccct configuration from CLI and config-file values."""

    REQUIRED = (
        ("ofx_file", "Error: OFX file unknown!"),
        ("statement_date", "Error: Statement date unknown!"),
        ("credential_dir", "Error: Credential directory unknown!"),
        ("bank_id", "Error: Bank ID unknown!"),
        ("alloc_columns", "Error: Allocation columns unknown!"),
    )

    def __init__(self, console_args: CCConsoleArgs = None, default_config_file=DEFAULT_CONFIG_FILE):
        self.default_config_file = default_config_file
        self.console_args = console_args
        if self.console_args is None:
            self.console_args = CCConsoleArgs().parse()

        for arg_name, value in self.console_args.to_dict().items():
            setattr(self, arg_name, value)

        self.alloc_columns_map = getattr(self.console_args, "alloc_columns_map", None)

    @classmethod
    def from_console(cls, exit_on_error=True, default_config_file=DEFAULT_CONFIG_FILE):
        return cls(
            console_args=CCConsoleArgs(exit_on_error=exit_on_error).parse(),
            default_config_file=default_config_file,
        )

    def load_from_config(self):
        config = self.config_file
        if not isinstance(config, dict):
            if self.default_config_file is not None and os.path.exists(self.default_config_file):
                config = CCConsoleArgs._is_valid_config_file(str(self.default_config_file))
            else:
                return False

        self.config_file = config
        self.__apply_config(config)
        return True

    def resolve(self):
        self.load_from_config()
        self.__validate_required()
        return self

    def __apply_config(self, config):
        if self.credential_dir is None and "credential_dir" in config:
            self.credential_dir = CCConsoleArgs._is_valid_credential_dir(config["credential_dir"])

        if self.bank_id is None and "bank_id" in config:
            self.bank_id = CCConsoleArgs._is_valid_bank_id(str(config["bank_id"]))

        if self.document_id is None and "document_id" in config:
            self.document_id = config["document_id"]

        if self.alloc_columns is None and "alloc_columns" in config:
            self.alloc_columns = []
            self.alloc_columns_map = {}
            for c in config["alloc_columns"]:
                self.alloc_columns.append(c["short"])
                self.alloc_columns_map[c["short"]] = c["long"]

    def __validate_required(self):
        for attr, error_msg in self.REQUIRED:
            if getattr(self, attr) is None:
                raise argparse.ArgumentTypeError(error_msg)
