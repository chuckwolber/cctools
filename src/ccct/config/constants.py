# SPDX-License-Identifier: MIT

from importlib.resources import files
from pathlib import Path

DEFAULT_CONFIG_FILE = Path("~/.config/cctools/ccct.config.json").expanduser()
SCHEMA_FILE = files("ccct.config").joinpath("ccct.config.schema.json")
