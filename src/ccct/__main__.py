#!/usr/bin/env python3
#
# SPDX-License-Identifier: MIT

from ccct.ccct import CCTransactionCategorizer
from ccct.config.args import CCConsoleArgs
from ccct.config.config import CCConfig
from ccct.config.constants import DEFAULT_CONFIG_FILE
from ccct.config.file import CCConfigFile

def main() -> None:
    console_args = CCConsoleArgs().parse()
    config_file = None
    if console_args.config_file is not None:
        config_file = CCConfigFile(console_args.config_file)
    elif DEFAULT_CONFIG_FILE.exists():
        config_file = CCConfigFile(DEFAULT_CONFIG_FILE)
    config = CCConfig(args=console_args, file=config_file).resolve()
    CCTransactionCategorizer(config).console()

if __name__ == "__main__":
    main()
