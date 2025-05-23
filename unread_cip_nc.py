#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 11 15:10:38 2024

@author: ninalar
"""

# read CIP nc files

# Read cip files, extract variables, extract stats information from flights
def read_cip_nc():
      
    import xarray as xr # read netcdf-files
    import numpy as np
    import warnings
    import pandas as pd
    import glob # allows for wildcards in filemanagement
    import os #get a list of all directories/files
    
    warnings.filterwarnings('ignore', category=DeprecationWarning) # stop the deprecation warnigns from np time management
    
    # functions used fron function.py file
    from notebooks.functions import sec_since_midnigth
    
    # Local disk path of data:
    main_path = '../Results_2022-islas/' # path to processed SODA files
    cip_file_struct = '/*CIP.nc' # structure of cip text-file names
    drop_flights = ['as220005','as220006'] # flights to drop, (if not all are to be analysed 5 and 6 is in france)
    
    # useful coordinates
    # coordinates of Kiruna
    lat_kir = 67.8256
    lon_kir = 20.3351
     
    flights = [
         f for f in os.listdir(main_path) if os.path.isdir(os.path.join(main_path, f))
    ]
     
    # remove flights to drop using listcomprehension
    flights = [i for i in flights if i not in drop_flights]
    
    islas_cip_df = []  # empty list for appending all data to one structure
    #islas_stats_dict = {}  #empty dictionary for collecting flight stats information
    
    for flight in flights:
        # ---- Get NAV data from flight
         
        cip_file = glob.glob(main_path + flight + cip_file_struct) # returns a list, must access with file[0]
        cip_xds = xr.open_dataset(cip_file[0]) # returns an xarray dataset
         
        # --- Turn into pandas dataframe
        # create pandas series of the variables:
        utc_ds = cip_xds.utc_time.to_pandas()
        tas_ds = cip_xds.TAS.to_pandas()
        conc_ds = cip_xds.CONCENTRATION.to_pandas()
        iwc_ds = cip_xds.IWC.to_pandas() # 
        lwc_ds = cip_xds.LWC.to_pandas() # 
        nt_ds = cip_xds.NT.to_pandas() # 
        mvd_ds = cip_xds.MVD.to_pandas() # 
        mnd_ds = cip_xds.MND.to_pandas() # 
        area_ds = cip_xds.AREA.to_pandas() # 
     
        # get unit information from 
        utc_unit = cip_xds.utc_time.attrs['units']
        tas_unit = cip_xds.TAS.attrs['units']
        conc_unit = cip_xds.CONCENTRATION.attrs['units']
        iwc_unit = cip_xds.IWC.attrs['units']
        lwc_unit = cip_xds.LWC.attrs['units']
        nt_unit = cip_xds.NT.attrs['units']
        mvd_unit = cip_xds.MVD.attrs['units']
        mnd_unit = cip_xds.MND.attrs['units']
        area_unit = cip_xds.AREA.attrs['units']
        
     
        cip_df = pd.DataFrame({f'Altitude ({alt_unit})':alt_ds,
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
        cip_df['UTC Seconds'] = cip_df.index.to_series().map(sec_since_midnigth) 
        cip_df['flightid']= flight # add flight information to data
        
        # get stat information for the flight
        stats_dict = {} # temp dictionart
        stats_dict['takeoff'] = np.datetime64(cip_xds.attrs['time_take_off'])
        stats_dict['landing'] = np.datetime64(cip_xds.attrs['time_landing'])
        stats_dict['time_in_air'] = np.datetime64(cip_xds.attrs['time_landing'])-np.datetime64(cip_xds.attrs['time_take_off'])
        stats_dict['lat_max'] = cip_xds.attrs['geospatial_lat_max']
        stats_dict['lat_min'] = cip_xds.attrs['geospatial_lat_min']
        stats_dict['lon_max'] = cip_xds.attrs['geospatial_lon_max']
        stats_dict['lon_min'] = cip_xds.attrs['geospatial_lon_min']
            
        islas_stats_dict[flight] = stats_dict
        
        islas_cip_df.append(cip_df) # append list with the new dataframe
    
    # concatenate all the flight dataframes in the list to a new dataframe containing all flights
    islas_cip_df = pd.concat(islas_cip_df)
    
    return(islas_cip_df, islas_stats_dict)