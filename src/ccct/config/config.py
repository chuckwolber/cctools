# SPDX-License-Identifier: MIT

import argparse
from typing import Self

from ccct.config.args import CCConsoleArgs
from ccct.config.file import CCConfigFile
from ccct.config.types import CCConfigType

class CCConfig:
    """Reconcile ccct configuration."""

    REQUIRED = (
        ("ofx_file", "Error: OFX file unknown!"),
        ("statement_date", "Error: Statement date unknown!"),
        ("credential_dir", "Error: Credential directory unknown!"),
        ("bank_id", "Error: Bank ID unknown!"),
        ("alloc_columns", "Error: Allocation columns unknown!"),
    )

    APPLY_SKIPPED = ["config_file", "alloc_columns"]

    def __init__(self, args: CCConsoleArgs = None, file: CCConfigFile = None):
        self._console_args = args
        self._config_file = file
        self._resolved = False

        self.ofx_file = None
        self.statement_date = None
        self.credential_dir = None
        self.bank_id = None
        self.document_id = None
        self.alloc_columns = None
        self.alloc_columns_map = None

    def resolve(self) -> Self:
        # Latch the resolution to disallow runtime changes.
        if self._resolved:
            return self

        # Console supplied args always win over config file.
        self.__apply_config(self._config_file)
        self.__apply_config(self._console_args)
        self.__validate()
        self._resolved = True
        return self

    def __apply_config(self, config: CCConfigType = None) -> None:
        if config is None:
            return
        for arg_name, value in config.to_dict().items():
            if arg_name in self.APPLY_SKIPPED:
                continue
            if value is not None:
                setattr(self, arg_name, value)

        if config.alloc_columns is not None:
            self.alloc_columns = config.alloc_columns
            self.alloc_columns_map = config.alloc_columns_map

    def __validate(self) -> None:
        for attr, error_msg in self.REQUIRED:
            value = getattr(self, attr, None)
            if value is None:
                raise argparse.ArgumentTypeError(error_msg)
        self.ofx_file = CCConsoleArgs._is_valid_ofx_file(self.ofx_file)
        self.statement_date = CCConsoleArgs._is_valid_statement_date(self.statement_date)
        self.credential_dir = CCConsoleArgs._is_valid_credential_dir(self.credential_dir)
        self.bank_id = CCConsoleArgs._is_valid_bank_id(str(self.bank_id))
