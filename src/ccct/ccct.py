# SPDX-License-Identifier: MIT
#
# Categorize credit card transactions and save them to a Google spreadsheet.

import argparse
import ofxtools
import os.path

from ccct.allocation import Allocation
from ccct.config.args import CCConsoleArgs
from ccct.config.args import DEFAULT_CONFIG_FILE
from ccct.config.config import CCConfig
from ccct.transaction import Transaction

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ofxtools.Parser import OFXTree

ACCTTYPE = "CREDITLINE"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TITLE = "CreditCardTransactions"


def _resolve_config(exit_on_error=True, default_config_file=DEFAULT_CONFIG_FILE):
    global _args
    _args = CCConfig.from_console(
        exit_on_error=exit_on_error,
        default_config_file=default_config_file,
    ).resolve()

    Allocation.init_cols(_args.alloc_columns)
    if _args.alloc_columns_map is not None:
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
