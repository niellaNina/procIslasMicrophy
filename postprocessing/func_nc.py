#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  23 13:30:26 2025
Scripts related to handling netcdfs in the islas processing

@author: ninalar
"""

def nc_save_with_check(savefile ,xds):
    """Check if a netCDF file exists. Overwrite existing if user accepts, create new if not existing.

    Args:
        savefile: Path to netCDF file
        xds: xarray.DataSet that user wants to write to savefile
    
    """

    import xarray as xr
    import os

    # Check if the file exists
    if os.path.exists(savefile):
        overwrite = input(f'The file {savefile} exists. Do you want to overwrite it?(y/n)')
        if overwrite.lower() in ["yes", "y"]:
            print(f'Saving to {savefile}')
            xds.to_netcdf(path=savefile, mode='a')
        else:
            print("Exiting...")
    else:
        xds.to_netcdf(path=savefile, mode='w')
        print(f'Saving to {savefile}')
        
    return

def floor_to_sec_res(ds, time_dim):
    """ Function to floor the time to whole seconds

    Args:
        ds: xarray dataset with time dimention variable defined by "time_dim"
        time_dim: name of xarray variable containing time dimention in seconds.
    
    Returns:
        the ds with the time_dim floored to closest whole seconds
    """
    
    import pandas as pd
    # Convert to pandas datetime index
    datetime_index = pd.to_datetime(ds[time_dim].values) # turn into datetime index
    floored_time = datetime_index.floor('s') # floor on seconds

    return ds.assign_coords({time_dim: floored_time})