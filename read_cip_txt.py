#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 13:37:41 2024

@author: ninalar

Reading the resulting .txt file from analysing the raw image fields from the CIP with the Soda2 program
File cosists of calculated bulk parameters for the given flight:
Variables:
   "Time" = Time at start of interval [UTC seconds]
   "Nt" = Total Concentration for Particles with D>112.50um [#/m3]
   "IWC" = Estimated Ice Water Content [g/m3]
   "MMD" = Median Mass-weighted Diameter [microns]
   "Conc001-Conc064" = Concentration per size bin, normalized by bin width [#/m4]

Returns: 
"""
def read_cip_txt():
    # ---Packages---

    # standard data analysis packages:
    import pandas as pd
    from datetime import datetime # to manage dates
    import re #for regex matching
    
    #filemanagement packages
    import glob # allows for wildcards in filemanagement
    import os #get a list of all directories/files
    
    
    # functions used fron function.py file
    from analysis.functions import read_chunky_csv
    # ---Data: CIP--- (ADJUSTED FOR MULTIPLE FILE READING)
    # Particle size distribution file created by SODA2
    # (if the PSD(ASCII)-option is chosen)
    # In my process, these files are stored in a results-folder, separate from the input-data
    
    # Local disk path of data:
    path_res = '../Results_2022-islas/' # path to processed SODA files
    path_flight = '../2022-islas/' # path to flight data
    cip_file_struct = '/*.txt' # structure of cip text-file names
    
    #flight = 'as220007' # Chosen flight
    
    # Get the datafiles for all flights 
    flights = [
        f for f in os.listdir(path_res) if os.path.isdir(os.path.join(path_res, f))
    ]

    # filter list to only items following the structure 'as2200XX'
    flights = [s for s in flights if re.match(r'as2200\d{2}$', s)]
    
    islas_proc_dict = {}  #empty dictionary for collecting processing information
    
    print('----Reading CIP files:')
    for flight in flights:
        
        # ---- Get CIP data
        
        # path to CIP data, the interesting files is in this directory
        filepath = path_res + flight + cip_file_struct
    
        txt = glob.glob(filepath) # all files ending in .txt in path_in as a list
        
        # read the processed CIP information from the files in txt
        for textfile in txt:
            print('Reading: ' + textfile)
            # The datafiles are composed of 5 different "chunks" of information separated by an empty line: 
            # 0: Processing information, 1: Bin information, 2: Notes, 3: Variable information, 5: Data
            # The number of lines in each chunck varies and depends on the preprocessing, number if image files etc.
            # Separate the chunks by splitting on empty lines [] by using the read_chunky_csv FUNCTION:
            cip_list = read_chunky_csv(textfile)
            
            # --- Processing information
            # Processing information is in the 0th chunk. Turn this into a dictionary:
            proc = cip_list[0]
            #The first entry is just a heading and not needed:
            proc.pop(0)
            data_dict={}
            for element in proc:
                # Split the element into key and value using ':'
                key_value = element[0].split(':')
        
                # Remove leading and trailing whitespaces from key and value
                key = key_value[0].strip()
                value = key_value[1].strip()
        
                # Assign key-value pair to the dictionary
                data_dict[key] = value
            
            # add processing information for flight to dict
            islas_proc_dict[flight] = data_dict
            
            
            # --- Bin information
            # bin information is in the 1st chunk
            bins = cip_list[1]
            # Get column headers
            mid_h = bins[0][0]
            end_h = bins[2][0]
            # Get bin end and mid values, split to get proper lists for generating df
            mid_v = bins[1][0].split()
            end_v = bins[3][0].split()
            #since endpoint includes first startpoint, this needs to be popped to get the correct lenght:
            start_v = end_v[:-1]
            end_v.pop(0)
            bins_df = pd.DataFrame({"Bin startpoints (microns)": pd.to_numeric(start_v), mid_h: pd.to_numeric(mid_v), end_h: pd.to_numeric(end_v)}) #dataframe with bin information
                    
            # --- Extra information
            notes=cip_list[2] 
            # chunk 2 includes various notes and information. Separate out specific useful info
            # and add to processing dict
            str1 = notes[1][0].strip()
            # extract minimum size for calculating bulk properties
            l = []
            for t in str1.split():
                try:
                    l.append(float(t))
                except ValueError:
                    pass
            # extract criteria for processing size distribution
            str2 = notes[2][0].strip()
            crit = str2.split("using",1)[1].strip(" .")
            notes_dict = {'Notes':{'min size': l, 'Notes 1':str1,'size dist processing': crit,'Notes 2': str2}}
            
            # extract mass-size parametrization coefficients
            text,a = notes[3][0].strip().split(":")
            key_a, value_a = a.split("=")
            key_b, value_b = notes[3][1].strip().split("=")
            coeff_dict = {text:{key_a.strip(): float(value_a.strip()), key_b: float(value_b.strip())}}
            
            #add to processing dict:
            islas_proc_dict[flight].update(notes_dict)
            islas_proc_dict[flight].update(coeff_dict)
            
            # --- Variable information
            # variable information is in the 3th chunk. Turn this into a dataframe:
            var = cip_list[3]
            # flatten the list
            var = [item[0] if len(item) == 1 else ' '.join(item) for item in var]
            var_df = pd.DataFrame(var[1:len(var)], columns=['Variable']) # create dataframe excluding the first entry (which is used as header)
            # clean up and separate variable from unit 
            var_df['unit'] = var_df['Variable'].apply(lambda x: x.split('[')[1].strip())
            var_df['Variable'] = var_df['Variable'].apply(lambda x: x.split('[')[0].strip())
            var_df = var_df.replace(']','',regex=True) # removing remaining ] in units
            
            
            # --- Data 
            # data information is in the 4th chunk. Turn this into a dataframe:
            data = cip_list[4] 
            header = data.pop(0) #get header
            data.pop(0) # remove separator line
    
            # adjust header, get bin information from header and add to bin_df
            header = header[0].split()
            bincount = len(bins_df) # get number of bins from bin-information 
            bins_df['Bin_name']= header[-bincount:]
    
            # Readjust to dataframe of numbers
            data = [item for sublist in data for item in sublist] # flatten data (list of lists to list)
            split_strings = [string.split() for string in data] # split strings to lists of strings
            data_df = pd.DataFrame(split_strings) # turn into dataframe
            data_df = data_df.map(lambda x: x.strip() if isinstance(x, str) else x) # remove extra whitespaces
            data_df = data_df.astype(float) # change froms tring to float
            data_df.columns = header #add header information to df
            data_df["safireid"]=flight
            data_df.rename(columns={"Time": "UTC Seconds"},inplace = True) #rename 'Time' column to UTC Seconds to match other dataframes 
            # create new column with full datetime object
            date = pd.to_datetime(islas_proc_dict[flight]['Flight date (mm/dd/yy)'])
            #date = datetime.strptime(date, '%m/%d/%Y') # get flight date from processing dictionary
            
            # transform time to datetime, adding date from attributes
            sec_temp = data_df['UTC Seconds'].apply(lambda x: pd.to_timedelta(x, unit='s')) #turn utc seconds since midnight into datetime object
            data_df['time'] = date + sec_temp # add date to the seconds since midnight
            
            # concatenate information from this flight to total df
            if flights.index(flight) == 0:
                # for first run of loop set up main dataframe
                islas_cip_bulk_df = data_df
                islas_bins_df = bins_df
                islas_var_df = var_df
            else:
                # for later runs of loop add to main dataframe
                islas_cip_bulk_df = pd.concat([islas_cip_bulk_df, data_df], axis=0, ignore_index=True)
                if islas_bins_df.compare(bins_df).empty == False:
                    print('error: mismatched bins')
                elif islas_var_df.compare(var_df).empty == False: 
                    print('error: mismatched variables')
                
    return(islas_cip_bulk_df, islas_bins_df, islas_var_df, islas_proc_dict)
