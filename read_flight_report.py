#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 11:07:34 2024

@author: ninalar
"""

def read_flight_report():
    # read all flight reports and return them as a joined dataframe of all entries from all flights
    # Input: None
    # Output: 
        # all_reports_df: df of all the entries from all the report from all flights
        # file_info_dict: dict of fileinformation from all files from all fligths
    
    # Packages 
    import pandas as pd
    import glob # allows for wildcards in filemanagement
    import os #get a list of all directories/files
    import re #regex

    # Local functions
    from functions import read_chunky_csv
    
    # --- Get flights and flightreports 
    main_path = '../2022-islas/' # path to 
    file_struct = '/*CRvol.csv' # structure of cip text-file names
    drop_flights = ['as220005','as220006'] # flights to drop, (if not all are to be analysed 5 and 6 is in france)

    # regex for only using folders that are flights
    patt = re.compile(r"as2200\d{2}") # flights have the pattern as2200 + 2 digits
 
    flights = [
     f for f in os.listdir(main_path) 
     if os.path.isdir(os.path.join(main_path, f)) and patt.fullmatch(f)
    ]
     
    # remove flights to drop using listcomprehension
    flights = [i for i in flights if i not in drop_flights]
    
    # --- Process flightreports
    # initializing lists and dicts for storing
    all_reports_df = [] 
    file_info_dict = {}
    
    for flight in flights:
        rep_files = glob.glob(main_path + flight + '/CRvol' +  file_struct)
     
        for file in rep_files:
            filename = file.split("CRvol/",1)[1] # get only filename for dataframe
    
            # reading in flight report as chunky csv    
            fr_list = read_chunky_csv(file)
        
            # dict of general flight information
            file_info_dict[filename] = {fr_list[0][0][i]: fr_list[0][1][i] for i in range(len(fr_list[0][0]))}
            
            # store flightreport entries as dataframe
            headers = pd.DataFrame(fr_list[1]).iloc[0]
            report_df  = pd.DataFrame(pd.DataFrame(fr_list[1]).values[1:], columns=headers)
    
            # Add flight and file information to dataframe
            report_df['flight'] = flight
            report_df['file'] = filename
            all_reports_df.append(report_df)
    
    all_reports_df = pd.concat(all_reports_df) 
    
    return(all_reports_df, file_info_dict)


def find_report_entries(df, str_new):
    # Search a dataframe for specific string 
    # Input: 
        # df: dataframe to search in
        # str_new: string to search for
    # Output:
        # filtered_df: dataframw with only the rows where the string was found
    
    # Define a search function
    def search_string(s, search):
        return search in str(s).lower()
    
    # Search for the string 'al' in all columns
    mask = df.apply(lambda x: x.map(lambda s: search_string(s, str_new)))
    
    # Filter the DataFrame based on the mask
    filtered_df = df.loc[mask.any(axis=1)]
    return(filtered_df)


