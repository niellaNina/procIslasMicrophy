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


def mass_param(param, xds, name_add=""):
    # Function to calculate the mass and IWC based on the given mass-parametrization scheme
    # Input: 
    # --- param: str
    #       parametrization scheme to use, available options: Heymsfield2010, Brown&Francis
    # --- xds: xarray DataSet
    #        xarray containing the original CIP bins, sizes and concentrations. The sizing method used when preprocessing the 2Dprobe data will affect
    #        the results from this function. 
    #        Following Wu and McFarquhar (2016) the diameter of smallest circle enclosing the particle is recommended, and used for the ISLAS dataset.  
    # --- varname: str
    #        string to add to 'MASS' and 'IWC' to set variable names (to use for identification if multiple parametrizations are used on one dataset)
    #        Default: ""           
    # Returns:
    # --- xds: xarray DataSet
    #        original xarray updated with the new parameters
    #
    # Example runs: 
    # ---
    #     f_cip_xds, massdim_param = mass_param('Heymsfield2010',f_cip_xds,'_H10')
    #     f_cip_xds, massdim_param = mass_param('Brown&Francis95',f_cip_xds,'_BF95')
    #     f_cip_xds, massdim_param = mass_param('Heymsfield2001',f_cip_xds,'_H01')

    # parametrization options
    massdim_param = {'Heymsfield2010': {'a':0.0121, 'b':1.9, 
                                        'description': 'CIP particle mass calculated from the Heymsfield (2010) mass-dimention relationship for warm clouds (T > -25°C). Computed the using alpha=0.0121, beta=1.9.',
                                        'doi': ""},
                 'Brown&Francis95': {'a':0.00294, 'b':1.9,
                                     'description': 'CIP particle mass calculated from the Brown and Francis 1978 mass-dimention relationship. Computed the using alpha=0.00294, beta=1.9.',
                                     'doi': ""},
                 'Heymsfield2010_general': {'a':0.00528,'b':2.1,
                                    'description': 'CIP particle mass calculated from Heymsfield et. al 2010. (also an option in SODA) General relationship to use for all ice cloud types. (when formation mechanisms and temperatures are not known)',
                                    'doi': "10.1175/2010JAS3507.1"}, #this one is technically also from 2010
                 'CRYSTAL': {'a':0.0061,'b':2.05,
                             'description':'CIP particle-mass parametrisation from the CRYSTAL dataset, convectively generated cirrus anvils',
                             'doi': "10.1175/1520-0469(2004)061<0982:EIPDDF>2.0.CO;2"}}


    # get coefficients from parametrization param
    a = massdim_param[param]['a']
    b = massdim_param[param]['b']

    # mass calculation: M = a*D^b
    mvar_name = 'MASS' + name_add
    xds[mvar_name] = a*(xds['MIDBINS']/1.0e4)**b # in m from um, MIDBINS are 25,50,75, ...,1600
    # update metadata for variable
    xds[mvar_name] = xds[mvar_name].assign_attrs({'long_name':f'Mass from {param}',
                                                        'source':'CIP',
                                                        'units':'g'})#,
                                                        #'description': massdim_param[param]['description']})

    # IWC calculation
    var_name = 'IWC' + name_add # adjust parameter name to account for multiple parametrizations in one dataset
    binwidth = xds['MIDBINS'][1].values - xds['MIDBINS'][0].values
    spec = xds['CONCENTRATION']*(binwidth/1.0e6) # unnormalize the concentration
    lwc_per_bin = spec*xds[mvar_name] 
    xds[var_name] = lwc_per_bin.sum(dim='Vector64')
    
    
    return xds, massdim_param

