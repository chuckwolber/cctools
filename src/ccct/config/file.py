# SPDX-License-Identifier: MIT

import argparse
import json

from pathlib import Path

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from ccct.config.types import CCConfigType
from ccct.config.constants import DEFAULT_CONFIG_FILE
from ccct.config.constants import SCHEMA_FILE


class CCConfigFile(CCConfigType):
    """Load and validate JSON configuration file values."""

    def __init__(self, config_file=DEFAULT_CONFIG_FILE, schema_file=SCHEMA_FILE) -> None:
        self._config_file = Path(config_file).expanduser()
        self._schema_file = schema_file
        self._config = None
        self._alloc_columns = None
        self._alloc_columns_map = None
        self.__load()

    def to_dict(self) -> dict:
        return self._config or {}

    @property
    def alloc_columns(self) -> list | None:
        return self._alloc_columns

    @property
    def alloc_columns_map(self) -> dict | None:
        return self._alloc_columns_map

    def __load(self) -> None:
        try:
            with open(self._schema_file, "r") as json_schema:
                schema = json.load(json_schema)
            with open(self._config_file, "r") as json_config:
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
            msg = "ERROR: Invalid config file {}".format(self._config_file)
            raise argparse.ArgumentTypeError(msg + "\n" + str(e))

        alloc_columns = config.get("alloc_columns")
        if alloc_columns is not None:
            self._alloc_columns = []
            self._alloc_columns_map = {}
            for column in alloc_columns:
                self._alloc_columns.append(column["short"])
                self._alloc_columns_map[column["short"]] = column["long"]

        self._config = config
