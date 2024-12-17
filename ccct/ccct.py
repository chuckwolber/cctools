# SPDX-License-Identifier: MIT
#
# Categorize credit card transactions and save them to a Google spreadsheet.

import argparse
import json
import os.path
import re

from datetime import datetime
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
CONFIG_DIR = SCRIPT_DIR + "/config"
SCHEMA_FILE = CONFIG_DIR + "/ccct.config.schema.json"
DEFAULT_CONFIG_FILE = Path("~/.config/cctools/ccct.config.json").expanduser()

ACCTTYPE = "CREDITLINE"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TITLE = "CreditCardTransactions"
TRANSACTION_COLUMNS = ["FITID", "DTPOSTED", "TRNTYPE", "TRNAMT", "NAME", "MEMO"]

#
# ActionType functions called from _parse_args(). Neither the arguments nor the
# firing order can be controlled, so validtion is isolated to the bare minimum.
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
        if not re.match('[0-9]{9}', bank_id):
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
        raise argparse.ArgumentTypeError("ERROR: Two or more allocation colums are required.")
    return cols

def _is_valid_fx_file(fx_file):
    try:
        fx_file = Path(fx_file).expanduser()
    except TypeError:
        raise argparse.ArgumentTypeError("ERROR: FX file missing!")
    if not os.path.exists(fx_file):
        raise argparse.ArgumentTypeError(f"ERROR: FX file not found: {(fx_file)}")
    return fx_file

def _is_valid_statement_date(statement_date):
    error_msg = "ERROR: Invalid statement date {}".format(statement_date)
    try:
        if not re.match('[0-9]{8}', statement_date):
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
    global args

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
                        help="The bank routing number. Used to validate the FX file.")
    parser.add_argument('--document-id',
                        required=False,
                        default=None,
                        help="The google document ID to write transactions. A new spreadsheet is created if this is omitted.")
    parser.add_argument('--alloc-columns',
                        required=False,
                        type=_set_alloc_columns,
                        help="Colon delimited list of categories to allocate transactions.")
    parser.add_argument('--fx-file',
                        required=True,
                        type=_is_valid_fx_file,
                        help="The QFX or OFX file to parse for transactions.")
    parser.add_argument('--statement-date',
                        required=True,
                        type=_is_valid_statement_date,
                        help="This is the worksheet that accumulates transactions.")
    parser.add_argument('--config-file',
                        required=False,
                        default=DEFAULT_CONFIG_FILE,
                        type=_is_valid_config_file,
                        help="JSON formatted config file. See docs for details.")
    args = parser.parse_args()
    return True

def _load_from_config(default_config_file=DEFAULT_CONFIG_FILE):
    """ Load Missing Configuration from a Configuration File
    If a default configuration file is available, load it and run the correct
    validation action on any missing arguments.

    Command line arguments always take precedence over configuration file
    provided values.
    """

    if not isinstance(args.config_file, dict):
        if os.path.exists(DEFAULT_CONFIG_FILE):
            args.config_file = _is_valid_config_file(str(DEFAULT_CONFIG_FILE))
        else:
            return False

    if args.credential_dir == None and "credential_dir" in args.config_file:
        args.credential_dir = _is_valid_credential_dir(args.config_file['credential_dir'])

    if args.bank_id == None and "bank_id" in args.config_file:
        args.bank_id = _is_valid_bank_id(str(args.config_file['bank_id']))

    if args.document_id == None and "document_id" in args.config_file:
        args.document_id = args.config_file['document_id']

    if args.alloc_columns == None and "alloc_columns" in args.config_file:
        args.alloc_columns = []
        args.alloc_columns_map = {}
        for c in args.config_file['alloc_columns']:
            args.alloc_columns.append(c['short'])
            args.alloc_columns_map[c['short']] = c['long']

    return True

def _resolve_config(exit_on_error=True, default_config_file=DEFAULT_CONFIG_FILE):
    _parse_args(exit_on_error=exit_on_error)
    _load_from_config(default_config_file=default_config_file)

    # Missing command line args are filled in from a config file if one is
    # available. Ensure that all requried values end up being populated.
    if args.fx_file == None:
        raise argparse.ArgumentTypeError("Error: FX file unknown!")
    if args.statement_date == None:
        raise argparse.ArgumentTypeError("Error: Statement date unknown!")
    if args.credential_dir == None:
        raise argparse.ArgumentTypeError("Error: Credential directory unknown!")
    if args.bank_id == None:
        raise argparse.ArgumentTypeError("Error: Bank ID unknown!")
    if args.alloc_columns == None:
        raise argparse.ArgumentTypeError("Error: Allocation columns unknown!")

    return True

def _parse_fx_file():
    global ofx

    parser = OFXTree()
    with open(args.fx_file, 'rb') as f:
        parser.parse(f)
    ofx = parser.convert()

    ofx_bank_id = ofx.bankmsgsrsv1[0].stmtrs.bankacctfrom.bankid
    ofx_accttype = ofx.bankmsgsrsv1[0].stmtrs.bankacctfrom.accttype

    if ofx_bank_id != args.bank_id:
        raise Exception("Error: Invalid BankID. Got {}, expected {}".format(ofx_bank_id, args.bank_id))
    if ofx_accttype != ACCTTYPE:
        raise Exception("Error: Invalid account type. Got {}, expected {}".format(ofx_accttype, ACCTTYPE))

    return True

def _get_google_creds():
    global creds
    global service

    credentials_file = os.path.join(args.credential_dir, "credentials.json")
    token_file = os.path.join(args.credential_dir, "token.json")

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
    service = build("sheets", "v4", credentials=creds)

    with open(token_file, "w") as token:
      token.write(creds.to_json())

def _create_spreadsheet():
    global document_id
    global spreadsheet

    try:
        if args.document_id != None:
            document_id = args.document_id
            spreadsheet = service.spreadsheets().get(spreadsheetId=document_id).execute()
            print(f"Spreadsheet Opened: {(TITLE)}")
        else:
            spreadsheet = (
                service.spreadsheets()
                    .create(body={"properties": {"title": TITLE}},
                            fields="spreadsheetId")
                        .execute()
            )
            document_id = spreadsheet.get('spreadsheetId')
            print(f"Spreadsheet Created and Opened: {(TITLE)}")

        print(f"Spreadsheet ID: {(spreadsheet.get('spreadsheetId'))}")
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
    for sheet in spreadsheet.get('sheets', ''):
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
        service.spreadsheets().batchUpdate(
                spreadsheetId=document_id, body=request_body).execute()
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def _create_statement_worksheet():
    try:
        sheets = spreadsheet.get('sheets', '')
        sheet_names = [sheet['properties']['title'] for sheet in sheets]

        response = None
        sheet_id = None
        if args.document_id == None:
            _rename_worksheet("Sheet1", args.statement_date)
        elif args.statement_date not in sheet_names:
            request_body = {
                'requests': [{
                        'addSheet': {
                                'properties': {
                                        'title': args.statement_date,
                                        'index': 0
                                }
                        }
                }]
            }
            response = service.spreadsheets().batchUpdate(
                        spreadsheetId=document_id, body=request_body).execute()

            # On newly created worksheets, sheet_id is not immediately
            # discoverable without looking at the batch response object.
            sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']

        # Google sheets makes a guess at column format. This guess turns out
        # to be an automatic number for the transaction amount which cuts off
        # characters when digits to the right of the decimal are zero. This
        # makes it difficult to compare transactions to avoid duplication.
        # Format the amount column to the numeric "@" format so the amounts are
        # effectivey treated as text. One might think they could sidestep this
        # complication by formatting all transaction amount strings to two
        # decimal places, but the OFX specification (section 3.2.9.1) says
        # little about the number of decimal places we should expect, except to
        # leave the number format up to the client/server. Since foreign
        # currency transactions require more than two decimal places, it makes
        # more sense to keep the format consistent with the original and avoid
        # making any assumptions.
        if sheet_id == None:
            sheet_id = _get_sheet_id(args.statement_date)
        request_body = {
                'requests': [{
                        'repeatCell': {
                                'range': {
                                        'sheet_id': sheet_id,
                                        'startColumnIndex': TRANSACTION_COLUMNS.index("TRNAMT"),
                                        'endColumnIndex': TRANSACTION_COLUMNS.index("TRNAMT") + 1
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
        service.spreadsheets().batchUpdate(
                spreadsheetId=document_id, body=request_body).execute()
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def _get_worksheet_header():
    global worksheet_header

    try:
        range_name = "{}!1:1".format(args.statement_date)
        result = service.spreadsheets().values().get(spreadsheetId=document_id, range=range_name).execute()
        worksheet_header = result.get('values', [])
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def _is_statement_worksheet_header_valid():
    if len(worksheet_header) == 0:
        return True
    elif worksheet_header == [TRANSACTION_COLUMNS + args.alloc_columns]:
        return True
    return False

def _set_statement_worksheet_header():
    range_name = "{}!1:1".format(args.statement_date)
    try:
        body = {"values": [TRANSACTION_COLUMNS + args.alloc_columns]}
        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=document_id,
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
        print("\tGot Header:      {}".format(worksheet_header))
        print("\tExpected Header: {}".format([TRANSACTION_COLUMNS + args.alloc_columns]))
        exit(1)
    if len(worksheet_header) == 0:
        _set_statement_worksheet_header()

def _get_statement_worksheet_transactions():
    global worksheet_transactions

    try:
        range_name = "{}!A:F".format(args.statement_date)
        result = service.spreadsheets().values().get(spreadsheetId=document_id, range=range_name).execute()
        worksheet_transactions = result.get('values', [])

        # Delete the header.
        del worksheet_transactions[0]

        # If the last field is empty (usually the memo field), google sheets
        # returns a truncated transaction. When importing a batch of
        # transactions, truncated transactions fail to be detected and we end up
        # reprocessing old transactions.
        worksheet_transactions = [row + [None] * (len(TRANSACTION_COLUMNS) - len(row)) for row in worksheet_transactions]

        print(f"Found {(len(worksheet_transactions))} worksheet transactions.")
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def _display_alloc_column_map_key(key):
    print("\t" + key + ":\t" + args.alloc_columns_map[key])

def _display_alloc_column_map(key=None):
    if key == None:
        for key in args.alloc_columns_map.keys():
            _display_alloc_column_map_key(key)
    else:
            _display_alloc_column_map_key(key)

def _get_allocations(amount: float):
    allocations = [0] * len(args.alloc_columns)
    original_amount = amount

    negative = False
    if amount < 0:
        negative = True

    while amount != 0:
        paired = [f"{a}({b})" if b != 0 else a for a, b in zip(args.alloc_columns, allocations)]

        # If we have a map, enable the '?' command to display it.
        if "alloc_columns_map" in args and args.alloc_columns_map != None:
            paired.append('?')

        valid_inputs = f"[{', '.join(paired)}]"
        user_input = input(f"Allocate Transaction {(valid_inputs)}[{(amount)}]: ")
        alloc = user_input.split()

        if len(alloc) > 0:
            col = alloc[0]

            if col == "?":
                _display_alloc_column_map()
                continue
            elif col not in args.alloc_columns:
                continue

            alloc_index = args.alloc_columns.index(col)
            amt = amount

            if len(alloc) > 1:
                if alloc[1] == "?":
                    _display_alloc_column_map(alloc[0])
                    continue
                try:
                    amt = float(alloc[1])

                    # Credit Card DEBITS cannot be allocated as payment DEBITS
                    # and vice versa.
                    if (negative and amt > 0) or (not negative and amt < 0):
                        continue

                    if negative and amt < amount:
                        amt = amount
                    elif not negative and amt > amount:
                        amt = amount
                except ValueError:
                    continue

            amount = amount + allocations[alloc_index]
            amount = round(amount - amt, 2)
            allocations[alloc_index] = amt

    if round(sum(allocations),2) != original_amount:
        raise Exception("Error: Transaction incorrectly allocated {} != {}".format(allocations, original_amount))
    return ['' if x == 0 else x for x in allocations]

def _allocate_ofx_transactions():
    global ofx_transactions

    transactions = ofx.bankmsgsrsv1[0].stmtrs.banktranlist
    print("Found {} OFX transactions.".format(len(transactions)))

    ofx_transactions = []
    for i, t in enumerate(transactions):
        ofx_transaction = [''] * len(TRANSACTION_COLUMNS)
        ofx_transaction[TRANSACTION_COLUMNS.index("FITID")]    = t.fitid
        ofx_transaction[TRANSACTION_COLUMNS.index("DTPOSTED")] = t.dtposted.isoformat()
        ofx_transaction[TRANSACTION_COLUMNS.index("TRNTYPE")]  = t.trntype
        ofx_transaction[TRANSACTION_COLUMNS.index("TRNAMT")]   = str(t.trnamt)
        ofx_transaction[TRANSACTION_COLUMNS.index("NAME")]     = t.name
        ofx_transaction[TRANSACTION_COLUMNS.index("MEMO")]     = t.memo

        # Due to some institutions occasionally reusing FITID values we are
        # forced to compare the entire transaction tuple rather than just the
        # FITID as the OFX specification originally intended. This approach will
        # fail if two affected transactions during a statement period have the
        # exact same dollar value, but there is nothing we can do about that
        # short of requiring an unreasonable amount of human intervention.
        if ofx_transaction not in worksheet_transactions:
            print("\nClassify transaction {} of {}:".format(i + 1, len(transactions)))
            print("\tTID:\t{}".format(t.fitid))
            print("\tDate:\t{}".format(t.dtposted.isoformat()))
            print("\tType:\t{}".format(t.trntype))
            print("\tAmount:\t{}".format(t.trnamt))
            print("\tName:\t{}".format(t.name))
            print("\tMemo:\t{}".format(t.memo))

            # Since this is credit card data, DEBIT transactions are purchases
            # and CREDIT transactions are payments and refunds. From the point
            # of view of the card's balance, a CREDIT transaction is a DEBIT on
            # the card's balance, and a DEBIT transaction is a CREDIT on the
            # card's balance. From the user's point of view, we invert the sign
            # on the transaction amount so card transaction DEBITs are
            # categorized as a CREDIT "owed" to the card (and vice versa). This
            # allows the user to view transactions in terms of the amount they
            # owe *TO* the credit card.
            allocations = _get_allocations(float(-1*t.trnamt))
            ofx_transactions.append(ofx_transaction + allocations)
        else:
            print("Skipping allocated transaction {} of {}:".format(i + 1, len(transactions)))

def _write_ofx_transactions():
    global ofx_transactions

    if len(ofx_transactions) <= 0:
        print("No transactions to write...")
        return 0

    ofx_transactions = sorted(ofx_transactions, key=lambda x: x[TRANSACTION_COLUMNS.index("DTPOSTED")])
    range_name = "{}!R{}C1:R{}C{}".format(args.statement_date,
                        len(worksheet_transactions) + 2,
                        len(worksheet_transactions) + 1 + len(ofx_transactions),
                        len(ofx_transactions[0]))
    try:
        body = {"values": ofx_transactions}
        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=document_id,
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

def console_main():
    _resolve_config()
    _parse_fx_file()
    _get_google_creds()

    _create_spreadsheet()
    _create_statement_worksheet()
    _create_statement_worksheet_header()

    _get_statement_worksheet_transactions()
    _allocate_ofx_transactions()
    _write_ofx_transactions()
