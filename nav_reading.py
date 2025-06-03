#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 28 11:09:21 2024

@author: ninalar
"""

#nav file reading

# from read_cip

import xarray as xr # read netcdf-files
import numpy as np
import warnings
import pandas as pd
import glob # allows for wildcards in filemanagement
import os #get a list of all directories/files

warnings.filterwarnings('ignore', category=DeprecationWarning) # stop the deprecation warnigns from np time management

# functions used fron function.py file
from analysis.functions import sec_since_midnigth

# Local disk path of data:
main_path = '../2022-islas/' # directory with flight data
pads_path = '/microphy/pads/' # path to pads (CIP and CDP data)
nav_file_struct_tdyn = '/ISLAS_SAFIRE-ATR42_CORE_TDYN_1HZ_*_L1_V1.nc' # structure of nav TDYN file names
nav_file_struct_nav = '/ISLAS_SAFIRE-ATR42_CORE_NAV_1HZ_*_L1_V1.nc' # structure of nav NAV file names
drop_flights = ['as220005','as220006'] # flights to drop, (if not all are to be analysed 5 and 6 is in france)
 
flights = [
     f for f in os.listdir(main_path) if os.path.isdir(os.path.join(main_path, f))
]
 
# remove flights to drop using listcomprehension
flights = [i for i in flights if i not in drop_flights]

islas_nav_df = []  # empty list for appending all data to one structure
islas_stats_df = {}  #empty dictionary for collecting flight stats information

for flight in flights:
    # ---- Get NAV data from flight
     
    nav_file = glob.glob(main_path + flight + nav_file_struct_tdyn) # returns a list, must access with file[0]
    nav_xds = xr.open_dataset(nav_file[0]) # returns an xarray dataset
     
    # --- Prepare NAV information for adding to the cdp_df
    # Necessary NAV data: TAS1 (m/s)(variable) and HEIGHT(meter)(coordinate)
    # Use TAS1: the TAS from the Scientific Static/Pitot system, given in m/s, instead of
    # TAS2: the TAS from the Avionic Static/Pitot system (ADC), given in kt, to have correct units
 
    # create pandas series of the variables:
    alt_ds = nav_xds.coords['ALTITUDE'].to_pandas()
    lat_ds = nav_xds.coords['LATITUDE'].to_pandas()
    lon_ds = nav_xds.coords['LONGITUDE'].to_pandas()
    tas1_ds = nav_xds.TAS1.to_pandas() # the TAS from the Scientific Static/Pitot system, given in m/s
    temp_ds = nav_xds.TEMP1.to_pandas() # the Air Static temperature corrected ffrom speed and recovery factor
    pres_ds = nav_xds.PRES.to_pandas() # Static pressure corrected for flow distortion
    dewp_ds = nav_xds.DP1.to_pandas() # Dew point temperature computed from WVSS2
    mixr_ds = nav_xds.MR1.to_pandas() # Water vapour mixing ration from WVSS2
    abshum_ds = nav_xds.HABS1.to_pandas() # Absolute humidity computed from WVSS2
    rh_ds = nav_xds.RH1.to_pandas() # Relative humidity computed from WVSS2
 
    # get unit information from 
    alt_unit = nav_xds.coords['ALTITUDE'].attrs['units']
    lat_unit = nav_xds.coords['LATITUDE'].attrs['units']
    lon_unit = nav_xds.coords['LONGITUDE'].attrs['units']
    tas_unit = nav_xds.TAS1.attrs['units']
    temp_unit = nav_xds.TEMP1.attrs['units']
    pres_unit = nav_xds.PRES.attrs['units']
    dewp_unit = nav_xds.DP1.attrs['units']
    mixr_unit = nav_xds.MR1.attrs['units']
    abshum_unit = nav_xds.HABS1.attrs['units']
    rh_unit = nav_xds.RH1.attrs['units']
    
 
    nav_df = pd.DataFrame({f'Altitude ({alt_unit})':alt_ds,
                           f'Latitude ({lat_unit})':lat_ds,
                           f'Longitude ({lon_unit})':lon_ds,
                           f'TAS ({tas_unit})':tas1_ds,
                           f'Temperature ({temp_unit})':temp_ds,
                           f'Pressure ({pres_unit})':pres_ds,
                           f'Dew point temperature ({dewp_unit})':dewp_ds,
                           f'Mixing ratio ({mixr_unit})':mixr_ds,
                           f'Absolute humidity ({abshum_unit})':abshum_ds,
                           f'Relative humidity ({rh_unit})':rh_ds
                           }) #unit information is in the attributes of the xds
 
    # add a new colum to the dataframe that is the time in UTC seconds/seconds from midnigth
    # FUNCTION: sec_since_midnigth: input: datetime-object, output: seconds since midnight as float
    nav_df['UTC Seconds'] = nav_df.index.to_series().map(sec_since_midnigth) 
    nav_df['flightid']= flight.astype("category") # add flight information to data
    
    # get stat information for the flight
    stats_dict = {} # temp dictionart
    stats_dict['takeoff'] = np.datetime64(nav_xds.attrs['time_take_off'])
    stats_dict['landing'] = np.datetime64(nav_xds.attrs['time_landing'])
    stats_dict['time_in_air'] = np.datetime64(nav_xds.attrs['time_landing'])-np.datetime64(nav_xds.attrs['time_take_off'])
    
    islas_stats_dict[flight] = stats_dict
    
    islas_nav_df.append(nav_df) # append list with the new dataframe

# concatenate all the flight dataframes in the list to a new dataframe containing all flights
islas_nav_df = pd.concat(islas_nav_df)

