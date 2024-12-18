#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 11 15:10:38 2024

@author: ninalar

Reading the resulting .nc file from analysing the raw image fields from the CIP with the Soda2 program
File cosists of calculated bulk parameters for the given flight:
Variables:


Returns: 
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
    import re #regex
    
    
    warnings.filterwarnings('ignore', category=DeprecationWarning) # stop the deprecation warnigns from np time management
    
    # Local disk path of data:
    main_path = '../Results_2022-islas/' # path to processed SODA files
    cip_file_struct = '/*CIP.nc' # structure of cip text-file names
    drop_flights = ['as220005','as220006'] # flights to drop, (if not all are to be analysed 5 and 6 is in france)
    
    # regex for only using folders that ar flights
    patt = re.compile(r"as2200\d{2}") # flights have the pattern as2200 + 2 digits
     
    flights = [
     f for f in os.listdir(main_path) 
     if os.path.isdir(os.path.join(main_path, f)) and patt.fullmatch(f)
    ]
     
    # remove flights to drop using listcomprehension
    flights = [i for i in flights if i not in drop_flights]
    
    cip_bulk_df = []  # empty list for appending all data to one structure
    cip_conc_df = [] #empty list for appending binned concentrations
    print('----Reading CIP.nc files')
    for flight in flights:
    # ---- Get CDP data from flight
     
        cip_file = glob.glob(main_path + flight + cip_file_struct) # returns a list, must access with file[0]
        cip_xds = xr.open_dataset(cip_file[0]) # returns an xarray dataset
        print(f'Reading: {cip_file[0]}')
        
        # -- extract data from CIP-file
        utc_ds = cip_xds.utc_time.to_pandas()
        tas_ds = cip_xds.TAS.to_pandas()
        conc_ds = cip_xds.CONCENTRATION.to_pandas()
        lwc_ds = cip_xds.LWC100.to_pandas()
        iwc_ds = cip_xds.IWC100.to_pandas()
        nt_ds = cip_xds.NT100.to_pandas() # 
        mvd_ds = cip_xds.MVD100.to_pandas() # 
        mnd_ds = cip_xds.MND100.to_pandas() # 
        area_ds = cip_xds.AREA100.to_pandas() # 
        date = pd.to_datetime(cip_xds.attrs['FlightDate'], format='%m/%d/%Y') #date of flight from attributes
        
        # get unit information from 
        lwc_unit = cip_xds.LWC100.attrs['units']
        iwc_unit = cip_xds.IWC100.attrs['units']
        utc_unit = cip_xds.utc_time.attrs['units']
        tas_unit = cip_xds.TAS.attrs['units']
        conc_unit = cip_xds.CONCENTRATION.attrs['units'] 
        nt_unit = cip_xds.NT100.attrs['units']
        mvd_unit = cip_xds.MVD100.attrs['units']
        mnd_unit = cip_xds.MND100.attrs['units']
        area_unit = cip_xds.AREA100.attrs['units']
        
        # get longname information from 
        lwc_ln = cip_xds.LWC100.attrs['long_name']
        iwc_ln = cip_xds.IWC100.attrs['long_name']
        utc_ln = cip_xds.utc_time.attrs['long_name']
        tas_ln = cip_xds.TAS.attrs['long_name']
        conc_ln = cip_xds.CONCENTRATION.attrs['long_name'] 
        nt_ln = cip_xds.NT100.attrs['long_name']
        mvd_ln = cip_xds.MVD100.attrs['long_name']
        mnd_ln = cip_xds.MND100.attrs['long_name']
        area_ln = cip_xds.AREA100.attrs['long_name']
        
        ''' (take out this)
        # check if conc_unit is correct: cm-3
        if nt_unit == '#/m3':
            nt_ds = nt_ds*10**(-6) #recalculate to per cm^3
            nt_unit = '#/cm3'
        '''
        
        # transform time to datetime, adding date from attributes
        sec_temp = pd.to_timedelta(utc_ds, unit='s') #turn utc seconds since midnight into datetime object
        new_time = date + sec_temp # add date to the seconds since midnight
        
        # Build the pandas  dataframe of the CIP data in the NetCDF file 
        # Build column names that include the unit.
        # Exception: uts_ds: time in seconds since midnigth. Use UTC Seconds to make the naming coherent over
        # all the different datatypes.
        cip_df = pd.DataFrame({'time': new_time,
                               'UTC Seconds': utc_ds,  
                               f'TAS ({tas_unit})':tas_ds,
                               f'MVD ({mvd_unit})':mvd_ds,
                               f'LWC ({lwc_unit})':lwc_ds,
                               f'NT ({nt_unit})':nt_ds,
                               f'MND ({mnd_unit})':mnd_ds,
                               f'Area Ratio ({area_unit})':area_ds,
                               f'IWC ({iwc_unit})':iwc_ds
                               }) #unit information is in the attributes of the xds
        
        # add safireid
        cip_df['safireid']= flight # add flight information to data
        
        # Build a pandas dataframe for the concentration binned
        conc_df = conc_ds.T #transpose the concentration data to have time as row values
        conc_df['UTC seconds'] = utc_ds #add time information (time in original df is just counting seconds from the beginning of measurements)
        conc_df['safireid']= flight # add fligth information for later handling
        
        # append lists with the new dataframes:
        cip_bulk_df.append(cip_df) 
        cip_conc_df.append(conc_df)
    
    # concatenate all the flight dataframes in the list to a new dataframe containing all flights
    cip_bulk_df = pd.concat(cip_bulk_df)
    cip_conc_df = pd.concat(cip_conc_df)
    
    # Build dataframe of variable information
    # initialize list of lists
    var_data = [['UTC seconds', utc_ln, utc_unit],
                [f'TAS ({tas_unit})', tas_ln, tas_unit],
                [f'MVD ({mvd_unit})',mvd_ln, mvd_unit],
                [f'LWC ({lwc_unit})',lwc_ln, lwc_unit],
                [f'NT ({nt_unit})', nt_ln, nt_unit],
                [f'MND ({mnd_unit})', mnd_ln, mnd_unit],
                [f'Area Ratio ({area_unit})', area_ln, area_unit],
                [f'IWC ({iwc_unit})',iwc_ln, iwc_unit],
                ['Bin # conc', conc_ln, conc_unit],
                ['Bin', 'Sizing bin',cip_xds.CONCENTRATION.attrs['Bin_units'] ]]
    
    # Bin information (to be added later?)
    bin_end = cip_xds.CONCENTRATION.attrs['Bin_endpoints'] 
   
 
    # Create the pandas DataFrame
    cip_var_df = pd.DataFrame(var_data, columns=['Variable', 'long_name','unit'])
    return(cip_bulk_df, cip_conc_df, cip_var_df)