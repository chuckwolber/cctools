
from ccct.allocation import Allocation
from datetime import datetime


class Transaction():
    """Transactions generally follow single-entry accounting rules.

    A traditional human readable credit card statement tends to use a single
    column to list charges as positive amounts and payments as negative amounts.
    The total at the bottom is usually a positive value referring to what the
    consumer owes the credit card company. This is an example of single-entry
    accounting, where you are only concerned with cashflow and do not care to
    make a distinction between various categories like revenue and expenses.

    In contrast, OFX files (like QFX) are a bit closer to traditional double
    entry accounting, except transaction amounts can be negative. True double
    entry accounting tends to use positive transaction amounts and relies on the
    meaning of CREDIT and DEBIT with respect to specific account type (e.g.
    asset, liability, capital, revenue, expense) to track the relevant financial
    picture.

    Section 3.2.9.2 of the OFX v2.3 specification explains:

        "An exception to the above rules are signage of the amount in statement
         download transactions, wrapped within <STMTTRN></STMTTRN> tags. The
         amounts in these transactions should be signed on the basis of how the
         account is affected, e.g. a <TRNTYPE>DEBIT should have a negative
         <TRNAMT> value."

    Section 11.4.4.1 of the OFX v2.3 specifiction further clarifies:

        "Transaction amounts are signed from the perspective of the customer.
         For example, a credit card payment is positive while a credit card
         purchase is negative."
    """
    TRANSACTION_COLUMNS = ["FITID", "DTPOSTED", "TRNTYPE", "TRNAMT", "NAME", "MEMO"]

    fitid: str
    dtposted: datetime
    trntype: str
    trnamt: float
    name: str
    memo: str
    allocation: Allocation

    def __init__(self, transaction):
        self.fitid      = transaction.fitid
        self.dtposted   = transaction.dtposted
        self.trntype    = transaction.trntype
        self.trnamt     = float(transaction.trnamt)
        self.name       = transaction.name
        self.memo       = transaction.memo
        self.allocation = Allocation(self.trnamt)

        if not isinstance(self.fitid, str):
            raise ValueError("Error: FITID is not a string.")
        if not isinstance(self.dtposted, datetime):
            raise ValueError("Error: DTPOSTED is not a datetime object.")

        # Currently only supporting CREDIT and DEBIT. Submit a bug if you find
        # examples of others being used. OFX v2.3 section 11.4.4.3 lists the
        # full set of valid values.
        if self.trntype != "CREDIT" and self.trntype != "DEBIT":
            raise ValueError("Error: Unknown transaction type.\n{}".format(str(transaction)))

        # OFX v2.3 sections 3.2.9.2 and 11.4.4.1 specify sign value from the
        # perspective of the customer.
        if self.trntype == "CREDIT" and self.trnamt < 0:
            raise ValueError("Error: Negative credit detected!\n{}".format(str(transaction)))
        if self.trntype == "DEBIT"  and self.trnamt > 0:
            raise ValueError("Error: Positive debit detected!\n{}".format(str(transaction)))

        if not isinstance(self.name, str):
            raise ValueError("Error: NAME is not a string.")

    def to_list(self) -> list:
        arr = [''] * len(self.TRANSACTION_COLUMNS)
        arr[self.TRANSACTION_COLUMNS.index("FITID")]    = self.fitid
        arr[self.TRANSACTION_COLUMNS.index("DTPOSTED")] = str(self.dtposted)
        arr[self.TRANSACTION_COLUMNS.index("TRNTYPE")]  = self.trntype
        arr[self.TRANSACTION_COLUMNS.index("TRNAMT")]   = self.trnamt
        arr[self.TRANSACTION_COLUMNS.index("NAME")]     = self.name
        arr[self.TRANSACTION_COLUMNS.index("MEMO")]     = self.memo
        return arr

    def print(self):
        print("\tTID:\t{}".format(self.fitid))
        print("\tDate:\t{}".format(self.dtposted.isoformat()))
        print("\tType:\t{}".format(self.trntype))
        print("\tAmount:\t{}".format(str(self.trnamt)))
        print("\tName:\t{}".format(self.name))
        print("\tMemo:\t{}".format(self.memo))