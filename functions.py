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

def sec_since_midnigth(dt_obj):
    # calculating the seconds since midnight from a given datetime object
    # requires: import datetime
    # input: datetime object
    # returns: seconds since midnight
    from datetime import datetime
    
    if isinstance(dt_obj, datetime):
        midnight = dt_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        seconds = (dt_obj - midnight).total_seconds()
        return(seconds)
    else:
        raise Exception(f'Error: The value "{dt_obj}" passed to sec_since_midnigth was not a datetime')

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

def read_chunky_csv(textfile, sep=[]):
    """
    Splits information of csv files with different "chucks" of data into a list of lists
    Each chunck gets its own list. The number of lines for each chunck does not matter. 
    # requires: import csv
    # input: path to csv-file, separator to split on: default empty list[]
    # returns: list of lists
    """
    import csv
    
    # read in file as a list of lines
    with open(textfile) as infile:
        data_list = list(csv.reader(infile))  

    # The datafiles are composed of 5 different "chunks" of information separated by an empty line: 
    # 0: Processing information, 1: Bin information, 2: Notes, 3: Variable information, 5: Data
    # The number of lines in each chunck varies and depends on the preprocessing, number if image files etc.
    # Separate the chunks by splitting on empty lines []:
    sublists = []
    current_sublist = []

    for item in data_list:
        if item == sep:
            if current_sublist:
                sublists.append(current_sublist)
                current_sublist = []
        else:
            current_sublist.append(item)

    if current_sublist:
        sublists.append(current_sublist)
    
    return sublists