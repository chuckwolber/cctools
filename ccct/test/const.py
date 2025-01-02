# SPDX-License-Identifier: MIT

from pathlib import Path

SCRIPT_DIR = str(Path(__file__).resolve().parent)
ASSETS_DIR = SCRIPT_DIR + "/assets"
CONFIG_DIR = SCRIPT_DIR + "/../config"

VALID_DIR = ASSETS_DIR
INVALID_DIR = "/path/that/must/not/exist/DD88DA98-A6D8-4E9A-BE62-356682B25598"

INVALID_CREDENTIAL_DIRS = [None, INVALID_DIR]
VALID_CREDENTIAL_DIRS = [ASSETS_DIR]

VALID_BANK_IDS = ["325081403", "314074269"]
INVALID_BANK_ID_STRINGS = [None, "", "1", "12345678", "1234567890"]
INVALID_BANK_ID_NUMBERS = ["123456789", "999999999"]
INVALID_BANK_IDS = INVALID_BANK_ID_STRINGS + INVALID_BANK_ID_NUMBERS

VALID_DOCUMENT_ID = "3DAsQI4N-Mh-UnE6mvYv8mpH4twBChgHQ34uyYcar7dg"

INVALID_ALLOC_COLUMNS = [None, "", "x", " "]
VALID_ALLOC_COLUMNS = ['a:b:c:d:e:f:g']

MISSING_OFX_FILES = [None, INVALID_DIR, INVALID_DIR + "/export.qfx"]
VALID_OFX_FILES = [ASSETS_DIR + "/export.valid.qfx"]

# Triggers argparse.ArgumentTypeError
INVALID_STATEMENT_DATE_STRINGS = [None, "1234567" , "123456789"]
# Triggers ValueError
INVALID_STATEMENT_DATE_VALUES = ["00000000", "00001201" , # Bad Year
                                 "20240001", "20241301" , # Bad Month
                                 "20230229", "20240132" , # Bad Day
                                ]
INVALID_STATEMENT_DATES = INVALID_STATEMENT_DATE_STRINGS + INVALID_STATEMENT_DATE_VALUES
VALID_STATEMENT_DATES = ["20241126"]

MISSING_CONFIG_FILES = [None, INVALID_DIR, INVALID_DIR + "/config.json"]
INVALID_CONFIG_FILES = [ASSETS_DIR + "/config.invalid-1.json",
                        ASSETS_DIR + "/config.invalid-2.json",
                        ASSETS_DIR + "/config.invalid-3.json"]

INVALID_CONFIGS =  MISSING_CONFIG_FILES + INVALID_CONFIG_FILES
VALID_CONFIG = ASSETS_DIR + "/config.valid.json"

MISSING_SCHEMA_FILES = [None, INVALID_DIR, INVALID_DIR + "/this.is.not.a.schema.file.json"]
INVALID_SCHEMA_FILES = [ASSETS_DIR + "/schema.invalid.json"]
INVALID_SCHEMA = MISSING_SCHEMA_FILES + INVALID_SCHEMA_FILES
VALID_SCHEMA_FILES = [CONFIG_DIR + "/ccct.config.schema.json"]