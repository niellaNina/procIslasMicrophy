#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 13:06:09 2024

Unit tests for functions in the functions.py file
Commented functions have no testing yet

@author: ninalar
"""

from functions import sec_since_midnigth
import pytest
import datetime as dt

#def datetime64_to_time_of_day(datetime64_array):
 
#def get_decimal_hours(ds):
    

def test_sec_since_midnigth():
   assert sec_since_midnigth(dt.datetime(2023,3,1,1,00,00)) == 3600
   
#def resolve_date(year, day_num):