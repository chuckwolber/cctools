# SPDX-License-Identifier: MIT

import datetime
import sys
import unittest

from . import args
from . import const
from .. import ccct

class TestTransaction(unittest.TestCase):
    class T():
            def __init__(self, fitid, dtposted, trntype, trnamt, name, memo):
                self.fitid      = fitid
                self.dtposted   = dtposted
                self.trntype    = trntype
                self.trnamt     = trnamt
                self.name       = name
                self.memo       = memo

    argv = sys.argv

    def setUp(self):
        sys.argv = sys.argv[0:1]
        ccct._args = None
        ccct._ofx = None

    def tearDown(self):
        sys.argv = self.argv

    def test__get_ofx_transactions(self):
        args.set_all_required()
        args.set_ofx_file(const.ASSETS_DIR + "/export.valid.qfx")
        args.set_config_file(const.VALID_CONFIG)
        self.assertTrue(ccct._resolve_config(None))
        self.assertTrue(ccct._parse_ofx_file())
        self.assertTrue(ccct._get_ofx_transactions())
        self.assertTrue(len(ccct._transactions) == 26)

        for t in ccct._transactions:
            self.assertIsNotNone(t.fitid)
            self.assertIsNotNone(t.dtposted)
            self.assertIsNotNone(t.trntype)
            self.assertIsNotNone(t.trnamt)
            self.assertIsNotNone(t.name)
            self.assertIsNotNone(t.allocation)

            self.assertIsInstance(t.fitid, str)
            self.assertIsInstance(t.dtposted, datetime.datetime)
            self.assertIsInstance(t.trntype, str)
            self.assertIsInstance(t.trnamt, float)
            self.assertIsInstance(t.name, str)
            self.assertIsInstance(t.allocation, ccct.Allocation)

            if t.memo != None:
                self.assertIsInstance(t.memo, str)

        tref = (2024, 11, 1, 12, 0, 0, 4, 306, 0)
        for t in ccct._transactions[0:4]:
            tt = t.dtposted.timetuple()
            self.assertTrue(tt == tref)
            self.assertTrue(t.trntype == "CREDIT")
            self.assertTrue(t.name == "PAYMENT - THANK YOU")

        i = 0
        for t in ccct._transactions[4:]:
            i += 1
            tt = t.dtposted.timetuple()
            self.assertTrue(t.trntype == "DEBIT")
            self.assertTrue(tt.tm_mday == i)

        tl = [
                ['8423858PG12AM3XZE', '2024-11-01 12:00:00+00:00', 'CREDIT', 123.45, 'PAYMENT - THANK YOU', None],
                ['8423858PG12AM3XZE', '2024-11-01 12:00:00+00:00', 'CREDIT', 8675.3, 'PAYMENT - THANK YOU', None],
                ['8423858PG12AM3XZE', '2024-11-01 12:00:00+00:00', 'CREDIT', 123.45, 'PAYMENT - THANK YOU', None],
                ['8423858PG12AM3XZE', '2024-11-01 12:00:00+00:00', 'CREDIT', 999.99, 'PAYMENT - THANK YOU', None],
                ['20241126000InterestChargeonPurchases', '2024-11-01 12:00:00+00:00', 'DEBIT', 0.0, 'Interest Charge on Purchases', None],
                ['2445106NS8WXQ9TXV', '2024-11-02 12:00:00+00:00', 'DEBIT', -1.96, 'ABCDEFG\t 123-456', 'ABCDEFG\t 800-555-1212 OR'],
                ['20241126000Redacted1', '2024-11-03 12:00:00+00:00', 'DEBIT', 0.0, 'Transaction 1', None],
                ['20241126000Redacted2', '2024-11-04 12:00:00+00:00', 'DEBIT', 0.0, 'Transaction 2', None],
                ['Redacted3', '2024-11-05 12:00:00+00:00', 'DEBIT', -15.96, 'Transaction 3', 'Memo for Transaction 3'],
                ['Redacted4', '2024-11-06 12:00:00+00:00', 'DEBIT', -49.6, 'Transaction 4', 'Memo for Transaction 4'],
                ['Redacted5', '2024-11-07 12:00:00+00:00', 'DEBIT', -42.98, 'Transaction 5', 'Memo for Transaction 5'],
                ['Redacted6', '2024-11-08 12:00:00+00:00', 'DEBIT', -55.0, 'Transaction 6', 'Memo for Transaction 6'],
                ['Redacted7', '2024-11-09 12:00:00+00:00', 'DEBIT', -1.2, 'Transaction 7', 'Memo for Transaction 7'],
                ['Redacted8','2024-11-10 12:00:00+00:00', 'DEBIT', -8.23, 'Transaction 8', 'Memo for Transaction 8'],
                ['Redacted9', '2024-11-11 12:00:00+00:00', 'DEBIT', -77.51, 'Transaction 9', 'Memo for Transaction 9'],
                ['Redacted10', '2024-11-12 12:00:00+00:00', 'DEBIT', -35.0, 'Transaction 10', 'Memo for Transaction 10'],
                ['Redacted11', '2024-11-13 12:00:00+00:00', 'DEBIT', -24.0, 'Transaction 11', 'Memo for Transaction 11'],
                ['Redacted12', '2024-11-14 12:00:00+00:00', 'DEBIT', -33.05, 'Transaction 12', 'Memo for Transaction 12'],
                ['Redacted13', '2024-11-15 12:00:00+00:00', 'DEBIT', -49.55, 'Transaction 13', 'Memo for Transaction 13'],
                ['Redacted14', '2024-11-16 12:00:00+00:00', 'DEBIT', -16.35, 'Transaction 14', 'Memo for Transaction 14'],
                ['Redacted15', '2024-11-17 12:00:00+00:00', 'DEBIT', -30.63, 'Transaction 15', 'Memo for Transaction 15'],
                ['Redacted16', '2024-11-18 12:00:00+00:00', 'DEBIT', -64.47, 'Transaction 16', 'Memo for Transaction 16'],
                ['Redacted17', '2024-11-19 12:00:00+00:00', 'DEBIT', -149.55, 'Transaction 17', 'Memo for Transaction 17'],
                ['Redacted18', '2024-11-20 12:00:00+00:00', 'DEBIT', -126.35, 'Transaction 18', 'Memo for Transaction 18'],
                ['Redacted19', '2024-11-21 12:00:00+00:00', 'DEBIT', -309.63, 'Transaction 19', 'Memo for Transaction 19'],
                ['Redacted20', '2024-11-22 12:00:00+00:00', 'DEBIT', -964.47, 'Transaction 20', 'Memo for Transaction 20']
        ]
        for i in range(0,26):
            self.assertEqual(ccct._transactions[i].to_list(), tl[i])

    def test_transaction_invalid_trnamt(self):
        args.set_all_required()
        args.set_ofx_file(const.ASSETS_DIR + "/export.valid.qfx")
        args.set_config_file(const.VALID_CONFIG)
        self.assertTrue(ccct._resolve_config(None))
        t = self.T(fitid=None, dtposted=None, trntype=None, trnamt="INVALIDAMOUNT", name=None, memo=None)
        self.assertRaises(ValueError, ccct.Transaction, t)

    def test_transaction_invalid_fitid(self):
        args.set_all_required()
        args.set_ofx_file(const.ASSETS_DIR + "/export.valid.qfx")
        args.set_config_file(const.VALID_CONFIG)
        self.assertTrue(ccct._resolve_config(None))
        t = self.T(fitid=None, dtposted=None, trntype=None, trnamt=1.11, name=None, memo=None)
        self.assertRaises(ValueError, ccct.Transaction, t)

    def test_transaction_invalid_dtposted(self):
        args.set_all_required()
        args.set_ofx_file(const.ASSETS_DIR + "/export.valid.qfx")
        args.set_config_file(const.VALID_CONFIG)
        self.assertTrue(ccct._resolve_config(None))
        t = self.T(fitid="8423858PG12AM3XZE", dtposted=None, trntype="CREDIT", trnamt=1.11, name=None, memo=None)
        self.assertRaises(ValueError, ccct.Transaction, t)

    def test_trasaction_unknown_type(self):
        args.set_all_required()
        args.set_ofx_file(const.ASSETS_DIR + "/export.valid.qfx")
        args.set_config_file(const.VALID_CONFIG)
        self.assertTrue(ccct._resolve_config(None))
        t = self.T(fitid="8423858PG12AM3XZE", dtposted=datetime.datetime(2024, 11, 5, 12, 0, tzinfo=datetime.timezone.utc),
                   trntype="UNKNOWN", trnamt=1.11, name=None, memo=None)
        self.assertRaises(ValueError, ccct.Transaction, t)

    def test_transaction_invalid_credit(self):
        args.set_all_required()
        args.set_ofx_file(const.ASSETS_DIR + "/export.valid.qfx")
        args.set_config_file(const.VALID_CONFIG)
        self.assertTrue(ccct._resolve_config(None))
        t = self.T(fitid="8423858PG12AM3XZE", dtposted=datetime.datetime(2024, 11, 5, 12, 0, tzinfo=datetime.timezone.utc),
                   trntype="CREDIT", trnamt=-1.11, name=None, memo=None)
        self.assertRaises(ValueError, ccct.Transaction, t)

    def test_transaction_invalid_debit(self):
        args.set_all_required()
        args.set_ofx_file(const.ASSETS_DIR + "/export.valid.qfx")
        args.set_config_file(const.VALID_CONFIG)
        self.assertTrue(ccct._resolve_config(None))
        t = self.T(fitid="8423858PG12AM3XZE", dtposted=datetime.datetime(2024, 11, 5, 12, 0, tzinfo=datetime.timezone.utc),
                   trntype="DEBIT", trnamt=1.11, name=None, memo=None)
        self.assertRaises(ValueError, ccct.Transaction, t)

    def test_transaction_invalid_name(self):
        args.set_all_required()
        args.set_ofx_file(const.ASSETS_DIR + "/export.valid.qfx")
        args.set_config_file(const.VALID_CONFIG)
        self.assertTrue(ccct._resolve_config(None))
        t = self.T(fitid="8423858PG12AM3XZE", dtposted=datetime.datetime(2024, 11, 5, 12, 0, tzinfo=datetime.timezone.utc),
                   trntype="DEBIT", trnamt=-1.11, name=None, memo=None)
        self.assertRaises(ValueError, ccct.Transaction, t)

    def test_transaction_to_list(self):
        args.set_all_required()
        args.set_ofx_file(const.ASSETS_DIR + "/export.valid.qfx")
        args.set_config_file(const.VALID_CONFIG)
        self.assertTrue(ccct._resolve_config(None))
        t = self.T(fitid="8423858PG12AM3XZE", dtposted=datetime.datetime(2024, 11, 5, 12, 0, tzinfo=datetime.timezone.utc),
                   trntype="DEBIT", trnamt=-1.11, name="NAME", memo=None)
        tr = ccct.Transaction(t)
        self.assertTrue(tr.to_list()[0] == "8423858PG12AM3XZE")
        self.assertTrue(tr.to_list()[1] == '2024-11-05 12:00:00+00:00')
        self.assertTrue(tr.to_list()[2] == "DEBIT")
        self.assertTrue(tr.to_list()[3] == -1.11)
        self.assertTrue(tr.to_list()[4] == "NAME")
        self.assertTrue(tr.to_list()[5] == None)
