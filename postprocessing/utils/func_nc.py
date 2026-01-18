#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  23 13:30:26 2025
Scripts related to handling netcdfs in the islas processing

@author: ninalar
"""

def floor_to_sec_res(ds, time_dim):
    """ Function to floor the time to whole seconds

    This function relies on the "pandas" package

    Parameters
    ---------- 
        ds: Xarray.DataSet
            xarray dataset with time dimention variable defined by "time_dim"
        time_dim: str
            name of xarray variable containing time dimention in seconds.
    
    Returns
    ----------
        ds: Xarray.DataSet
            the original ds with the time_dim floored to closest whole seconds
    """
    
    import pandas as pd

    # Convert to pandas datetime index
    datetime_index = pd.to_datetime(ds[time_dim].values) # turn into datetime index
    floored_time = datetime_index.floor('s') # floor on seconds

    return ds.assign_coords({time_dim: floored_time})

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
    """Resolving date from day number (day_num) and year 

    This function relies on the 'datetime' and 'dateutil' packages

    Parameters
    ----------
    day_num: int
        number of days since 01.01
    year: int
        Year in YYYY format

    Returns
    ----------
    res:
        resulting date in format YYYY-MM-DD
    """
  
    from datetime import timedelta
    from dateutil import parser
 
    # creating date string
    date_str = year.astype('int').astype('str') + "-01-01"  # January 1st of the given year
    date_obj = date_str.apply(parser.parse)  # parse date string to datetime object
    
    # creating the days in proper format from series'
    day_obj = day_num.apply(lambda x: timedelta(days=int(x)-1))
 
    # adding days to datetime object
    res = date_obj + day_obj
 
    return res

def find_unique_listkey(dict, sub_key):
    """Count number of unique keys in a dictionary 

    Parameters
    ----------
    dict: dict
        dictionary containing keys
    sub_key: str
        

    Returns
    ----------
    set(values): set
        the unique values found
    """
    values = []
    
    for key in dict:
        if sub_key in dict[key].keys():
          values.append(dict[key][sub_key][0])
    
    # Return all unique values
    return set(values)



