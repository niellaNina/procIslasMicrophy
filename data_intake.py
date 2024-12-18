#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  2 09:41:33 2024

@author: ninalar
"""

def read_sic(f_date):
    # Reading in sea ice concentration from satellite.
    # INPUT:
    # date: date in string format "YYYYMMDD" or as a datetime object
    #
    # OUTPUT:
    # sic_ds: xarray object of sea ice cconcentration(sic)  values for the given date
    
    # ---Packages---
    import xarray as xr
    
    
   # f_date='20230326' # testing
    # check if date is in the right format
    
    # Local disk path of data:
    path_in = '../sea_ice_satellite/' # path to processed satellite files
    sic_file = f'asi-n6250-{f_date}-5.4_regridded.nc' # structure of cip text-file names
    
    # ---Data---
    # Read in single satellite data file, give error if file does not exist
    try:
        sic_ds = xr.open_dataset(path_in + sic_file)
        # rename data variable and update attributes
        sic_ds['sic'] = sic_ds['__xarray_dataarray_variable__'].assign_attrs(units="Percent", description="Sea Ice Concentration")
        sic_ds = sic_ds.drop_vars(['__xarray_dataarray_variable__'])
    
        return sic_ds
        sic_ds.close()
    except:
        print(f"No file exists for date: {f_date}")

