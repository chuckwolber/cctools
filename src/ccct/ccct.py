# SPDX-License-Identifier: MIT
#
# Categorize credit card transactions and save them to a Google spreadsheet.

import ofxtools
import os.path

from ccct.allocation import Allocation
from ccct.config.config import CCConfig
from ccct.transaction import Transaction

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ofxtools.Parser import OFXTree

ACCTTYPE = "CREDITLINE"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TITLE = "CreditCardTransactions"


class CCTransactionCategorizer:
    def __init__(self, config: CCConfig) -> None:
        self._config = config.resolve()
        self._ofx = None
        self._service = None
        self._document_id = None
        self._spreadsheet = None
        self._worksheet_header = None
        self._worksheet_transactions = []
        self._transactions = []
        self._ofx_transactions = []

        Allocation.init_cols(self._config.alloc_columns)
        if self._config.alloc_columns_map is not None:
            Allocation.init_cols_map(self._config.alloc_columns_map)

    def _parse_ofx_file(self):
        parser = OFXTree()
        with open(self._config.ofx_file, 'rb') as f:
            try:
                parser.parse(f)
            except IndexError as ie:
                raise Exception(f"Error: Invalid OFX file. {(str(ie))}")

        try:
            self._ofx = parser.convert()
        except ofxtools.Types.OFXSpecError as oe:
            raise ValueError(f"Error: Malformed OFX data. {(str(oe))}")

        ofx_bank_id = self._ofx.bankmsgsrsv1[0].stmtrs.bankacctfrom.bankid
        ofx_accttype = self._ofx.bankmsgsrsv1[0].stmtrs.bankacctfrom.accttype

        if ofx_bank_id != self._config.bank_id:
            raise Exception("Error: Invalid BankID. Got {}, expected {}".format(ofx_bank_id, self._config.bank_id))
        if ofx_accttype != ACCTTYPE:
            raise Exception("Error: Invalid account type. Got {}, expected {}".format(ofx_accttype, ACCTTYPE))

        return True

    def _get_google_creds(self):
        credentials_file = os.path.join(self._config.credential_dir, "credentials.json")
        token_file = os.path.join(self._config.credential_dir, "token.json")

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
        self._service = build("sheets", "v4", credentials=creds)

        with open(token_file, "w") as token:
            token.write(creds.to_json())

    def _create_spreadsheet(self):
        try:
            if self._config.document_id is not None:
                self._document_id = self._config.document_id
                self._spreadsheet = self._service.spreadsheets().get(spreadsheetId=self._document_id).execute()
                print(f"Spreadsheet Opened: {(TITLE)}")
            else:
                self._spreadsheet = (
                    self._service.spreadsheets()
                        .create(body={"properties": {"title": TITLE}},
                                fields="spreadsheetId")
                            .execute()
                )
                self._document_id = self._spreadsheet.get('spreadsheetId')
                print(f"Spreadsheet Created and Opened: {(TITLE)}")

            print(f"Spreadsheet ID: {(self._spreadsheet.get('spreadsheetId'))}")
        except HttpError as error:
            print(f"An error occurred: {error}")
            return error

    def _get_sheet_id(self, title):
        """
        Retrieve the worksheet ID

        Sheet ID is assigned at worksheet creation time and persists regardless
        of the worksheet's indexed position in the spreadsheet web UI. Worksheets
        can be created at a particular position index, but accessing and modifying
        worksheet contents should be done via the sheet ID.
        """
        for sheet in self._spreadsheet.get('sheets', ''):
            if sheet['properties']['title'] == title:
                return sheet['properties']['sheetId']
        return None

    def _rename_worksheet(self, old_title: str, new_title: str):
        try:
            request_body = {
                    'requests': [{
                            'updateSheetProperties': {
                                    'properties': {
                                            'sheetId': self._get_sheet_id(old_title),
                                            'title': new_title
                                    },
                                    'fields': 'title'
                            }
                    }]
            }
            self._service.spreadsheets().batchUpdate(
                    spreadsheetId=self._document_id, body=request_body).execute()
        except HttpError as error:
            print(f"An error occurred: {error}")
            return error

    def _create_statement_worksheet(self):
        try:
            sheets = self._spreadsheet.get('sheets', '')
            sheet_names = [sheet['properties']['title'] for sheet in sheets]

            response = None
            sheet_id = None
            if self._config.document_id is None:
                self._rename_worksheet("Sheet1", self._config.statement_date)
            elif self._config.statement_date not in sheet_names:
                request_body = {
                    'requests': [{
                            'addSheet': {
                                    'properties': {
                                            'title': self._config.statement_date,
                                            'index': 0
                                    }
                            }
                    }]
                }
                response = self._service.spreadsheets().batchUpdate(
                            spreadsheetId=self._document_id, body=request_body).execute()

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
            if sheet_id is None:
                sheet_id = self._get_sheet_id(self._config.statement_date)
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
            self._service.spreadsheets().batchUpdate(
                    spreadsheetId=self._document_id, body=request_body).execute()
        except HttpError as error:
            print(f"An error occurred: {error}")
            return error

    def _get_worksheet_header(self):
        try:
            range_name = "{}!1:1".format(self._config.statement_date)
            result = self._service.spreadsheets().values().get(spreadsheetId=self._document_id, range=range_name).execute()
            self._worksheet_header = result.get('values', [])
        except HttpError as error:
            print(f"An error occurred: {error}")
            return error

    def _is_statement_worksheet_header_valid(self):
        if len(self._worksheet_header) == 0:
            return True
        elif self._worksheet_header == [Transaction.TRANSACTION_COLUMNS + self._config.alloc_columns]:
            return True
        return False

    def _set_statement_worksheet_header(self):
        range_name = "{}!1:1".format(self._config.statement_date)
        try:
            body = {"values": [Transaction.TRANSACTION_COLUMNS + self._config.alloc_columns]}
            result = (
                self._service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=self._document_id,
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

    def _create_statement_worksheet_header(self):
        self._get_worksheet_header()
        if not self._is_statement_worksheet_header_valid():
            print("ERROR: Worksheet header appears to be invalid.")
            print("\tGot Header:      {}".format(self._worksheet_header))
            print("\tExpected Header: {}".format([Transaction.TRANSACTION_COLUMNS + self._config.alloc_columns]))
            exit(1)
        if len(self._worksheet_header) == 0:
            self._set_statement_worksheet_header()

    def _get_statement_worksheet_transactions(self):
        try:
            range_name = "{}!A:F".format(self._config.statement_date)
            result = self._service.spreadsheets().values().get(spreadsheetId=self._document_id, range=range_name).execute()
            self._worksheet_transactions = result.get('values', [])

            # Delete the header.
            del self._worksheet_transactions[0]

            # If the last field is empty (usually the memo field), google sheets
            # returns a truncated transaction. When importing a batch of
            # transactions, truncated transactions fail to be detected and we end up
            # reprocessing old transactions.
            self._worksheet_transactions = [row + [None] * (len(Transaction.TRANSACTION_COLUMNS) - len(row)) for row in self._worksheet_transactions]

            print(f"Found {(len(self._worksheet_transactions))} worksheet transactions.")
        except HttpError as error:
            print(f"An error occurred: {error}")
            return error

    def _get_ofx_transactions(self):
        self._transactions = []
        banktranlist = self._ofx.bankmsgsrsv1[0].stmtrs.banktranlist

        for t in banktranlist:
            self._transactions.append(Transaction(t))

        return True

    def _allocate_ofx_transaction(self, transaction: Transaction, index: int):
        print("\nAllocate transaction {} of {}:".format(index + 1, len(self._transactions)))
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

    def _allocate_ofx_transactions(self):
        print("Found {} OFX transactions.".format(len(self._transactions)))

        self._ofx_transactions = []
        for i, t in enumerate(self._transactions):
            ofx_transaction = t.to_list()

            # Testing a transaction for prior categorization should be as simple as
            # looking for an existing FITID value. Section 3.2.3 of the OFX v2.3
            # specification says that, "FITIDs must be unique within the scope of an
            # account". Unfortunately, some institutions occasionally reuse FITID
            # values, so we are forced to compare the entire transaction tuple. This
            # approach will fail if two affected transactions during a statement
            # period have identical tuples, but there is nothing we can do about
            # that short of requiring an unreasonable amount of human intervention.
            if ofx_transaction not in self._worksheet_transactions:
                allocations = self._allocate_ofx_transaction(transaction=t, index=i)
                self._ofx_transactions.append(ofx_transaction + allocations)
            else:
                print("Skipping allocated transaction {} of {}:".format(i + 1, len(self._transactions)))

    def _write_ofx_transactions(self):
        if len(self._ofx_transactions) <= 0:
            print("No transactions to write...")
            return 0

        range_name = "{}!R{}C1:R{}C{}".format(self._config.statement_date,
                            len(self._worksheet_transactions) + 2,
                            len(self._worksheet_transactions) + 1 + len(self._ofx_transactions),
                            len(self._ofx_transactions[0]))
        try:
            body = {"values": self._ofx_transactions}
            result = (
                self._service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=self._document_id,
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

    def console(self):
        self._parse_ofx_file()
        self._get_google_creds()

        self._create_spreadsheet()
        self._create_statement_worksheet()
        self._create_statement_worksheet_header()

        self._get_statement_worksheet_transactions()
        self._get_ofx_transactions()
        self._allocate_ofx_transactions()
        self._write_ofx_transactions()
