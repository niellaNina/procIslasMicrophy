#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 30 13:52:45 2024

@author: ninalar

Reading the resulting .pbp.nc (particle-by-particle)file from analysing the raw image fields from the CIP with the Soda2 program
File cosists of calculated bulk parameters for the given flight:
Variables:
   
    Time related variables (All time related variables are dtype = timedelta64[ns])
        time: dimension time
        probetime, buffertime, rawtime, reftime
        inttime: interarrival time from previous particle

    Size related variables
        diam: Particle diameter from circle fit. No Poisson spot size corrections applied
        xsize: X-size (across array). No Poisson spot size corrections applied
        ysize: Y-size (along airflow). No Poisson spot size corrections applied
        xextent: Maximum x-size (across array) for a single slice. No Poisson spot size corrections applied
        oned: 1-D emulation size. Number of latched pixels. No Poisson spot size corrections applied
        twod: 2-D emulation size. Maximum number of shaded pixels on a single slice. No Poisson spot size corrections applied
        areasize: Equivalent area size. No Poisson spot size corrections applied
        arearatio: Area ratio
        arearatiofilled: Area ratio with particle voids filled
        aspectratio: Aspect ratio
        area: Number of shaded pixels
        areafilled: Number of shaded pixels including voids
        perimeterarea: Number of shaded pixels on particle perimeter
        area75: Number of shaded pixels at the 75% (or grey level-3) shading
        xpos: X-position of particle center (across array)
        ypos: Y-position of particle center (along airflow)

    flags and corrections
        allin: All-in flag (1=all-in)
        centerin: Center-in flag (1=center-in)
        dofflag: Depth of field flag from probe (1=accepted)
        edgetouch: Edge touch (1=left 2=right 3=both)
        sizecorrection: Size correction factor from Korolev 2007 (D_edge/D0). Use to adjust sizes in this file if necessary
        zd: Z position from Korolev correction
        missed: Missed particle count
        overloadflag: Overload flag
        rejectionflag: Particle rejection code (see soda2_reject.pro)

    Additional variables
        probetas: True air speed for probe clock
        aircrafttas: True air speed for aircraft (if available)
        particlecounter: Particle counter
        orientation: Particle orientation relative to array axis

    Per June 2024, the folllowing is extracted: 
        utc_time,TAS,CONCENTRATION,LWC,IWC,NT,MVD,MND,AREA

Returns: 
"""

# read Particle by particle nc files from the CIP

# Read cip files, extract variables, extract stats information from flights
#def read_cip_pbp_nc():
      
import xarray as xr # read netcdf-files
import numpy as np
import warnings
import pandas as pd
import glob # allows for wildcards in filemanagement
import os #get a list of all directories/files


warnings.filterwarnings('ignore', category=DeprecationWarning) # stop the deprecation warnigns from np time management

# Local disk path of data:
main_path = '../Results_2022-islas/' # path to processed SODA files
cip_file_struct = '/*CIP.pbp.nc' # structure of cip text-file names
drop_flights = ['as220005','as220006'] # flights to drop, (if not all are to be analysed 5 and 6 is in france)


flights = [
 f for f in os.listdir(main_path) if os.path.isdir(os.path.join(main_path, f))
]
 
# remove flights to drop using listcomprehension
flights = [i for i in flights if i not in drop_flights]

cip_pbp_df = []  # empty list for appending all data to one structure

print('----Reading CIP.pbp.nc files')


for flight in flights:
# ---- Get CDP data from flight
    cip_file = glob.glob(main_path + flight + cip_file_struct) # returns a list, must access with file[0]
    if flight == 'as220007':
        cip_xds = xr.open_dataset(cip_file[0]) # returns an xarray dataset
    print(f'Reading: {cip_file[0]}')
    '''
    # -- extract data from CIP-file
    area_ratio_ds = cip_xds.arearatio.to_pandas()
    perimeterarea_ds = cip_xds.perimeterarea.to_pandas()
    area_ds = cip_xds.area.to_pandas()
    areafilled_ds = cip_xds.areafilled.to_pandas()
    iwc_ds = cip_xds.IWC.to_pandas()
    nt_ds = cip_xds.NT.to_pandas() # 
    mvd_ds = cip_xds.MVD.to_pandas() # 
    mnd_ds = cip_xds.MND.to_pandas() # 
    area_ds = cip_xds.AREA.to_pandas() # 
    date = pd.to_datetime(cip_xds.attrs['FlightDate'], format='%m/%d/%Y') #date of flight from attributes
    
    # get unit information from 
    lwc_unit = cip_xds.LWC.attrs['units']
    iwc_unit = cip_xds.IWC.attrs['units']
    utc_unit = cip_xds.utc_time.attrs['units']
    tas_unit = cip_xds.TAS.attrs['units']
    conc_unit = cip_xds.CONCENTRATION.attrs['units'] 
    nt_unit = cip_xds.NT.attrs['units']
    mvd_unit = cip_xds.MVD.attrs['units']
    mnd_unit = cip_xds.MND.attrs['units']
    area_unit = cip_xds.AREA.attrs['units']
    
    # get longname information from 
    lwc_ln = cip_xds.LWC.attrs['long_name']
    iwc_ln = cip_xds.IWC.attrs['long_name']
    utc_ln = cip_xds.utc_time.attrs['long_name']
    tas_ln = cip_xds.TAS.attrs['long_name']
    conc_ln = cip_xds.CONCENTRATION.attrs['long_name'] 
    nt_ln = cip_xds.NT.attrs['long_name']
    mvd_ln = cip_xds.MVD.attrs['long_name']
    mnd_ln = cip_xds.MND.attrs['long_name']
    area_ln = cip_xds.AREA.attrs['long_name']
    
    
    
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
    
    #cip_df.set_index(f'time ({utc_unit})', inplace=True) # Set 'time' as the index
    cip_df['TWC (gram/m3)'] = cip_df['LWC (gram/m3)']+cip_df['IWC (gram/m3)'] # calculate total water content (LWC + IWC)
    cip_df['LWC %'] = (cip_df['LWC (gram/m3)']/cip_df['TWC (gram/m3)'])*100 # calculate percentage of LWC 
    cip_df['flightid']= flight # add flight information to data
    
    # Build a pandas dataframe for the concentration binned
    conc_df = conc_ds.T #transpose the concentration data to have time as row values
    conc_df['UTC seconds'] = utc_ds #add time information (time in original df is just counting seconds from the beginning of measurements)
    conc_df['flightid']= flight # add fligth information for later handling
    
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
'''
# Bin information (to be added later?)
#bin_end = cip_xds.CONCENTRATION.attrs['Bin_endpoints'] 
   
 
# Create the pandas DataFrame
#cip_var_df = pd.DataFrame(var_data, columns=['Variable', 'long_name','unit'])

#return(cip_bulk_df, cip_conc_df, cip_var_df)