#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 28 11:09:21 2024

@author: ninalar

"""

# Read Nav files, extract variables, extract stats information from flights
# Also updates nomenclature on flights (adds ISLAS flightid in addtion to safireid)
# WARNING: this code has some hardcodet paths to fix the 8th flight (two islas flightids in one safireid 
def read_nav():
          
    import xarray as xr # read netcdf-files
    import numpy as np
    import warnings
    import pandas as pd
    import glob # allows for wildcards in filemanagement
    import os #get a list of all directories/files
    from datetime import datetime
    import read_flight_report
    
    warnings.filterwarnings('ignore', category=DeprecationWarning) # stop the deprecation warnigns from np time management
    
    # functions used fron function.py file
    from functions import sec_since_midnigth
        
    # Local disk path of data:
    main_path = '../2022-islas/' # directory with flight data
    nav_file_struct_tdyn = '/ISLAS_SAFIRE-ATR42_CORE_TDYN_1HZ_*_L1_V1.nc' # structure of nav TDYN file names
    nav_file_struct_nav = '/ISLAS_SAFIRE-ATR42_CORE_NAV_1HZ_*_L1_V1.nc' # structure of nav NAV file names
    drop_flights = ['as220005','as220006'] # flights to drop, (if not all are to be analysed 5 and 6 is in france)
    
     
    flights = [
         f for f in os.listdir(main_path) if os.path.isdir(os.path.join(main_path, f))
    ]
     
    # remove flights to drop using listcomprehension
    flights = [i for i in flights if i not in drop_flights]
    
    islas_nav_df = []  # empty list for appending all data to one structure
    islas_stats_dict = {}  #empty dictionary for collecting flight stats information
    
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
        nav_df['safireid']= flight # add flight information to data 
        
        # get stat information for the flight
        stats_dict = {} # temp dictionart
        stats_dict['safireid'] = flight
        stats_dict['takeoff'] = datetime.strptime(nav_xds.attrs['time_take_off'], '%Y-%m-%dT%H:%M:%SZ')
        stats_dict['landing'] = datetime.strptime(nav_xds.attrs['time_landing'], '%Y-%m-%dT%H:%M:%SZ')
    
        islas_stats_dict[flight] = stats_dict
        
        
        islas_nav_df.append(nav_df) # append list with the new dataframe
    
    # concatenate all the flight dataframes in the list to a new dataframe containing all flights
    islas_nav_df = pd.concat(islas_nav_df)
    
    # ---- Testing for determining flightpath from altitude
    
    # Mark wheter altitude change is decending or acending (or no altitude change)
    # first create a rolling mean of the altitude
    
    islas_nav_df['Alt_roll_mean'] = islas_nav_df['Altitude (meter)'].rolling(5).mean # five sec rolling mean
    #cloud_nav_df[]
    
    # ---- adding ISLAS id and separating flight 8
    # Separate flight 8 based on extra landing information from the flight report:
    file = main_path + 'as220008/CRvol/top_cel_MAIN_24-03-2022_07-33-12_CRvol.csv'
    f8_report_df = read_flight_report.read_flight_report(file) # read in the flight report from file
    
    # find the landing times
    landings = f8_report_df[f8_report_df['title']=='landing']
    takeoffs = f8_report_df[f8_report_df['title']=='takeoff']
    
    # double check that there is 2 landings and get the time of the earliest one
    if len(landings) == 2:
        extra_landing_time = datetime.strptime(landings.iloc[0,1], '%Y-%m-%dT%H:%M:%S.%fZ') # as datetime-object
        extra_takeoff_time = datetime.strptime(takeoffs.iloc[1,1], '%Y-%m-%dT%H:%M:%S.%fZ') # as datetime-object
    elif len(landings)>2:
         print('More than 2 landings, check data')
    else:
        print('1 or less landings, no need to separate')
        
    # Change stats dictionary to dataframe to manipulate
    # also transpose and reset index
    stats_df = pd.DataFrame.from_dict(islas_stats_dict).T.reset_index(drop=True)
    
    # duplicate the row with flight 8
    new = stats_df[stats_df['safireid']=='as220008'].copy() # create a copy
    stats_df = pd.concat([stats_df,new], ignore_index = True) # add to df
    stats_df = stats_df.sort_values('safireid').reset_index(drop=True) #sort according to id
    
    # change landingtime for the first flight8 values and takeoff time for the second
    # NB!!! HARDCODED: CHANGE IF USING DIFFERENT DATA OR ADDING FLIGHT 6
    stats_df.iloc[1,2]=extra_landing_time
    stats_df.iloc[2,1]=extra_takeoff_time
    
    # ----------- Flightid nomenclature change
    # From safireid (as2200XX) to islasid/flightid (IS22-XX)
    # Flight 8/as220006 has 2 flights in 1 safireid (to LYS and back again) and needs to be separated. 
    
    # Separate flight 8 based on extra landing information from the flight report:
    # NB! HARDCODED FILEPATH
    file = main_path + 'as220008/CRvol/top_cel_MAIN_24-03-2022_07-33-12_CRvol.csv'
    f8_report_df = read_flight_report.read_flight_report(file) # read in the flight report from file
    
    # find the landing times
    landings = f8_report_df[f8_report_df['title']=='landing']
    takeoffs = f8_report_df[f8_report_df['title']=='takeoff']
    
    # double check that there is 2 landings and get the time of the earliest one
    if len(landings) == 2:
        extra_landing_time = datetime.strptime(landings.iloc[0,1], '%Y-%m-%dT%H:%M:%S.%fZ') # as datetime-object
        extra_takeoff_time = datetime.strptime(takeoffs.iloc[1,1], '%Y-%m-%dT%H:%M:%S.%fZ') # as datetime-object
    elif len(landings)>2:
        print('More than 2 landings, check data')
    else:
        print('1 or less landings, no need to separate')
    
    # Update stats_df with new flightid
    # create new column with values based on conditions
    # NB! HARDCODED! could be moved to function
    conditions = [
        (stats_df['safireid']=='as220006'),
        (stats_df['safireid']=='as220007'),
        (stats_df['safireid']=='as220008') & (stats_df['landing'] == extra_landing_time),
        (stats_df['safireid']=='as220008') & (stats_df['takeoff'] == extra_takeoff_time),
        (stats_df['safireid']=='as220009'),
        (stats_df['safireid']=='as220010'),
        (stats_df['safireid']=='as220011'),
        (stats_df['safireid']=='as220012'),
        (stats_df['safireid']=='as220013'),
        (stats_df['safireid']=='as220014'),
        (stats_df['safireid']=='as220015')
        ]
    values = ['IS22-01','IS22-02','IS22-03','IS22-04','IS22-05','IS22-06','IS22-07','IS22-08','IS22-09','IS22-10','IS22-11']
    
    stats_df['flightid'] = np.select(conditions, values)
    stats_df['time_in_air'] = stats_df['landing']-stats_df['takeoff'] # add column with time in air for the flights
    
    
    # Update islas_nav_df with new flightid
    # create new column with values based on conditions, same values can be reused, but conditions are slightly different
    # NB! HARDCODED! could be moved to function
    conditions = [
        (islas_nav_df['safireid']=='as220006'),
        (islas_nav_df['safireid']=='as220007'),
        (islas_nav_df['safireid']=='as220008') & (islas_nav_df.index <= extra_landing_time),
        (islas_nav_df['safireid']=='as220008') & (islas_nav_df.index > extra_landing_time),
        (islas_nav_df['safireid']=='as220009'),
        (islas_nav_df['safireid']=='as220010'),
        (islas_nav_df['safireid']=='as220011'),
        (islas_nav_df['safireid']=='as220012'),
        (islas_nav_df['safireid']=='as220013'),
        (islas_nav_df['safireid']=='as220014'),
        (islas_nav_df['safireid']=='as220015')
        ]
    
    islas_nav_df['flightid'] = np.select(conditions, values)
    islas_nav_df['flightid'] = islas_nav_df['flightid'].astype("category") # make sure that flight is of type "category")
    
       
    return(islas_nav_df, stats_df)
    
