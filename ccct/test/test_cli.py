# SPDX-License-Identifier: MIT

import argparse
import ccct
import sys
import unittest

from pathlib import Path

SCRIPT_DIR = str(Path(__file__).resolve().parent)
ASSETS_DIR = SCRIPT_DIR + "/assets"
INVALID_DIR = "/path/that/should/not/exist"

class CommandLineArgumentsTestCases(unittest.TestCase):
    argv = sys.argv

    def setUp(self):
        sys.argv = sys.argv[0:1]
    
    def tearDown(self):
        sys.argv = self.argv

    def add_arg(self, arg, value):
        if not arg in sys.argv:
            sys.argv.append(arg)
            sys.argv.append(value)
        else:
            i = sys.argv.index(arg) + 1
            sys.argv[i] = value
    
    def get_arg_value(self, arg=None):
        if arg == None:
            raise ValueError("Missing required argument!")
        i = sys.argv.index(arg) + 1
        return 
            
    def add_arg_credential_dir(self, custom=None):
        arg = '--credential-dir'
        if custom == None:
            custom = ASSETS_DIR
        self.add_arg(arg=arg, value=custom)

    def add_arg_bank_id(self, custom=None):
        arg = '--bank-id'
        if custom == None:
            custom = "314074269"
        self.add_arg(arg=arg, value=custom)

    def add_arg_alloc_columns(self, custom=None):
        arg = '--alloc-columns'
        if custom == None:
            custom = 'a:b:c:d:e:f:g'
        self.add_arg(arg=arg, value=custom)

    def add_arg_fx_file(self, custom=None):
        arg = '--fx-file'
        if custom == None:
            custom = ASSETS_DIR + "/export.qfx"
        self.add_arg(arg=arg, value=custom)

    def add_arg_statement_date(self, custom=None):
        arg = '--statement-date'
        if custom == None:
            custom = "20241126"
        self.add_arg(arg=arg, value=custom)

    def add_arg_all_required(self):
        self.add_arg_fx_file()
        self.add_arg_statement_date()


    def test_args_none(self):
        self.assertRaises(argparse.ArgumentError, ccct._parse_args, False)

    def test_args_minimum_required(self):
        self.add_arg_all_required()
        self.assertTrue(ccct._parse_args())

    def test_args_credential_dir(self):
        self.add_arg_all_required()
        with self.subTest():
            self.add_arg_credential_dir()
            self.assertTrue(ccct._parse_args())
        with self.subTest():
            self.add_arg_credential_dir(custom=INVALID_DIR)
            self.assertRaises(argparse.ArgumentError, ccct._parse_args, False)

    def test_args_bank_id(self):
        self.add_arg_all_required()
        with self.subTest():
            self.add_arg_bank_id()
            self.assertTrue(ccct._parse_args())
        for i in ["1", "12345678", "123456789", "1234567890"]:
            with self.subTest(i=i):
                self.add_arg_bank_id(custom=i)
                self.assertRaises(argparse.ArgumentError, ccct._parse_args, False)

    def test_args_alloc_columns(self):
        self.add_arg_all_required()
        with self.subTest():
            self.add_arg_alloc_columns()
            self.assertTrue(ccct._parse_args())
        for i in ["", "x", " "]:
            with self.subTest(i=i):
                self.add_arg_alloc_columns(custom=i)
                self.assertRaises(argparse.ArgumentError, ccct._parse_args, False)

    def test_args_fx_file(self):
        self.add_arg_all_required()
        self.add_arg_fx_file(INVALID_DIR + "/export.qfx")
        self.assertRaises(argparse.ArgumentError, ccct._parse_args, False)

    def test_args_statement_date(self):
        self.add_arg_all_required()
        for i in ["1234567" , "123456789", # Bad String
                  "00000000", "00001201" , # Bad Year
                  "20240001", "20241301" , # Bad Month
                  "20230229", "20240132" , # Bad Day
                  ]:
            with self.subTest(i=i):
                self.add_arg_statement_date(custom=i)
                self.assertRaises(argparse.ArgumentError, ccct._parse_args, False)
