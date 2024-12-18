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
def read_cdp(nav_df):
    #Reads the CDP files and does corrections based on TAS (needs this from nav_df)
    # ---Packages---
    import xarray as xr # read netcdf-files
    
    # standard data analysis packages: (all packages used in modules must be imported in the module)
    import pandas as pd
    #import datetime as dt
    #from dateutil import parser (not used yet)
    
    #filemanagement packages
    import glob # allows for wildcards in filemanagement
    import os #get a list of all directories/files
    
    # functions used fron function.py file
    from functions import sec_since_midnigth, read_chunky_csv, resolve_date
    
    # ----- Data ------
    # Read in the CDP files and the NAV files(for temperature and coordinates)
    # NAV files ar nc files in the format: ISLAS_SAFIRE-ATR42_CORE_TDYN_1HZ_YYYYMMDD_*flightid*_L1_V1.nc
    # 
    # CDP files are csvfiles in the format: 00CDP YYYYMMDDXXXXX.csv
    
    # Local disk path of data:
    main_path = '../2022-islas/' # directory with flight data
    pads_path = '/microphy/pads/' # path to pads (CIP and CDP data)
    cdp_file_struct = '/02CDP*.csv' # structure of cdp file names
    drop_flights = ['as220005','as220006'] # flights to drop, (if not all are to be analysed 5 and 6 is in france)
    
    flights = [
        f for f in os.listdir(main_path) if os.path.isdir(os.path.join(main_path, f))
    ]
    
    # remove flights to drop using listcomprehension
    flights = [i for i in flights if i not in drop_flights]
    
    islas_cdp_df = []  # empty list for appending all data to one structure
    #check_df = [] #empty checklist keep for metadata later
    
    print('----Reading CDP files:')
    
    for flight in flights:
          
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
            cdp_list = read_chunky_csv(file)
            
            # --- Get data information from 2th chunk. Turn this into a dataframe:
            data = cdp_list[2]
            data.pop(0) # remove separator line
            header = data.pop(0) #get header
            cdp_df = pd.DataFrame(data) # turn into dataframe
            cdp_df = cdp_df.astype(float) # change from string to float
            cdp_df.columns = header #add header information to df
            cdp_df["flightid"]=flight # add flight information
            
            # transform UTC Seconds to datetime, add to time
            date_temp= resolve_date(cdp_df['Year'], cdp_df['Day of Year'])
            sec_temp = cdp_df['UTC Seconds'].apply(lambda x: pd.to_timedelta(x, unit='s')) #turn utc seconds since midnight into datetime object
            cdp_df['time'] = date_temp + sec_temp # add date to the seconds since midnight
            
            
            #---- Get metadata from 0th item in cdp_list
            meta = cdp_list[0]
            # flatten the list
            cdp_meta = [item[0] if len(item) == 1 else ' '.join(item) for item in meta]
            cdp_meta.pop(0) # remove first item of list [Instrument2]
            
            # split list based on conditions (including "Channel" or "<30>" and the rest)
            sub_ch = 'Channels'
            sub_bin = '<30>'
            
            chan_list = [i for i in cdp_meta if sub_ch in i] # list of all items with 'Channel'
            bin_list = [i for i in cdp_meta if sub_bin in i] # list of all items with '<30>'
            
            meta_bin_list = list(set(cdp_meta).difference(chan_list)) # remove chan_list from cdp_list
            meta_list = list(set(meta_bin_list).difference(bin_list)) # remove bin_list from the resulting list
            
            # Turn metadata list into dataframe, clean up and separate variable from value 
            meta_df=pd.DataFrame(meta_list, columns=['Metadata'])
            meta_df['Value'] = meta_df['Metadata'].apply(lambda x: x.split('=')[1].strip())
            meta_df['Metadata'] = meta_df['Metadata'].apply(lambda x: x.split('=')[0].strip())
            # Fix the sample time metadata for later use
            st = meta_df.loc[meta_df['Metadata'] == 'Sample Time', 'Value'].iloc[0].split(" ")
            st_sec = {'Metadata': 'Sample Time (sec)', 'Value': int(st[0])}
            meta_df.loc[len(meta_df)]=st_sec
            
            # Turn bin_list (list of strings) into dataframe of bin information
            # Take entry that includes size or thres, remove the parts of the string that is not values, turn into list
            size_list = [i for i in bin_list if 'Size' in i][0].replace("Sizes=<30>","",1).split(" ")
            thr_list = [i for i in bin_list if 'Thres' in i][0].replace("Thresholds=<30>","",1).split(" ")
            # Make list of lower edges
            # lower edge of the first bin is in the metadata, the rest is the same as size list -last entry
            bin1min = meta_df.loc[meta_df['Metadata']=='Bin 1 Lower Thresh.','Value'].iloc[0] # get the value of the lower bin size treshold
            size_min_list = list(bin1min)+ size_list # add the bin1min to the top of the list
            size_min_list.pop() # remove the last item of the list
            # generate bin number based on lenght of size_list and thr_list
            if len(size_list)==len(thr_list):
                bin_list = list(range(1,len(size_list)+1, 1))
            else:
                print('Warning: size_list and thr_list not of equal lenght')
            
            # turn the three lists into dataframe of integers
            bins_df = pd.DataFrame({'CDP_Bin': bin_list, 'Size (microns)': size_list,'Min size': size_min_list, 'Threshold': thr_list}).astype('int64').set_index('CDP_Bin')
            # calculate the bind width for each bin (for later normalization of values)
            bins_df['Width']=bins_df['Size (microns)'] - bins_df['Min size']
           
            
            # --- get pads information from 1st item in cdp_list
            pads_info_df = pd.DataFrame(cdp_list[1], columns=['Info'])
            # clean up and separate variable from unit 
            pads_info_df['Value'] = pads_info_df['Info'].apply(lambda x: x.split('=')[1].strip())
            pads_info_df['Info'] = pads_info_df['Info'].apply(lambda x: x.split('=')[0].strip())

            # adding NAV information to the cdp data by merging on nearest UTC Seconds. 
            flight_nav_df = nav_df[nav_df['safireid']==flight]
            cdp_nav_df = pd.merge_asof(cdp_df, flight_nav_df[['UTC Seconds','TAS (m/s)']] , on = 'UTC Seconds', direction = 'nearest')
        
            islas_cdp_df.append(cdp_nav_df) # append list with the new dataframe
    
    # concatenate all the flight dataframes in the list to a new dataframe containing all flights
    islas_cdp_df = pd.concat(islas_cdp_df)
    
    # Clean up unnnecessary columns: Spare
    islas_cdp_df = islas_cdp_df.loc[:,~islas_cdp_df.columns.str.startswith('Spare')]
    
    # --- Data corrections
    
    # adjust time variables to have a complete datetime object 'time'
    

    # -- CDP: adjust bulk parameters for TAS
    # calculate TAS correction factor for each timestep
    # (aircraft TAS - 13%)/PAS from probe calculations from Frey(2011)
    islas_cdp_df['TAS probe reduction (m/s)'] = 0.87*islas_cdp_df['TAS (m/s)'] # reduce TAS due to airflow (-13%)
    islas_cdp_df['TAS correction factor'] = (islas_cdp_df['TAS probe reduction (m/s)'])/islas_cdp_df['Applied PAS (m/s)']
    
    # adjust the Numb conc and the LWC parameters with the correction factor
    # (MVD and ED is not dependent on TAS)
    islas_cdp_df['Number Conc corr (#/cm^3)'] = islas_cdp_df['Number Conc (#/cm^3)']/islas_cdp_df['TAS correction factor']
    islas_cdp_df['LWC corr (g/m^3)'] = islas_cdp_df['LWC (g/m^3)']/islas_cdp_df['TAS correction factor']
    
    #calculate the sample volume (sample area SA * TAS redused * sample time (1 sek))
    # sample area from meta information and given in mm^2 readjust to m by dividing with 10⁶
    sa = float(meta_df.loc[meta_df['Metadata'] == 'Sample Area (mm^2)', 'Value'].iloc[0]) /(1000*1000)
    st = meta_df.loc[meta_df['Metadata'] == 'Sample Time (sec)', 'Value'].iloc[0] 
    islas_cdp_df['SV (m^3)'] = sa * islas_cdp_df['TAS probe reduction (m/s)'] * st
    
    # Get variable information from header of dataframe
    var_df = pd.DataFrame(islas_cdp_df.columns[islas_cdp_df.columns.str.endswith(')')], columns=['Variable'])
    var_df['unit'] = var_df['Variable'].apply(lambda x: x.split('(')[1].strip())
    var_df['Variable'] = var_df['Variable'].apply(lambda x: x.split('(')[0].strip())
    var_df = var_df.replace(r'\)','',regex=True) # removing remaining ] in units
    
    return(islas_cdp_df, bins_df, var_df, meta_df)