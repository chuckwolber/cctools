# SPDX-License-Identifier: MIT

import sys

from . import const

def set_arg(arg, value=None):
    if arg == None:
        raise ValueError("Missing required argument!")
    if not arg in sys.argv:
        sys.argv.append(arg)
        sys.argv.append(value)
    else:
        i = sys.argv.index(arg) + 1
        sys.argv[i] = value

def get_arg(arg=None):
    i = sys.argv.index(arg) + 1
    return

def set_all_required():
    set_ofx_file(const.VALID_OFX_FILES[0])
    set_statement_date(const.VALID_STATEMENT_DATES[0])

def set_credential_dir(custom):
    arg = '--credential-dir'
    set_arg(arg=arg, value=custom)

def set_bank_id(custom):
    arg = '--bank-id'
    set_arg(arg=arg, value=custom)

def set_document_id(custom):
    arg = '--document-id'
    set_arg(arg=arg, value=custom)

def set_alloc_columns(custom):
    arg = '--alloc-columns'
    set_arg(arg=arg, value=custom)

def set_ofx_file(custom):
    arg = '--ofx-file'
    set_arg(arg=arg, value=custom)

def set_statement_date(custom):
    arg = '--statement-date'
    set_arg(arg=arg, value=custom)

def set_config_file(custom):
    arg = '--config-file'
    set_arg(arg=arg, value=custom)
