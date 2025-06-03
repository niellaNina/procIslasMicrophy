#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  4 10:02:23 2024

Reading in the LWC files

@author: ninalar
"""
def read_lwc(nav_df):
    # ---Packages---
    
    # standard data analysis packages: (all packages used in modules must be imported in the module)
    import pandas as pd
    #import datetime as dt
    #from dateutil import parser (not used yet)
    
    #filemanagement packages
    import glob # allows for wildcards in filemanagement
    import os #get a list of all directories/files
    
    # functions used fron function.py file
    from analysis.functions import read_chunky_csv
    
    # ----- Data ------
    # Read in the CDP files and the NAV files(for temperature and coordinates)
    # NAV files ar nc files in the format: ISLAS_SAFIRE-ATR42_CORE_TDYN_1HZ_YYYYMMDD_*flightid*_L1_V1.nc
    # 
    # CDP files are csvfiles in the format: 00CDP YYYYMMDDXXXXX.csv
    
    # Local disk path of data:
    main_path = '../2022-islas/' # directory with flight data
    pads_path = '/microphy/pads/' # path to pads (CIP and CDP data)
    lwc_file_struct = '/01LWC*.csv' # structure of cdp file names
    drop_flights = ['as220005','as220006'] # flights to drop, (if not all are to be analysed 5 and 6 is in france)
    
    flights = [
        f for f in os.listdir(main_path) if os.path.isdir(os.path.join(main_path, f))
    ]
    
    # remove flights to drop using listcomprehension
    flights = [i for i in flights if i not in drop_flights]
    
    islas_lwc_df = [] #empty list for appending all data to one structure
    #check_df = [] #empty checklist keep for metadata later
    
    print('----Reading LWC files:')
    
    for flight in flights:
       
        # ---- Get LWC data
                
        # path to LWC data
        path_in = main_path + flight + pads_path
        
        # Get a list of all the CDPfiles in the directory (also look in subdirectories)
        filelist = glob.glob(path_in + '**' + lwc_file_struct, recursive=True)
    
        #in each directory there is a CDP-csv file
        for file in filelist:
            print('Reading: ' + file) 
            
            # reading in csv data without metadata    
            lwc_list = read_chunky_csv(file)
            
            # --- Get data information from 2th chunk. Turn this into a dataframe:
            data = lwc_list[2]
            data.pop(0) # remove separator line
            header = data.pop(0) #get header
            lwc_df = pd.DataFrame(data) # turn into dataframe
            lwc_df = lwc_df.astype(float) # change from string to float
            lwc_df.columns = header #add header information to df
            lwc_df["Flightid"]=flight # add flight information
            
            #---- Get metadata from 0th chunk in lwc_list
            meta = lwc_list[0]
            # flatten the list
            lwc_meta = [item[0] if len(item) == 1 else ' '.join(item) for item in meta]
            lwc_meta.pop(0) # remove first item of list [Instrument2]
            
            # split list based on conditions (including "Channel" or "<30>" and the rest)
            sub_ch = 'Channels'
            
            chan_list = [i for i in lwc_meta if sub_ch in i] # list of all items with 'Channel'
            
            meta_list = list(set(lwc_meta).difference(chan_list)) # remove chan_list from cdp_list
            
            # Turn metadata list into dataframe, clean up and separate variable from value 
            meta_df=pd.DataFrame(meta_list, columns=['Metadata'])
            meta_df['Value'] = meta_df['Metadata'].apply(lambda x: x.split('=')[1].strip())
            meta_df['Metadata'] = meta_df['Metadata'].apply(lambda x: x.split('=')[0].strip())
            
            
            # Turn channel information into a dictionary
            # Extract channel number and create dataframe
            chan_list.pop(0) # remove first entry of channel lisst
            chan_df = pd.DataFrame([i.split(' ')[1].strip('.Chan.') for i in chan_list], columns=['Channel'])
            
            # Get the part of the the string not used yet
            temp = [i.split(' ')[2] for i in chan_list]
            # Extract the name of the channel parameter (between .. and = in the string)
            chan_df['Param'] = pd.DataFrame([i.split('..')[1].split('=')[0] for i in temp])
            # get the value of the parameter (after =)
            chan_df['Value'] = pd.DataFrame([i.split('=')[1].strip('<5>') for i in chan_list])

            #Turn into dictionary
            chan_dict = {k: f.groupby('Param')['Value'].apply(list).to_dict() for k, f in chan_df.groupby('Channel')}
            
            # --- get pads information from 1st item in cdp_list
            pads_info_df = pd.DataFrame(lwc_list[1], columns=['Info'])
            # clean up and separate variable from unit 
            pads_info_df['Value'] = pads_info_df['Info'].apply(lambda x: x.split('=')[1].strip())
            pads_info_df['Info'] = pads_info_df['Info'].apply(lambda x: x.split('=')[0].strip())
            
            # adding NAV information to the cdp data by merging on nearest UTC Seconds. 
            flight_nav_df = nav_df[nav_df['flightid']==flight]
            lwc_nav_df = pd.merge_asof(lwc_df, flight_nav_df[['UTC Seconds','TAS (m/s)']] , on = 'UTC Seconds', direction = 'nearest')
            
            # Adjust the LWC to the actual TAS
            lwc_nav_df['TAScorr'] = lwc_nav_df['PAS(m/s)']/lwc_nav_df['TAS (m/s)']
            lwc_nav_df['LWC-calcDAPcorr'] = lwc_nav_df['LWC-CalculatedDAP']*lwc_nav_df['TAScorr']
        

            islas_lwc_df.append(lwc_nav_df) # append list with the new dataframe
    
    # concatenate all the flight dataframes in the list to a new dataframe containing all flights
    islas_lwc_df = pd.concat(islas_lwc_df)
    
    # Clean up unnnecessary columns: Spare
    islas_lwc_df = islas_lwc_df.loc[:,~islas_lwc_df.columns.str.startswith('Spare')]
    
    # Get variable information from header of dataframe
    #var_df = pd.DataFrame(islas_lwc_df.columns[islas_lwc_df.columns.str.endswith(')')], columns=['Variable'])
    #var_df['unit'] = var_df['Variable'].apply(lambda x: x.split('(')[1].strip())
    #var_df['Variable'] = var_df['Variable'].apply(lambda x: x.split('(')[0].strip())
    #var_df = var_df.replace(r'\)','',regex=True) # removing remaining ] in units
    
    return(islas_lwc_df, meta_df, chan_dict)
