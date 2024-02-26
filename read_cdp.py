#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 19 14:30:02 2024

Reading in CDP files and combining with altitude and temperature from the navigation file

Creates: 
    - islas_cdp_df: dataframe of all the data, index: sec since midnigth
    - 

@author: ninalar
"""

# ---Packages---
import xarray as xr # read netcdf-files

# standard data analysis packages:
import numpy as np
import pandas as pd
import datetime as dt
from dateutil import parser

#filemanagement packages
import glob # allows for wildcards in filemanagement
import os #get a list of all directories/files

# functions used fron function.py file
from functions import sec_since_midnigth

# ----- Data ------
# Read in the CDP files and the NAV files(for temperature and coordinates)
# NAV files ar nc files in the format: ISLAS_SAFIRE-ATR42_CORE_TDYN_1HZ_YYYYMMDD_*flightid*_L1_V1.nc
# 
# CDP files are csvfiles in the format: 00CDP YYYYMMDDXXXXX.csv

# Local disk path of data:
main_path = '../2022-islas/' # directory with flight data
pads_path = '/microphy/pads/' # path to pads (CIP and CDP data)
nav_file_struct = '/ISLAS_SAFIRE-ATR42_CORE_TDYN_1HZ_*_L1_V1.nc' # structure of nav file names
cdp_file_struct = '/02CDP*.csv' # structure of cdp file names
drop_flights = ['as220005','as220006'] # flights to drop, (if not all are to be analysed 5 and 6 is in france)

flights = [
    f for f in os.listdir(main_path) if os.path.isdir(os.path.join(main_path, f))
]

# remove flights to drop using listcomprehension
flights = [i for i in flights if i not in drop_flights]

islas_cdp_df = [] #empty list for appending all data to one structure
check_df = [] #empty checklist

for flight in flights:
    # ---- Get NAV data from flight
    
    nav_file = glob.glob(main_path + flight + nav_file_struct) # returns a list, must access with file[0]
    nav_xds = xr.open_dataset(nav_file[0]) # returns an xarray dataset
    
    # --- Prepare NAV information for adding to the cdp_df
    # Necessary NAV data: TAS1 (m/s)(variable) and HEIGHT(meter)(coordinate)
    # Use TAS1: the TAS from the Scientific Static/Pitot system, given in m/s, instead of
    # TAS2: the TAS from the Avionic Static/Pitot system (ADC), given in kt, to have correct units

    # create pandas series of the variables:
    alt_ds = nav_xds.coords['ALTITUDE'].to_pandas()
    tas1_ds = nav_xds.TAS1.to_pandas() # the TAS from the Scientific Static/Pitot system, given in m/s

    # get unit information from 
    alt_unit = nav_xds.coords['ALTITUDE'].attrs['units']
    tas_unit = nav_xds.TAS1.attrs['units']

    nav_df = pd.DataFrame({f'Altitude ({alt_unit})':alt_ds, f'TAS ({tas_unit})':tas1_ds}) #unit information is in the attributes of the xds

    # add a new colum to the dataframe that is the time in UTC seconds/seconds from midnigth
    # FUNCTION: sec_since_midnigth: input: datetime-object, output: seconds since midnight as float
    nav_df['UTC Seconds'] = nav_df.index.to_series().map(sec_since_midnigth) 

    # ---- Get CDP data
    #TODO: consider collecting the instrument metadata as well (line 1-54)
    # at least these could be interresting: sample time, sample aresa, PAS information (3 lines)
    
    # path to CDP data
    path_in = main_path + flight + pads_path
    
    # Get a list of all the CDPfiles in the directory (also look in subdirectories)
    filelist = glob.glob(path_in + '**' + cdp_file_struct, recursive=True)

    #in each directory there is a CDP-csv file
    for file in filelist:
        print('Reading: ' + file) 
        
        # reading in csv data without metadata    
        cdp_df = pd.read_csv(file, skiprows = 58, encoding = "ISO-8859-1")
    
        # Bins are defined in the metadata on rows 23 and 24, separate on both , and > to get correct values, 
        # engine = python to use regext in sep    
        # Create a dataframe of the bin size and threshold information by extracting the informations into lists
        # and building the dataframe from these
        size = list(pd.read_csv(file, 
                             index_col=[0],
                             skiprows = lambda x: x not in [22], 
                             encoding = "ISO-8859-1", 
                             sep=r'[,>]', 
                             engine = 'python'))
        thr = list(pd.read_csv(file, 
                             index_col=[0],
                             skiprows = lambda x: x not in [23], 
                             encoding = "ISO-8859-1", 
                             sep=r'[,>]', 
                             engine = 'python'))
        #define bin numbers
        cdp_bin = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30]  
        # Create dataframe from dictionary of lists and change dtype to int
        bins_df = pd.DataFrame({'CDP Bin': cdp_bin, 'Size': size, 'Threshold': thr}).astype('int64')

        # adding NAV information to the cdp data by merging on nearest UTC Seconds. 
        cdp_nav_df = pd.merge_asof(cdp_df, nav_df, on = 'UTC Seconds', direction = 'nearest')

        # add flightid for managing multiple fligths
        cdp_nav_df["Flight_Id"]=flight
    
        islas_cdp_df.append(cdp_nav_df) # append list with the new dataframe

# concatenate all the flight dataframes in the list to a new dataframe containing all flights
islas_cdp_df = pd.concat(islas_cdp_df)
