# SPDX-License-Identifier: MIT

import unittest

from .. import ccct

class TestAllocation(unittest.TestCase):
    invalid_col = "x"
    cols = ["a", "b", "c", "d", "e", "f"]
    cols_map = ["aa", "bb", "cc", "dd", "ee", "ff"]
    amount = 1.25

    def tearDown(self):
        ccct.Allocation.ALLOC_COLUMNS = None
        ccct.Allocation.ALLOC_COLUMNS_MAP = None

    def test_allocation_uninitialized(self):
        self.assertRaises(ValueError, ccct.Allocation, 1.11)

    def test_allocation_invalid_float(self):
        ccct.Allocation.init_cols([])
        self.assertRaises(ValueError, ccct.Allocation, amount="NOTAFLOAT")

    def test_allocation_init(self):
        num_cols = 6
        ccct.Allocation.init_cols([0.0]*num_cols)
        a = ccct.Allocation(self.amount)
        self.assertEqual(len(a.allocation), num_cols)
        self.assertEqual(a.amount_orig, -1*self.amount)
        self.assertEqual(a.amount_orig, a.amount_curr)
        self.assertTrue(a.negative)
        self.assertEqual(a.to_list(), ['']*len(self.cols))
        self.assertEqual(a.get_allocations_sum(), 0.0)

    def test_allocation_cols(self):
        ccct.Allocation.init_cols(self.cols)
        a = ccct.Allocation(self.amount)
        self.assertEqual(a.get_paired_allocations(), '[' + ', '.join(self.cols) + ']')
        self.assertEqual(a.to_list(), ['']*len(self.cols))
        self.assertEqual(a.get_allocations_sum(), 0.0)

    def test_allocation_cols_map(self):
        ccct.Allocation.init_cols(self.cols)
        ccct.Allocation.init_cols_map(self.cols_map)
        a = ccct.Allocation(self.amount)
        self.assertEqual(a.get_paired_allocations(), '[' + ', '.join(self.cols + ['?']) + ']')
        self.assertEqual(a.to_list(), ['']*len(self.cols))
        self.assertEqual(a.get_allocations_sum(), 0.0)

    def test_allocation_valid_catetory(self):
        ccct.Allocation.init_cols(self.cols)
        a = ccct.Allocation(self.amount)
        for col in self.cols:
            self.assertTrue(a._Allocation__is_valid_category(col))

    def test_allocation_amount_invalid_col(self):
        ccct.Allocation.init_cols(self.cols)
        a = ccct.Allocation(self.amount)
        a.allocate_amount(self.invalid_col, -1*self.amount)
        self.assertEqual(a.to_list(), ['']*len(self.cols))
        self.assertEqual(a.get_paired_allocations(), '[' + ', '.join(self.cols) + ']')
        self.assertEqual(a.get_allocations_sum(), 0.0)

    def test_allocation_amount_invalid(self):
        ccct.Allocation.init_cols(self.cols)
        a = ccct.Allocation(-1*self.amount)
        a.allocate_amount(self.cols[0], "NOTANUMBER")
        self.assertEqual(a.to_list(), ['']*len(self.cols))
        self.assertEqual(a.get_paired_allocations(), '[' + ', '.join(self.cols) + ']')
        self.assertEqual(a.get_allocations_sum(), 0.0)

    def test_allocation_amount_wrong_sign_1(self):
        ccct.Allocation.init_cols(self.cols)
        a = ccct.Allocation(self.amount)
        a.allocate_amount(self.cols[0], self.amount)
        self.assertEqual(a.to_list(), ['']*len(self.cols))
        self.assertEqual(a.get_paired_allocations(), '[' + ', '.join(self.cols) + ']')
        self.assertEqual(a.get_allocations_sum(), 0.0)

    def test_allocation_amount_wrong_sign_2(self):
        ccct.Allocation.init_cols(self.cols)
        a = ccct.Allocation(-1*self.amount)
        a.allocate_amount(self.cols[0], -1*self.amount)
        self.assertEqual(a.to_list(), ['']*len(self.cols))
        self.assertEqual(a.get_paired_allocations(), '[' + ', '.join(self.cols) + ']')
        self.assertEqual(a.get_allocations_sum(), 0.0)

    def test_allocation_amount_equal(self):
        ccct.Allocation.init_cols(self.cols)
        a = ccct.Allocation(-1*self.amount)
        allocs = ['']*len(self.cols)
        allocs[0] = self.amount
        z = [f"{a}({b})" if b != '' else a for a, b in zip(self.cols, allocs)]
        a.allocate_amount(self.cols[0], allocs[0])
        self.assertEqual(a.to_list(), allocs)
        self.assertEqual(a.get_paired_allocations(), '[' + ', '.join(z) + ']')
        self.assertEqual(a.get_allocations_sum(), allocs[0])

    def test_allocation_amount_greater_positive(self):
        ccct.Allocation.init_cols(self.cols)
        a = ccct.Allocation(-1*self.amount)
        allocs = ['']*len(self.cols)
        allocs[0] = self.amount
        z = [f"{a}({b})" if b != '' else a for a, b in zip(self.cols, allocs)]
        a.allocate_amount(self.cols[0], allocs[0]*10)
        self.assertEqual(a.to_list(), allocs)
        self.assertEqual(a.get_paired_allocations(), '[' + ', '.join(z) + ']')
        self.assertEqual(a.get_allocations_sum(), allocs[0])

    def test_allocation_amount_greater_negative(self):
        ccct.Allocation.init_cols(self.cols)
        a = ccct.Allocation(self.amount)
        allocs = ['']*len(self.cols)
        allocs[0] = -1*self.amount
        z = [f"{a}({b})" if b != '' else a for a, b in zip(self.cols, allocs)]
        a.allocate_amount(self.cols[0], allocs[0]*10)
        self.assertEqual(a.to_list(), allocs)
        self.assertEqual(a.get_paired_allocations(), '[' + ', '.join(z) + ']')
        self.assertEqual(a.get_allocations_sum(), allocs[0])

    def test_allocation_amount_multiple(self):
        ccct.Allocation.init_cols(self.cols)
        a = ccct.Allocation(-1*self.amount)
        allocs = ['']*len(self.cols)

        allocs[0] = 1.0
        z = [f"{a}({b})" if b != '' else a for a, b in zip(self.cols, allocs)]
        a.allocate_amount(self.cols[0], allocs[0])
        self.assertEqual(a.to_list(), allocs)
        self.assertEqual(a.get_paired_allocations(), '[' + ', '.join(z) + ']')
        self.assertEqual(a.get_allocations_sum(), allocs[0])

        allocs[1] = self.amount - allocs[0]
        z = [f"{a}({b})" if b != '' else a for a, b in zip(self.cols, allocs)]
        a.allocate_amount(self.cols[1], 2.0)
        self.assertEqual(a.to_list(), allocs)
        self.assertEqual(a.get_paired_allocations(), '[' + ', '.join(z) + ']')
        self.assertEqual(a.get_allocations_sum(), self.amount)

    def test_allocation_amount_reset(self):
        ccct.Allocation.init_cols(self.cols)
        a = ccct.Allocation(-1*self.amount)
        allocs = ['']*len(self.cols)

        allocs[2] = 1.0
        allocs[3] = 0.1
        z = [f"{a}({b})" if b != '' else a for a, b in zip(self.cols, allocs)]
        a.allocate_amount(self.cols[2], allocs[2])
        a.allocate_amount(self.cols[3], allocs[3])
        self.assertEqual(a.to_list(), allocs)
        self.assertEqual(a.get_paired_allocations(), '[' + ', '.join(z) + ']')
        self.assertEqual(a.get_allocations_sum(), allocs[2] + allocs[3])
        self.assertEqual(a.amount_curr, self.amount - allocs[2] - allocs[3])

        allocs[2] = 0.1
        z = [f"{a}({b})" if b != '' else a for a, b in zip(self.cols, allocs)]
        a.allocate_amount(self.cols[2], allocs[2])
        self.assertEqual(a.to_list(), allocs)
        self.assertEqual(a.get_paired_allocations(), '[' + ', '.join(z) + ']')
        self.assertEqual(a.get_allocations_sum(), allocs[2] + allocs[3])
        self.assertEqual(a.amount_curr, round(self.amount - allocs[2] - allocs[3], 2))