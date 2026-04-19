# SPDX-License-Identifier: MIT
#
# Categorize credit card transactions and save them to a Google spreadsheet.

import argparse
import json
import ofxtools
import os.path
import re

from ccct.allocation import Allocation
from ccct.transaction import Transaction

from datetime import datetime
from importlib.resources import files
from pathlib import Path
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ofxtools.Parser import OFXTree

SCRIPT_DIR = str(Path(__file__).resolve().parent)
DEFAULT_CONFIG_FILE = Path("~/.config/cctools/ccct.config.json").expanduser()
SCHEMA_FILE = files("ccct.config").joinpath("ccct.config.schema.json")

ACCTTYPE = "CREDITLINE"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TITLE = "CreditCardTransactions"


#
# ActionType functions called from _parse_args(). Neither the arguments nor the
# firing order can be controlled, so validation is isolated to the bare minimum.
# Stronger validation happens later on.
#
def _is_valid_credential_dir(credential_dir):
    try:
        credential_dir = Path(credential_dir).expanduser()
    except TypeError:
        raise argparse.ArgumentTypeError("ERROR: Credential dir missing!")
    if not os.path.exists(credential_dir):
        raise argparse.ArgumentTypeError(f"ERROR: Credential directory not found: {(credential_dir)}")
    return credential_dir

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

def _set_alloc_columns(alloc_columns):
    try:
        cols = alloc_columns.split(":")
    except AttributeError:
        raise argparse.ArgumentTypeError("ERROR: alloc columns string missing!")
    if len(cols) <= 1:
        raise argparse.ArgumentTypeError("ERROR: Two or more allocation columns are required.")
    return cols

def _is_valid_ofx_file(ofx_file):
    try:
        ofx_file = Path(ofx_file).expanduser()
    except TypeError:
        raise argparse.ArgumentTypeError("ERROR: OFX file missing!")
    if not os.path.exists(ofx_file):
        raise argparse.ArgumentTypeError(f"ERROR: OFX file not found: {(ofx_file)}")
    return ofx_file

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

def _parse_args(exit_on_error=True):
    global _args

    parser = argparse.ArgumentParser(
            description="Categorize Credit Card Transactions",
            exit_on_error=exit_on_error)
    parser.add_argument('--credential-dir',
                        required=False,
                        type=_is_valid_credential_dir,
                        help="Google API credential directory.")
    parser.add_argument('--bank-id',
                        required=False,
                        type=_is_valid_bank_id,
                        help="The bank routing number. Used to validate the OFX file.")
    parser.add_argument('--document-id',
                        required=False,
                        default=None,
                        help="The Google document ID to write transactions. A new spreadsheet is created if this is omitted.")
    parser.add_argument('--alloc-columns',
                        required=False,
                        type=_set_alloc_columns,
                        help="Colon delimited list of categories to allocate transactions.")
    parser.add_argument('--ofx-file',
                        required=True,
                        type=_is_valid_ofx_file,
                        help="The OFX file to parse for transactions.")
    parser.add_argument('--statement-date',
                        required=True,
                        type=_is_valid_statement_date,
                        help="This is the worksheet that accumulates transactions.")
    parser.add_argument('--config-file',
                        required=False,
                        default=DEFAULT_CONFIG_FILE,
                        type=_is_valid_config_file,
                        help="JSON formatted config file. See docs for details.")
    _args = parser.parse_args()
    return True

def _load_from_config(default_config_file=DEFAULT_CONFIG_FILE):
    """ Load Missing Configuration from a Configuration File
    If a default configuration file is available, load it and run the correct
    validation action on any missing arguments.

    Command line arguments always take precedence over configuration file
    provided values.
    """
    if '_args' not in globals():
        raise argparse.ArgumentError("ERROR: Argument object not found!")

    if not isinstance(_args.config_file, dict):
        if default_config_file is not None and os.path.exists(default_config_file):
            _args.config_file = _is_valid_config_file(str(default_config_file))
        else:
            return False

    if _args.credential_dir == None and "credential_dir" in _args.config_file:
        _args.credential_dir = _is_valid_credential_dir(_args.config_file['credential_dir'])

    if _args.bank_id == None and "bank_id" in _args.config_file:
        _args.bank_id = _is_valid_bank_id(str(_args.config_file['bank_id']))

    if _args.document_id == None and "document_id" in _args.config_file:
        _args.document_id = _args.config_file['document_id']

    if _args.alloc_columns == None and "alloc_columns" in _args.config_file:
        _args.alloc_columns = []
        _args.alloc_columns_map = {}
        for c in _args.config_file['alloc_columns']:
            _args.alloc_columns.append(c['short'])
            _args.alloc_columns_map[c['short']] = c['long']

    return True

def _resolve_config(exit_on_error=True, default_config_file=DEFAULT_CONFIG_FILE):
    _parse_args(exit_on_error=exit_on_error)
    _load_from_config(default_config_file=default_config_file)

    # Missing command line args are filled in from a config file if one is
    # available. Ensure that all required values end up being populated.
    if _args.ofx_file == None:
        raise argparse.ArgumentTypeError("Error: OFX file unknown!")
    if _args.statement_date == None:
        raise argparse.ArgumentTypeError("Error: Statement date unknown!")
    if _args.credential_dir == None:
        raise argparse.ArgumentTypeError("Error: Credential directory unknown!")
    if _args.bank_id == None:
        raise argparse.ArgumentTypeError("Error: Bank ID unknown!")
    if _args.alloc_columns == None:
        raise argparse.ArgumentTypeError("Error: Allocation columns unknown!")

    Allocation.init_cols(_args.alloc_columns)
    if hasattr(_args, 'alloc_columns_map'):
        Allocation.init_cols_map(_args.alloc_columns_map)

    return True

def _parse_ofx_file():
    global _ofx

    parser = OFXTree()
    with open(_args.ofx_file, 'rb') as f:
        try:
            parser.parse(f)
        except IndexError as ie:
            raise Exception(f"Error: Invalid OFX file. {(str(ie))}")

    try:
        _ofx = parser.convert()
    except ofxtools.Types.OFXSpecError as oe:
        raise ValueError(f"Error: Malformed OFX data. {(str(oe))}")

    ofx_bank_id = _ofx.bankmsgsrsv1[0].stmtrs.bankacctfrom.bankid
    ofx_accttype = _ofx.bankmsgsrsv1[0].stmtrs.bankacctfrom.accttype

    if ofx_bank_id != _args.bank_id:
        raise Exception("Error: Invalid BankID. Got {}, expected {}".format(ofx_bank_id, _args.bank_id))
    if ofx_accttype != ACCTTYPE:
        raise Exception("Error: Invalid account type. Got {}, expected {}".format(ofx_accttype, ACCTTYPE))

    return True

def _get_google_creds():
    global _service

    credentials_file = os.path.join(_args.credential_dir, "credentials.json")
    token_file = os.path.join(_args.credential_dir, "token.json")

    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

        # creds.refresh() appears to be broken so delete invalid tokens.
        if not creds.valid:
            os.remove(token_file)
            creds = None

    # Kick the user to a login web page if valid credentials are unavailable.
    if not creds:
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_file, SCOPES
        )
        creds = flow.run_local_server(port=0)
    _service = build("sheets", "v4", credentials=creds)

    with open(token_file, "w") as token:
      token.write(creds.to_json())

def _create_spreadsheet():
    global _document_id
    global _spreadsheet

    try:
        if _args.document_id != None:
            _document_id = _args.document_id
            _spreadsheet = _service.spreadsheets().get(spreadsheetId=_document_id).execute()
            print(f"Spreadsheet Opened: {(TITLE)}")
        else:
            _spreadsheet = (
                _service.spreadsheets()
                    .create(body={"properties": {"title": TITLE}},
                            fields="spreadsheetId")
                        .execute()
            )
            _document_id = _spreadsheet.get('spreadsheetId')
            print(f"Spreadsheet Created and Opened: {(TITLE)}")

        print(f"Spreadsheet ID: {(_spreadsheet.get('spreadsheetId'))}")
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def _get_sheet_id(title):
    """
    Retrieve the worksheet ID

    Sheet ID is assigned at worksheet creation time and persists regardless
    of the worksheet's indexed position in the spreadsheet web UI. Worksheets
    can be created at a particular position index, but accessing and modifying
    worksheet contents should be done via the sheet ID.
    """
    for sheet in _spreadsheet.get('sheets', ''):
        if sheet['properties']['title'] == title:
            return sheet['properties']['sheetId']
    return None

def _rename_worksheet(old_title: str, new_title: str):
    try:
        request_body = {
                'requests': [{
                        'updateSheetProperties': {
                                'properties': {
                                        'sheetId': _get_sheet_id(old_title),
                                        'title': new_title
                                },
                                'fields': 'title'
                        }
                }]
        }
        _service.spreadsheets().batchUpdate(
                spreadsheetId=_document_id, body=request_body).execute()
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def _create_statement_worksheet():
    try:
        sheets = _spreadsheet.get('sheets', '')
        sheet_names = [sheet['properties']['title'] for sheet in sheets]

        response = None
        sheet_id = None
        if _args.document_id == None:
            _rename_worksheet("Sheet1", _args.statement_date)
        elif _args.statement_date not in sheet_names:
            request_body = {
                'requests': [{
                        'addSheet': {
                                'properties': {
                                        'title': _args.statement_date,
                                        'index': 0
                                }
                        }
                }]
            }
            response = _service.spreadsheets().batchUpdate(
                        spreadsheetId=_document_id, body=request_body).execute()

            # On newly created worksheets, sheet_id is not immediately
            # discoverable without looking at the batch response object.
            sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']

        # Google sheets makes a guess at column format. This guess turns out
        # to be an automatic number for the transaction amount which cuts off
        # characters when digits to the right of the decimal are zero. This
        # makes it difficult to compare transactions to avoid duplication.
        # Format the amount column to the numeric "@" format so the amounts are
        # effectively treated as text. One might think they could sidestep this
        # complication by formatting all transaction amount strings to two
        # decimal places, but the OFX specification (section 3.2.9.1) says
        # little about the number of decimal places we should expect, except to
        # leave the number format up to the client/server. Since foreign
        # currency transactions require more than two decimal places, it makes
        # more sense to keep the format consistent with the original and avoid
        # making any assumptions.
        if sheet_id == None:
            sheet_id = _get_sheet_id(_args.statement_date)
        request_body = {
                'requests': [{
                        'repeatCell': {
                                'range': {
                                        'sheetId': sheet_id,
                                        'startColumnIndex': Transaction.TRANSACTION_COLUMNS.index("TRNAMT"),
                                        'endColumnIndex': Transaction.TRANSACTION_COLUMNS.index("TRNAMT") + 1
                                },
                                'cell': {
                                        'userEnteredFormat': {
                                                'numberFormat': {
                                                        'type': 'NUMBER',
                                                        'pattern': '0.00'
                                                }
                                        }
                                },
                                'fields': "userEnteredFormat.numberFormat"
                        }
                },{
                        # While we are at it, freeze the header row for usability.
                        "updateSheetProperties": {
                                "properties": {
                                        "sheetId": sheet_id,
                                        "gridProperties": {
                                        "frozenRowCount": 1
                                        }
                                },
                                "fields": "gridProperties.frozenRowCount"
                        }
                }]
        }
        _service.spreadsheets().batchUpdate(
                spreadsheetId=_document_id, body=request_body).execute()
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def _get_worksheet_header():
    global _worksheet_header

    try:
        range_name = "{}!1:1".format(_args.statement_date)
        result = _service.spreadsheets().values().get(spreadsheetId=_document_id, range=range_name).execute()
        _worksheet_header = result.get('values', [])
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def _is_statement_worksheet_header_valid():
    if len(_worksheet_header) == 0:
        return True
    elif _worksheet_header == [Transaction.TRANSACTION_COLUMNS + _args.alloc_columns]:
        return True
    return False

def _set_statement_worksheet_header():
    range_name = "{}!1:1".format(_args.statement_date)
    try:
        body = {"values": [Transaction.TRANSACTION_COLUMNS + _args.alloc_columns]}
        result = (
            _service.spreadsheets()
            .values()
            .update(
                spreadsheetId=_document_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def _create_statement_worksheet_header():
    _get_worksheet_header()
    if not _is_statement_worksheet_header_valid():
        print("ERROR: Worksheet header appears to be invalid.")
        print("\tGot Header:      {}".format(_worksheet_header))
        print("\tExpected Header: {}".format([Transaction.TRANSACTION_COLUMNS + _args.alloc_columns]))
        exit(1)
    if len(_worksheet_header) == 0:
        _set_statement_worksheet_header()

def _get_statement_worksheet_transactions():
    global _worksheet_transactions

    try:
        range_name = "{}!A:F".format(_args.statement_date)
        result = _service.spreadsheets().values().get(spreadsheetId=_document_id, range=range_name).execute()
        _worksheet_transactions = result.get('values', [])

        # Delete the header.
        del _worksheet_transactions[0]

        # If the last field is empty (usually the memo field), google sheets
        # returns a truncated transaction. When importing a batch of
        # transactions, truncated transactions fail to be detected and we end up
        # reprocessing old transactions.
        _worksheet_transactions = [row + [None] * (len(Transaction.TRANSACTION_COLUMNS) - len(row)) for row in _worksheet_transactions]

        print(f"Found {(len(_worksheet_transactions))} worksheet transactions.")
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def _get_ofx_transactions():
    global _transactions

    _transactions = []
    banktranlist = _ofx.bankmsgsrsv1[0].stmtrs.banktranlist

    for t in banktranlist:
        _transactions.append(Transaction(t))

    return True

def _allocate_ofx_transaction(transaction: Transaction, index: int):
    print("\nAllocate transaction {} of {}:".format(index + 1, len(_transactions)))
    transaction.print()

    alloc = transaction.allocation
    while alloc.amount_curr != 0:
        valid_inputs = alloc.get_paired_allocations()
        user_input = input(f"Allocate Transaction {(valid_inputs)}[{(alloc.amount_curr)}]: ")
        user_input_list = user_input.split()

        if len(user_input_list) == 1:
            category = user_input_list[0]
            if category == "?":
                Allocation.print_cols_map()
                continue
            alloc.allocate_amount(category=category)
        elif len(user_input_list) == 2:
            category = user_input_list[0]
            amount = user_input_list[1]
            if str(amount) == "?":
                Allocation.print_cols_map(key=category)
                continue
            alloc.allocate_amount(category=category, amount=amount)

    # Check for arithmetic errors.
    if alloc.get_allocations_sum() != alloc.amount_orig:
        raise Exception("Error: Transaction incorrectly allocated {} != {}".format(alloc.allocations, alloc.amount_orig))

    return alloc.to_list()

def _allocate_ofx_transactions():
    global _ofx_transactions
    print("Found {} OFX transactions.".format(len(_transactions)))

    _ofx_transactions = []
    for i, t in enumerate(_transactions):
        ofx_transaction = t.to_list()

        # Testing a transaction for prior categorization should be as simple as
        # looking for an existing FITID value. Section 3.2.3 of the OFX v2.3
        # specification says that, "FITIDs must be unique within the scope of an
        # account". Unfortunately, some institutions occasionally reuse FITID
        # values, so we are forced to compare the entire transaction tuple. This
        # approach will fail if two affected transactions during a statement
        # period have identical tuples, but there is nothing we can do about
        # that short of requiring an unreasonable amount of human intervention.
        if ofx_transaction not in _worksheet_transactions:
            allocations = _allocate_ofx_transaction(transaction=t, index=i)
            _ofx_transactions.append(ofx_transaction + allocations)
        else:
            print("Skipping allocated transaction {} of {}:".format(i + 1, len(_transactions)))

def _write_ofx_transactions():
    if len(_ofx_transactions) <= 0:
        print("No transactions to write...")
        return 0

    range_name = "{}!R{}C1:R{}C{}".format(_args.statement_date,
                        len(_worksheet_transactions) + 2,
                        len(_worksheet_transactions) + 1 + len(_ofx_transactions),
                        len(_ofx_transactions[0]))
    try:
        body = {"values": _ofx_transactions}
        result = (
            _service.spreadsheets()
            .values()
            .update(
                spreadsheetId=_document_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )
        print(f"{result.get('updatedCells')} cells updated.")
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def console():
    _resolve_config()
    _parse_ofx_file()
    _get_google_creds()

    _create_spreadsheet()
    _create_statement_worksheet()
    _create_statement_worksheet_header()

    _get_statement_worksheet_transactions()
    _get_ofx_transactions()
    _allocate_ofx_transactions()
    _write_ofx_transactions()
