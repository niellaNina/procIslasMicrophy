#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 19 12:46:01 2024

@author: ninalar
"""

#### ---Functions---

# from yariv stack overflow
def datetime64_to_time_of_day(datetime64_array):
    """
    Return a new array. For every element in datetime64_array return the time of day (since midnight).
    >>> datetime64_to_time_of_day(np.array(['2012-01-02T01:01:01.001Z'],dtype='datetime64[ms]'))
    array([3661001], dtype='timedelta64[ms]')
    >>> datetime64_to_time_of_day(np.datetime64('2012-01-02T01:01:01.001Z','[ms]'))
    numpy.timedelta64(3661001,'ms')
    """
    day = datetime64_array.astype('datetime64[D]').astype(datetime64_array.dtype)
    time_of_day = datetime64_array - day
    return time_of_day

def get_decimal_hours(ds):
    # subtracting 'time_take_off' from observation 'time'
    # this results in a numpy timedelta64 object in nanoseconds
    ns = list(ds.coords['time'].values-np.datetime64(ds.attrs['time_take_off']))

    # transform ns np.timedelta64 to pd.timedelta.
    # pd.timedelta format has easier to use transformations between nanoseconds, seconds, hours, days
    # will keep decimals/floating number
    hours = pd.to_timedelta(ns[:])/ dt.timedelta (hours=1)
    return(hours)

def sec_since_midnigth(dt):
    # calculating the seconds since midnight from a given datetime object
    # requires: import datetime
    # input: datetime object
    # returns: seconds since midnight
    midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds = (dt - midnight).total_seconds()
    return(seconds)

def resolve_date(year, day_num):
    # Resolving date from day number (day_num) and year
    # Input: 
    #       day_num: number of days since 01.01
    #       year: Year in YYYY format
    # Output: date in format YYYY-MM-DD
    # dependent of packages: from datetime import timedelta, from dateutil import parser
 
    # creating date string
    date_str = str(int(year)) + "-01-01"  # January 1st of the given year
    date_obj = parser.parse(date_str)  # parse date string to datetime object
 
    # adding days to datetime object
    date_res = date_obj + timedelta(days=int(day_num) - 1)
 
    # formatting result date
    res = date_res.strftime("%Y-%m-%d")
    return res