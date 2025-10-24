#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 19 12:46:01 2024

@author: ninalar
"""

#### ---Functions---

# from yariv stack overflow
def datetime64_to_time_of_day(datetime64_array):
    """
    Return a new array. For every element in datetime64_array return the time of day (since midnight).
    >>> datetime64_to_time_of_day(np.array(['2012-01-02T01:01:01.001Z'],dtype='datetime64[ms]'))
    array([3661001], dtype='timedelta64[ms]')
    >>> datetime64_to_time_of_day(np.datetime64('2012-01-02T01:01:01.001Z','[ms]'))
    numpy.timedelta64(3661001,'ms')
    """
    day = datetime64_array.astype('datetime64[D]').astype(datetime64_array.dtype)
    time_of_day = datetime64_array - day
    return time_of_day

def get_decimal_hours(ds):
    # subtracting 'time_take_off' from observation 'time'
    # this results in a numpy timedelta64 object in nanoseconds
    import numpy as np
    import pandas as pd
    import datetime as dt
    
    ns = list(ds.coords['time'].values-np.datetime64(ds.attrs['time_take_off']))

    # transform ns np.timedelta64 to pd.timedelta.
    # pd.timedelta format has easier to use transformations between nanoseconds, seconds, hours, days
    # will keep decimals/floating number
    hours = pd.to_timedelta(ns[:])/ dt.timedelta (hours=1)
    return(hours)

def sec_since_midnigth(dt_obj):
    # calculating the seconds since midnight from a given datetime object
    # requires: import datetime
    # input: datetime object
    # returns: seconds since midnight
    from datetime import datetime
    
    if isinstance(dt_obj, datetime):
        midnight = dt_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        seconds = (dt_obj - midnight).total_seconds()
        return(seconds)
    else:
        raise Exception(f'Error: The value "{dt_obj}" passed to sec_since_midnigth was not a datetime')

def resolve_date(year, day_num):
    # Resolving date from day number (day_num) and year
    # Input: 
    #       day_num: number of days since 01.01
    #       year: Year in YYYY format
    # Output: date in format YYYY-MM-DD
    from datetime import timedelta
    from dateutil import parser
 
    # creating date string
    date_str = year.astype('int').astype('str') + "-01-01"  # January 1st of the given year
    date_obj = date_str.apply(parser.parse)  # parse date string to datetime object
    
    # creating the days in proper format from series'
    day_obj = day_num.apply(lambda x: timedelta(days=int(x)-1))
 
    # adding days to datetime object
    res = date_obj + day_obj
 
    return res

def read_chunky_csv(textfile, sep=[]):
    """
    Splits information of csv files with different "chucks" of data into a list of lists
    Each chunck gets its own list. The number of lines for each chunck does not matter. 
    # requires: import csv
    # input: path to csv-file, separator to split on: default empty list[]
    # returns: list of lists
    """
    import csv
    
    # read in file as a list of lines
    with open(textfile, encoding='ISO-8859-1') as infile:
        data_list = list(csv.reader(infile))  

    # The datafiles are composed of 5 different "chunks" of information separated by an empty line: 
    # 0: Processing information, 1: Bin information, 2: Notes, 3: Variable information, 5: Data
    # The number of lines in each chunck varies and depends on the preprocessing, number if image files etc.
    # Separate the chunks by splitting on empty lines []:
    sublists = []
    current_sublist = []

    for item in data_list:
        if item == sep:
            if current_sublist:
                sublists.append(current_sublist)
                current_sublist = []
        else:
            current_sublist.append(item)

    if current_sublist:
        sublists.append(current_sublist)
    
    return sublists

def norm_by_bin(bin_start, bin_end, count_value, type_norm=None):
    # normalize the count N in bin j by the width of the bin j
    import numpy as np
    
    if type_norm == 'log':
        norm_value_name = 'dN/dlogDp'
        # calculate dlogDp
        bin_norm = np.log(bin_end)-np.log(bin_start)  
    elif type_norm == None:
        norm_value_name = 'dN/dDp'
        bin_norm = bin_end - bin_start
    else:
        print('Warning: type of normalization not defined')
    
    norm_count_value = count_value/bin_norm  
    
    return(norm_count_value, norm_value_name)

def unnormalize(count_value, binwidth):
    # Function to unnormalize a size spectra
    # INPUT:
        # - count_value: a size spectra/concentration in m^-4
        # - endbins: bin endpoints in micro-m 
    # OUTPUT:
        # - unnorm_count_value: the unnormalized size spectra/concentration (in m⁻3)
    unnorm_count_value = count_value*binwidth/1.0e6 # divide by 10e^6 to get m istead of micro-m 
    
    return(unnorm_count_value)
    
def plot_flight_v_data(flight, df, variable="", save_f=""):
    # Plots the flight path and (optionally) adds a variable along the flightpath as scatterplot points
    # 
    # Input: 
    # flight: flightid, text to be used to select info from dictionary and dataframe
    # df: dataframe with ISLAS data
    # variable: optional value, add if a variable should be plotted as scatter plot on top of flight path
    # save_f: optional filename to save figure to
    
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    
    #-- Map initialization based on flight info --
    
    # get the lat_max, lat_min, long_max and long_min from the given flight
    # stored in nav_stats_dict
    # add small increment for plotting
    inc = 1
    lat_max = df['Latitude (degree)'].max() + inc
    lat_min = df['Latitude (degree)'].min() - inc
    lon_max = df['Longitude (degree)'].max()+ inc
    lon_min = df['Longitude (degree)'].min() - inc

    # coordinates of Kiruna
    # TODO: transform to dictionary?
    lat_kir = 67.8256
    lon_kir = 20.3351

    # select data from only the given flight
    sel_df = df[df['flightid']==flight] 

    # ---- Plot coordinates -----
    # Plotting lat and lon on map

    fig = plt.figure(figsize=(10, 9))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.NorthPolarStereo())

    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linewidth=2)
    data_projection = ccrs.PlateCarree()

    #plot the given flight
    ax.plot(sel_df['Longitude (degree)'], sel_df['Latitude (degree)'], color='tab:blue', 
            label = flight,
            transform=data_projection)

    if variable != "":
        #plot the given variable if it is given
        plt.scatter(x=sel_df['Longitude (degree)'], y=sel_df['Latitude (degree)'],
                color="orangered",
                s=sel_df[variable],
                alpha=0.8,
                label = variable,
                transform=ccrs.PlateCarree()) ## Important

    #Plot Kiruna on map
    ax.plot(lon_kir, lat_kir, marker='o', color='tab:red', transform=data_projection)
    #Add text "Kiruna" at the plotted point
    offset_lon = 0.7  # adjust the horizontal offset
    offset_lat = -0.7  # adjust the vertical offset
    ax.text(lon_kir + offset_lon, lat_kir + offset_lat, "Kiruna", transform=data_projection, ha='right', va='bottom')

    ax.set_extent([lon_min, lon_max, lat_min, lat_max])
    ax.set_title('Flight path with clouds')
    plt.legend(loc='best')

    if save_f != "":
        # save figure in the Figures folder for presentations if filename is given
        plt.savefig(f'Figures/{save_f}')

def add_man_relevance(df):
    # Function to add information about relevance for each timestep. Information about times is taken from flight reports
    # Input: a dataframe that at least contains a 'time' column and a 'flightid' column, flightid should be in the format: 'IS22-XX'
    # Output: the same dataframe, with the added column 'Relevance' Relevance is a categorical value with the following possible values:
    #          'Lower clouds, relevant': Lower clouds, main focus of the campaign
    #          'Lower clouds, endpoints': Loer clouds during the initial ascent or final descent
    #          'Upper clouds': upper cloud, not the main focus here
    #          'No relevance': Default value, usually no cloud 
    
    import numpy as np
    
    # list of conditions to select relevance categories
    conds = [
        # flight IS22-02
        (df['flightid'] == 'IS22-02') & (df['time'] < '2022-03-22 11:58'),
        (df['flightid'] == 'IS22-02') & (df['time']>= '2022-03-22 11:58') & (df['time'] < '2022-03-22 13:55'),
        (df['flightid'] == 'IS22-02') & (df['time']>= '2022-03-22 13:55'),
        # flight IS22-03
        (df['flightid'] == 'IS22-03') & (df['time'] < '2022-03-24 08:15'),
        (df['flightid'] == 'IS22-03') & (df['time']>= '2022-03-24 08:15') & (df['time'] < '2022-03-24 10:45'),
        (df['flightid'] == 'IS22-03') & (df['time']>= '2022-03-24 10:45') & (df['time'] < '2022-03-24 12:00'),
        (df['flightid'] == 'IS22-03') & (df['time']>= '2022-03-24 12:00'),
        # flight IS22-04
        (df['flightid'] == 'IS22-04') & (df['time'] < '2022-03-24 13:29'),
        (df['flightid'] == 'IS22-04') & (df['time']>= '2022-03-24 13:29') & (df['time'] < '2022-03-24 14:34'),
        (df['flightid'] == 'IS22-04') & (df['time']>= '2022-03-24 14:34'),
        # flight IS22-05
        (df['flightid'] == 'IS22-05') & (df['time'] < '2022-03-26 08:20'),
        (df['flightid'] == 'IS22-05') & (df['time']>= '2022-03-26 08:30') & (df['time'] < '2022-03-26 09:42'),
        (df['flightid'] == 'IS22-05') & (df['time']>= '2022-03-26 09:42'),
        # flight IS22-06
        (df['flightid'] == 'IS22-06') & (df['time'] < '2022-03-26 17:00'),
        (df['flightid'] == 'IS22-06') & (df['time']>= '2022-03-26 17:00') & (df['time'] < '2022-03-26 17:30'),
        (df['flightid'] == 'IS22-06') & (df['time']>= '2022-03-26 17:30'),
        # flight IS22-07
        (df['flightid'] == 'IS22-07') & (df['time'] < '2022-03-29 09:50'),
        (df['flightid'] == 'IS22-07') & (df['time']>= '2022-03-29 09:50') & (df['time'] < '2022-03-29 11:40'),
        (df['flightid'] == 'IS22-07') & (df['time']>= '2022-03-29 11:40'),
        # flight IS22-08
        (df['flightid'] == 'IS22-08') & (df['time']>= '2022-03-30 14:00') & (df['time'] < '2022-03-30 15:00'),
        (df['flightid'] == 'IS22-08') & (df['time']>= '2022-03-30 15:00') & (df['time'] < '2022-03-30 16:00'),
        (df['flightid'] == 'IS22-08') & (df['time']>= '2022-03-30 16:00'),
        # flight IS22-09
        (df['flightid'] == 'IS22-09') & (df['time'] < '2022-03-31 09:47'),
        (df['flightid'] == 'IS22-09') & (df['time']>= '2022-03-31 09:47') & (df['time'] < '2022-03-31 11:00'),
        (df['flightid'] == 'IS22-09') & (df['time']>= '2022-03-31 11:00') & (df['time'] < '2022-03-31 13:11'),
        (df['flightid'] == 'IS22-09') & (df['time'] > '2022-03-31 13:11'),
        # flight IS22-10
        (df['flightid'] == 'IS22-10') & (df['time'] < '2022-04-03 07:30'),
        (df['flightid'] == 'IS22-10') & (df['time']>= '2022-04-03 07:30') & (df['time'] < '2022-04-03 09:00'),
        (df['flightid'] == 'IS22-10') & (df['time']>= '2022-04-03 09:00') & (df['time'] < '2022-04-03 10:54'),
        (df['flightid'] == 'IS22-10') & (df['time']>= '2022-04-03 10:54'),
        # flight IS22-11
        (df['flightid'] == 'IS22-11') & (df['time'] < '2022-04-03 12:45'),
        (df['flightid'] == 'IS22-11') & (df['time']>= '2022-04-03 12:56') & (df['time'] < '2022-04-03 15:00'),
        (df['flightid'] == 'IS22-11') & (df['time']>= '2022-04-03 15:00')
    ]
    # list of categories to return
    relevance = [
        # flight IS22-02
        'Upper clouds',
        'Lower clouds, relevant',
        'Upper clouds',
        # flight IS22-03
        'Lower clouds, endpoints',
        'Upper clouds',
        'Lower clouds, relevant',
        'Lower clouds, endpoints',
        # flight IS22-04
        'Lower clouds, endpoints',
        'Lower clouds, relevant',
        'Upper clouds',
        # flight IS22-05
        'Lower clouds, endpoints',
        'Upper clouds',
        'Lower clouds, relevant',
        # flight IS22-06
        'Lower clouds, relevant',
        'Upper clouds',
        'Lower clouds, endpoints',
        # flight IS22-07
        'Upper clouds',
        'Lower clouds, relevant',
        'Upper clouds',
        # flight IS22-08
        'Upper clouds',
        'Lower clouds, relevant',
        'Upper clouds',
        # flight IS22-09
        'Lower clouds, endpoints',
        'Upper clouds',
        'Lower clouds, relevant',
        'Lower clouds, endpoints',
        # flight IS22-10
        'Lower clouds, endpoints',
        'Upper clouds',
        'Lower clouds, relevant',
        'Lower clouds, endpoints',
        # flight IS22-11
        'Lower clouds, endpoints',
        'Lower clouds, relevant',
        'Upper clouds'
    ]
    df['Relevance']=np.select(conds,relevance,"No relevance")
    return df

def add_man_cloud(df):
    # Function to add information about separate clouds measured for each flight. Information about times is taken from flight reports
    # Input: a dataframe that at least contains a 'time' column and a 'flightid' column, flightid should be in the format: 'IS22-XX'
    # Output: the same dataframe, with the added column 'cloudid' in the format 'flightid'-'letter' ('IS22-02-a')
        
    import numpy as np
    
    # list of conditions to set cloud id
    conds = [
        # flight IS22-02
        (df['flightid'] == 'IS22-02') & (df['time']>= '2022-03-22 11:52') & (df['time'] < '2022-03-22 12:44'),
        (df['flightid'] == 'IS22-02') & (df['time']>= '2022-03-22 13:20') & (df['time'] < '2022-03-22 13:55'),
        # flight IS22-03
        (df['flightid'] == 'IS22-03') & (df['time']>= '2022-03-24 10:35') & (df['time'] < '2022-03-24 11:23'),
        # flight IS22-04
        (df['flightid'] == 'IS22-04') & (df['time']>= '2022-03-24 13:29') & (df['time'] < '2022-03-24 14:34'),
        # flight IS22-05
        (df['flightid'] == 'IS22-05') & (df['time']>= '2022-03-26 09:42') & (df['time'] < '2022-03-26 10:14'),
        (df['flightid'] == 'IS22-05') & (df['time']>= '2022-03-26 10:14') & (df['time'] < '2022-03-26 11:09'),
        (df['flightid'] == 'IS22-05') & (df['time']>= '2022-03-26 11:09') & (df['time'] < '2022-03-26 11:37'),
        # flight IS22-06
        (df['flightid'] == 'IS22-06') & (df['time']>= '2022-03-26 14:36 ') & (df['time'] < '2022-03-26 15:09'),
        (df['flightid'] == 'IS22-06') & (df['time']>= '2022-03-26 15:09') & (df['time'] < '2022-03-26 16:35'),
        (df['flightid'] == 'IS22-06') & (df['time']>= '2022-03-26 16:35') & (df['time'] < '2022-03-26 16:54'),
        # flight IS22-07
        (df['flightid'] == 'IS22-07') & (df['time']>= '2022-03-29 09:59') & (df['time'] < '2022-03-29 10:45'),
        (df['flightid'] == 'IS22-07') & (df['time']>= '2022-03-29 10:45') & (df['time'] < '2022-03-29 10:58'),
        (df['flightid'] == 'IS22-07') & (df['time']>= '2022-03-29 11:04') & (df['time'] < '2022-03-29 11:36'),
        # flight IS22-08
        (df['flightid'] == 'IS22-08') & (df['time']>= '2022-03-30 15:05') & (df['time'] < '2022-03-30 15:18'),
        (df['flightid'] == 'IS22-08') & (df['time']>= '2022-03-30 15:20') & (df['time'] < '2022-03-30 15:52'),
        # flight IS22-09
        (df['flightid'] == 'IS22-09') & (df['time']>= '2022-03-31 11:00') & (df['time'] < '2022-03-31 11:44'),
        (df['flightid'] == 'IS22-09') & (df['time']>= '2022-03-31 12:10') & (df['time'] < '2022-03-31 12:43'),
        # flight IS22-10
        (df['flightid'] == 'IS22-10') & (df['time']>= '2022-04-03 09:00') & (df['time'] < '2022-04-03 09:46'),
        (df['flightid'] == 'IS22-10') & (df['time']>= '2022-04-03 09:46') & (df['time'] < '2022-04-03 09:59'),
        (df['flightid'] == 'IS22-10') & (df['time']>= '2022-04-03 09:59') & (df['time'] < '2022-04-03 10:37'),
        # flight IS22-11
        (df['flightid'] == 'IS22-11') & (df['time']>= '2022-04-03 12:50') & (df['time'] < '2022-04-03 13:23'),
        (df['flightid'] == 'IS22-11') & (df['time']>= '2022-04-03 13:35') & (df['time'] < '2022-04-03 14:18'),
        (df['flightid'] == 'IS22-11') & (df['time']>= '2022-04-03 14:18') & (df['time'] < '2022-04-03 14:35'),
        (df['flightid'] == 'IS22-11') & (df['time']>= '2022-04-03 14:35') & (df['time'] < '2022-04-03 15:00')
    ]
    # list of categories to return
    relevance = [
        # flight IS22-02
        'IS22-02-a',
        'IS22-02-b',
        # flight IS22-03
        'IS22-03-a',
        # flight IS22-04
        'IS22-04-a',
        # flight IS22-05
        'IS22-05-a',
        'IS22-05-b',
        'IS22-05-c',
        # flight IS22-06
        'IS22-06-a',
        'IS22-06-b',
        'IS22-06-c',
        # flight IS22-07
        'IS22-07-a',
        'IS22-07-b',
        'IS22-07-c',
        # flight IS22-08
        'IS22-08-a',
        'IS22-08-b',
        # flight IS22-09
        'IS22-09-a',
        'IS22-09-b',
        # flight IS22-10
        'IS22-10-a',
        'IS22-10-b',
        'IS22-10-c',
        # flight IS22-11
        'IS22-11-a',
        'IS22-11-b',
        'IS22-11-c',
        'IS22-11-d'
    ]
    df['cloudid']=np.select(conds,relevance,np.NAN)
    return df

def cloud_alt_pos(df,sel_cats):
    # Function for calculating cloud position categories (top,bulk,base) based on max and min of the in-cloud altitude
    # top: the top-most 25% of the total altitude
    # bulk: the middle 50% of the total altitude
    # base: the lower 25% of the total altitude
    
    # INPUT:
    # df: Dataframe which should at least contain the selection category variable (sel_cats) and the variable 'Altitude (meter)'
    # sel_cats: column name of the column containing the selection categories to use (flightid)
    # OUTPUT:
    # cloud_alt_pos_dict: nested dictionary with selection category (flightid) at upper level, and height values:
    #                     max, min, depth, lower25% higher 25%
    
    # --Preparations
    cats = df[sel_cats].unique() # get the unique categories
    df = df[df['incloud']==True]
    cloud_alt_pos_dict = {} # initiate a new empty dictionary for storing height values (for plotting etc)

    # -- Define cloud positions for each category
    for cat in cats:
        # do not calculate for nan values of category
        if cat != 'nan':
            # calculate the separation lines between the different cloud positions (as integers)
            cl_a_max = int(df[df[sel_cats]==cat]['Altitude (meter)'].max()) # maximal cloud height 
            cl_a_min = int(df[df[sel_cats]==cat]['Altitude (meter)'].min()) # minimal cloud height
            cl_depth = cl_a_max-cl_a_min                                    # cloud depth
            cl_a_low25 = cl_a_min + int(cl_depth/4)                         # lower 25%: minimum + 1/4 of the depth
            cl_a_high25 = cl_a_max - int(cl_depth/4)                        # higher 25%: maximum - 1/4 of the depth
            
            # save these values in a dictionary for further use 
            f_dict = {
                'min':cl_a_min,
                'low_25':cl_a_low25,
                'high_25':cl_a_high25,
                'max':cl_a_max,
                'depth':cl_depth
            }
            cloud_alt_pos_dict[cat]=f_dict # update the main dictionary of height values connected to the correct flight

    return cloud_alt_pos_dict

def set_c_pos_cat(row, cloud_pos_dict):
    # Function to set a categorical variable to "Top", "Bulk" "Base" based on threshold values hold in a dictionary
    # The dictionary 'cloud_pos_dict' with thresholds for cloud positions for each flightid needs to exist
    # input: 
    #    row: row of dataframe with cloud altitudes and flights
    # output: 
    #    Value = {'Top', 'Bulk', 'Base', 'unknown'} to add to dataframe
    # 

    cloud_id = row['cloudid']
    altitude = row['Altitude (meter)']
    
    # Fetch thresholds from the dictionary (if dictionary does not exist give error message)
    try:
        thresholds = cloud_pos_dict.get(cloud_id)
    except NameError:
        print('The dictionary cloud_pos_dict is not available. Create this to fix this error')

    #only calculate thresholds if 'in-cloud'
    if row['incloud']:
    
        if thresholds is not None:
            low_threshold = thresholds['low_25']
            high_threshold = thresholds['high_25']
            
            if altitude > high_threshold:
                return 'Top'
            elif altitude < low_threshold:
                return 'Base'
            else:
                return 'Bulk'
        else:
            return 'unknown'  # In case the flight ID is not in the dictionary
    else:
        return
        

def get_ax_vals(df, param, value, ax):
    # Function to transform the first and last time value of dataframe (df) where a specific column (param) 
    # equals a specific value (value)
    # returns an xmax and an xmin value in axes coordinates
    # Used to get axes coordinates to set axhspan boxes in correct locations
    import matplotlib.dates as mdates

    # get x values for the cloud (data coordinates)
    xmin_data = mdates.date2num(df[df[param]==value]['time'].min())
    xmax_data = mdates.date2num(df[df[param]==value]['time'].max())

    # convert data coordinates to display coordinates
    xmin_display, _ = ax.transData.transform((xmin_data, 0))
    xmax_display, _ = ax.transData.transform((xmax_data, 0))
    
    # convert display coordinates to axes coordinates
    xmin_axes, _ = ax.transAxes.inverted().transform((xmin_display, 0))
    xmax_axes, _ = ax.transAxes.inverted().transform((xmax_display, 0))

    return xmin_axes,xmax_axes

def rel_alt(row, cloudids, cloud_alt_dict):
    # normalize the in cloud altitude
    if row['cloudid'] in cloudids:
        if row['incloud'] == True:
            # get min altitude and depth for cloud
            cmin = cloud_alt_dict[row['cloudid']]['min']
            cdep = cloud_alt_dict[row['cloudid']]['depth']
            # calculate the relative altitude in cloud
            return (row['Altitude (meter)']-cmin)/cdep
        
def prep_numb_conc(cdp_bulk_df, cdp_bins_df, cip_bulk_df, cip_bins_df):
    import pandas as pd
    import numpy as np
    import analysis.functions as functions
    
    
    # Prepare number concentration data for histogram
    
    # CIP data preparations ----
    # CIP bin counts are normalized by bin width and needs to be unnormalized before log normalizing
    # Filter out just the columns starting with Conc (concentrations in bin number X)
    filter_col = [col for col in cip_bulk_df if col.startswith('Conc')]
    cip_numb_conc = cip_bulk_df[filter_col]
    
    # get the mean of number concentrations for each size bin
    cip_numb_conc_mean = pd.DataFrame(cip_numb_conc.mean(), columns = ['count'])
    
    # Join the bin information for easier access when plotting
    cip_numb_conc_mean = pd.merge(cip_numb_conc_mean, cip_bins_df, left_index=True, right_on="Bin_name")
    
    # ignore bins with end points lower than 125 (midpoint lower than 100) 
    cip_numb_conc_mean =  cip_numb_conc_mean[cip_numb_conc_mean['Bin midpoints (microns):'] >= 100]
  
    # the cip bin counts are normalized by bin width, unnormalize
    cip_numb_conc_mean['unnorm'] = functions.unnormalize(cip_numb_conc_mean['count'], (cip_numb_conc_mean['Bin endpoints (microns):']-cip_numb_conc_mean['Bin startpoints (microns)']))
    # log normalize cip data
    cip_numb_conc_mean['count_norm'] = cip_numb_conc_mean['unnorm']/(np.log(cip_numb_conc_mean['Bin endpoints (microns):']*1.e-6)-np.log(cip_numb_conc_mean['Bin startpoints (microns)']*1.e-6))
    #Checking for what happens when I keep the original normalization
    cip_numb_conc_mean['count_norm'] = cip_numb_conc_mean['count']
    
    
    # CDP data preparation ----
    # CDP Bin # contains the number of particles counted for that size bin (not normalized)
    # Filter out just the columns starting with Conc (concentrations in bin number X)
    filter_col = [col for col in cdp_bulk_df if col.startswith('CDP Bin')]
    cdp_counts_per_bin = cdp_bulk_df[filter_col]
    
    # the counts from the cdp are raw counts, needs to adjust them to sample volume
    # this is a matrix multiplication, so the shapes of the matrizes must match up the correct way:
    # if a.shape=(10,) and b.shape=(10,2) they will need to match as (2,10)(10,) .T transposes the matrix so that
    # (b.T/a).shape = (2,10) (and to get the shape we want: (b.T/a).T.shape = (10,2))
    cdp_numb_conc = (cdp_counts_per_bin.T/cdp_bulk_df['SV (m^3)']).T
   
    # get the total sum and mean of number concentrations for each size bin
    cdp_numb_conc_mean = pd.DataFrame(cdp_numb_conc.mean(), columns = ['count'])

    # join with bin information for easier access when plotting, and normalizing
    cdp_numb_conc_mean = pd.concat([cdp_numb_conc_mean.reset_index(drop=True),cdp_bins_df.reset_index(drop=True)], axis=1)

    # normalize the values from the log of the bin-width (in m)
    cdp_numb_conc_mean['count_norm'] = cdp_numb_conc_mean['count']/(np.log(cdp_numb_conc_mean['Size (microns)']*1.e-6)-np.log(cdp_numb_conc_mean['Min size']*1.e-6))
    
    return(cdp_numb_conc, cip_numb_conc)

def safireid_to_islasid(df, extra_landing):
    # Function to add islasid to df based on 'safireid' and extra landing information
    import numpy as np
    
    # check if 'safireid' and 'time' are columns in df
    if set(['safireid','time']).issubset(df.columns):

        # if based on time column
        conditions = [
            (df['safireid']=='as220006'),
            (df['safireid']=='as220007'),
            (df['safireid']=='as220008') & (df['time'] <= extra_landing),
            (df['safireid']=='as220008') & (df['time'] > extra_landing),
            (df['safireid']=='as220009'),
            (df['safireid']=='as220010'),
            (df['safireid']=='as220011'),
            (df['safireid']=='as220012'),
            (df['safireid']=='as220013'),
            (df['safireid']=='as220014'),
            (df['safireid']=='as220015')
            ]
        
        # New flightids
        values = ['IS22-01','IS22-02','IS22-03','IS22-04','IS22-05','IS22-06','IS22-07','IS22-08','IS22-09','IS22-10','IS22-11']
        
        df['flightid'] = np.select(conditions, values, default = None) # create new column with the new fligthids
        df['flightid'] = df['flightid'].astype("category") # make sure that flight is of type "category")
    else:
        # Return useable errormessage (TODO)
        print('ERROR: missing columns safireid and time')
    
    return df

def update_land(row):
    # Function to use globe_land_mask to check each lat, lon pair if land.
    # Returns the original value of 'surface_cond' if not land and 'land' if land

    # import package
    from global_land_mask import globe
    
    if globe.is_land(row['Latitude (degree)'], row['Longitude (degree)']):
        return 'land'
    return row['surface_cond']



def cdp_df_to_netcdf(cdp_nav_df, cdp_list, meta_df, chan_list, bins_df, source_files, path_store):
    # function to turn the results from the function read_cdp into a netcdf file
    # INPUT: 
    # -- cdp_nav_df: dataframe with combined cdp and nav observations
    # -- cdp_list: metadata with pads information
    # -- meta_df: metadata with instrument information
    # -- chan_list: metadata with channel information
    # -- source_files: csv-files used to generate the cdp_nav_df
    # -- path_store: where to store the netcdf file
    # OUTPUT:
    # --ds: Returns the dataset generated
    

    # Imports
    import xarray as xr
    import pandas as pd
    
    
    # Gather the Bin counts in one df, for 2D xr.DataArray
    bin_count_df = cdp_nav_df[['CDP Bin 1','CDP Bin 2', 'CDP Bin 3', 'CDP Bin 4', 'CDP Bin 5', 'CDP Bin 6','CDP Bin 7', 'CDP Bin 8', 'CDP Bin 9', 'CDP Bin 10', 'CDP Bin 11','CDP Bin 12', 'CDP Bin 13', 'CDP Bin 14', 'CDP Bin 15', 'CDP Bin 16','CDP Bin 17', 'CDP Bin 18', 'CDP Bin 19', 'CDP Bin 20', 'CDP Bin 21','CDP Bin 22', 'CDP Bin 23', 'CDP Bin 24', 'CDP Bin 25', 'CDP Bin 26','CDP Bin 27', 'CDP Bin 28', 'CDP Bin 29', 'CDP Bin 30']]
    
    # Creating coordinates for the cdp data
    coords = {
        'time': cdp_nav_df['time'],
        'lat': ('time', cdp_nav_df['Latitude (degree)']),
        'lon': ('time', cdp_nav_df['Longitude (degree)']),
        'alt': ('time', cdp_nav_df['Altitude (meter)'])
    }
    
    # drop duplicate times
    # remove any duplicated times
    cdp_nav_df = cdp_nav_df[~cdp_nav_df['time'].duplicated(keep='first')]

    ds = xr.Dataset({
        # variables with dimension 'time'
        'End Seconds': xr.DataArray(data = cdp_nav_df['End Seconds'], dims = ['time'],coords = coords,attrs  = {}),
        'Day of Year': xr.DataArray(data = cdp_nav_df['Day of Year'], dims = ['time'],coords = coords,attrs  = {}),
        'Year': xr.DataArray(data = cdp_nav_df['Year'], dims = ['time'],coords = coords,attrs  = {}),
        'Status': xr.DataArray(data = cdp_nav_df['Status'], dims = ['time'],coords = coords,attrs  = {}),
        'DOF Reject Counts': xr.DataArray(data = cdp_nav_df['DOF Reject Counts'], dims = ['time'],coords = coords,attrs  = {}),
        'Avg Transit Reject': xr.DataArray(data = cdp_nav_df['Avg Transit Reject'], dims = ['time'],coords = coords,attrs  = {}),
        'Avg Transit Time': xr.DataArray(data = cdp_nav_df['Avg Transit Time'], dims = ['time'],coords = coords,attrs  = {}),
        'DT Bandwidth': xr.DataArray(data = cdp_nav_df['DT Bandwidth'], dims = ['time'],coords = coords,attrs  = {}),
        'Dynamic Threshold': xr.DataArray(data = cdp_nav_df['Dynamic Threshold'], dims = ['time'],coords = coords,attrs  = {}),
        'ADC Overflow': xr.DataArray(data = cdp_nav_df['ADC Overflow'], dims = ['time'],coords = coords,attrs  = {}),
        'Laser Current': xr.DataArray(data = cdp_nav_df['Laser Current (mA)'], dims = ['time'],coords = coords,attrs  = {'unit': 'mA'}),
        'Dump Spot Monitor': xr.DataArray(data = cdp_nav_df['Dump Spot Monitor (V)'], dims = ['time'],coords = coords,attrs  = {'unit': 'V'}),
        'Wingboard Temp': xr.DataArray(data = cdp_nav_df['Wingboard Temp (C)'], dims = ['time'],coords = coords,attrs  = {'unit': 'C'}),
        'Laser Temp': xr.DataArray(data = cdp_nav_df['Laser Temp (C)'], dims = ['time'],coords = coords,attrs  = {'unit': 'C'}),
        'Sizer Baseline': xr.DataArray(data = cdp_nav_df['Sizer Baseline (V)'], dims = ['time'],coords = coords,attrs  = {'unit': 'V'}),
        'Qualifier Baseline': xr.DataArray(data = cdp_nav_df['Qualifier Baseline (V)'], dims = ['time'],coords = coords,attrs  = {'unit': 'V'}),
        '5V Monitor': xr.DataArray(data = cdp_nav_df['+5V Monitor (V)'], dims = ['time'],coords = coords,attrs  = {'unit': 'V', 'name': '+5V Monitor'}),
        'Control Board T': xr.DataArray(data = cdp_nav_df['Control Board T (C)'], dims = ['time'],coords = coords,attrs  = {'unit': 'C'}),
        'Number Conc': xr.DataArray(data = cdp_nav_df['Number Conc (#/cm^3)'], dims = ['time'],coords = coords,
                                    attrs  = {'longname':'Particle number concentration','unit': '#/cm^3', 'range': [0,2000]}),
        'LWC': xr.DataArray(data = cdp_nav_df['LWC (g/m^3)'], dims = ['time'],coords = coords,
                            attrs  = {'longname': 'Liquid Water Content','unit': 'g/m^3'}),    
        'MVD': xr.DataArray(data = cdp_nav_df['MVD (um)'], dims = ['time'],coords = coords,
                            attrs  = {'longname':'Median Volume Diameter','unit': 'um'}),
        'ED': xr.DataArray(data = cdp_nav_df['ED (um)'], dims = ['time'],coords = coords,
                           attrs  = {'longname':'Effective diameter','unit': 'um'}),
        'Applied PAS': xr.DataArray(data = cdp_nav_df['Applied PAS (m/s)'], dims = ['time'],coords = coords,attrs  = {'unit': 'm/s', 'description' : 'Probe Air Speed (PAS) used during data collection for adjusting variables'}),
        'TAS': xr.DataArray(data = cdp_nav_df['TAS (m/s)'], dims = ['time'],coords = coords,attrs  = {'unit': 'm/s', 'description':'True Air Speed (TAS) from navigational data'}),
        #----------- remove later
        'TAS correction factor': xr.DataArray(data = cdp_nav_df['TAS correction factor'], dims = ['time'], coords = coords,attrs={'name':'TAS correction factor',
                                                                           'description': 'Correction factor for TAS depended variables. (aircraft TAS/PAS from probe calculations from Frey(2011)',
                                                                           'parent variables':['Applied PAS','TAS'] }),
        'Number Conc corr': xr.DataArray(data = cdp_nav_df['Number Conc corr (#/cm^3)'], dims = ['time'], coords = coords,attrs={'name':'Number concentration TAS corrected',
                                                                'unit':'#/cm^3',
                                                                'description': 'Number concentration corrected with the TAS correction factor',
                                                               'parent variables':['Number Conc','TAS correction factor'] }),
        'LWC corr': xr.DataArray(data = cdp_nav_df['LWC corr (g/m^3)'], dims = ['time'], coords = coords,attrs={'name':'Liquid water content TAS corrected',
                                                                'unit':'g/m^3',
                                                                'description': 'Liquid water content corrected with the TAS correction factor',
                                                               'parent variables':['LWC','TAS correction factor']}),
        #----------- remove
        'SV': xr.DataArray(data = cdp_nav_df['SV (m^3)'], dims = ['time'], coords = coords,attrs={'name':'Sample volume',
                                    'unit':'m^3',
                                    'description': 'Sample volume calculated (sample area SA * TAS redused * sample time (1 sek))',
                                    'parent variables':['TAS reduce'],
                                    'parent attributes': ['Sample Time (sec)','Sample Area (mm^2)'] }),                                                   
        # variables with dimesion 'bin'
        'Bin_min':xr.DataArray(data = bins_df['Min size'], dims = ['CDP_Bin'], coords = {'CDP_Bin': bins_df.index},attrs = {'unit': 'um', 'description':'Lower bin size'}),
        'Size':xr.DataArray(data = bins_df['Size (microns)'], dims = ['CDP_Bin'], coords = {'CDP_Bin': bins_df.index},attrs = {'unit': 'um', 'description':'Upper bin size'}),
        'Threshold':xr.DataArray(data = bins_df['Threshold'], dims = ['CDP_Bin'], coords = {'CDP_Bin': bins_df.index},attrs = {'description':'Upper ADC Threshold'}),
        'Width':xr.DataArray(data = bins_df['Width'], dims = ['CDP_Bin'], coords = {'CDP_Bin': bins_df.index},attrs = {'description':'Bin width'}),
        'CDP Bin Particle Count': xr.DataArray(data = bin_count_df,dims = ['time','CDP_Bin'],coords = {'time': cdp_nav_df['time'], 'lat': ('time', cdp_nav_df['Latitude (degree)']),'lon': ('time', cdp_nav_df['Longitude (degree)']), 'alt': ('time', cdp_nav_df['Altitude (meter)']), 'CDP_Bin': bins_df.index},attrs = {'description': 'Number of particles detected in each of the CDP sizing bins during the current sampling interval.'})   
        },
            attrs = {'description': 'Updated CDP data from a single flight during the ISLAS campaign in 2022. Nav-information (time, lat, lon, alt, TAS and islasid) is added to raw cdp data. TAS-corrected LWC and number concentration is added',
                     'safireid': cdp_nav_df['safireid'].unique()[0],
                    'islasid': cdp_nav_df['flightid'].unique()[0],
                    'source files': source_files}
        )

    
    # UPDATING METADATA/ATTRIBUTES
    # Add PADS metadata (from the second item of cdp_list)
    for item in cdp_list:
        # Create key-value pairs by splitting each item on =
        key, value = item[0].split('=', 1)
        # add as attributes to xarray
        ds = ds.assign_attrs({key.strip():value.strip()}) # strip to remove leading and trailing whitespace

    # ADD instrument metadata to attributes
    for index, row in meta_df.iterrows():
        ds = ds.assign_attrs({row['Metadata']:row['Value']})
    
    # ADD housekeeping channel information as attributes to the housekeeping channels
    ds = ds.assign_attrs({'Housekeeping channel description': 'The first 8 channels in the original data packet are analog-to-digital signals that must be converted by the data system (e.g., PADS) into meaningful numbers. The data arrive in hex format. PADS or another data system must then use a scaling algorithm specified within the program to yield results such as laser current, dump spot monitor voltage, etc.'})
    
    # Prepare lists to collect the parsed information
    channels = []
    names = []
    equations = []
    coefficients = []
    
    # Iterate over the list and parse each attribute
    for line in chan_list[1:]:  # Skip the first line 'Channels=<8>'
        parts = line.split('=')
        if 'Name' in line:
            channels.append(parts[0].split()[1].split('.')[0])
            names.append(parts[1].lstrip('+'))
        elif 'Equation' in line:
            equations.append(parts[1])
        elif 'Coefficients' in line:
            coefficients.append(parts[1].lstrip('<5>').strip())
    
    # Create a DataFrame
    df = pd.DataFrame({
        'channel': channels,
        'Name': names,
        'Equation': equations,
        'Coefficients': coefficients
    })
    
    for index, row in df.iterrows():
        var = row['Name'].split('(')[0].strip() # get variable name by removing unit
        ds[var] = ds[var].assign_attrs({'Housekeeping channel number': row['channel'], 'longname':row['Name'],'Equation scaling algorithm':row['Equation'], 'Coefficients':row['Coefficients']})
    
    # save as netcdf
    print(f'{path_store}CDP_updated_{ds.attrs['islasid']}.nc')
    ds.to_netcdf(f'{path_store}CDP_updated_{ds.attrs['islasid']}.nc','w')
    
    return ds
        

def find_unique_listkey(dict, sub_key):
    values = []
    
    for key in dict:
        #print(dict[key].keys())
        if sub_key in dict[key].keys():
          values.append(dict[key][sub_key][0])
    
    # Return all unique values
    return set(values)

def floor_to_sec_res(ds, time_dim):
    # function to floor the time to whole seconds
    import pandas as pd
    # Convert to pandas datetime index
    datetime_index = pd.to_datetime(ds[time_dim].values) # turn into datetime index
    floored_time = datetime_index.floor('s') # floor on seconds

    return ds.assign_coords({time_dim: floored_time})

def reduce_to_bin_dim(ds):
    # function to reduce away the time dimension for variables that are consistent over time
    # for the selection of variables that are not actually time dependent
    # -- some datavariables have only one of the binning dimensions (Vector64, Vector40 or CDP Bin) as dimensions.
    # these datavariables describe some element of the binning categories and are the same throughout the datasets.
    # during the joining, the time dimension is unnecessarily added to these varables. This part of the code reduces the dimensions of these 
    # variables back to only the binning dimensions:
    # Variables: MIDBINS (Vector64),SA (Vector64),INTMIDBINS (Vector40),Bin_min (CDP_Bin),Size (CDP_Bin),Threshold (CDP_Bin),Width (CDP_Bin)

    import numpy as np
    
    for var in ['Size','Bin_min','MIDBINS','SA','INTMIDBINS','Threshold','Width']:
       if 'time' in ds[var].dims:
          # if time is a dimension for this variable
          ds[var]=ds[var].reduce(np.median,dim='time',keep_attrs=True) # reduce time dimension
    return ds

def alt_cat_separator(ds, outer_layers=2, num_layer =2, precip=True):
    # Function to take the altitude bins form a dataset and divide them into different altitude categories for selecting data
    # INPUT:
    # --- ds: dataset in xarray format. Needs to have the value 'altitude_bin'
    # --- outer_layers: number of bins to put in 'top' and 'base' category. Default = 2
    # --- precip: whether or not the lowest layer should be considered precip and get its own category. Default = True
    # OUTPUT:
    # --- precip_list: list of the bin to be considered precip
    # --- base_list: list of the bins to be considered base of cloud
    # --- bulk_list: list of the bins to be considered bulk of cloud
    # --- top_list: list of the bins to be considered top of cloud
    # --- alt_cats: list of all bins

    import numpy as np
    
    alt_cats = np.unique(ds['altitude_bin'].values).tolist() # create list of the unique altitude bins
    
    l = len(alt_cats) # Number of categories
    if precip == True:
        print('creating categories, including precip layer')
        if num_layer == 2:
            l_min = 2 + (outer_layers*2) # minimum number of layers is 2 times the number of outer layers and 1 layer for precip and one layer for bulk
            if l >= l_min:
                # there is enough layers to use the given number of outer layers
                precip_list = alt_cats[0:1]
                base_list = alt_cats[1:(1+outer_layers)]
                bulk_list = alt_cats[3:(l-outer_layers)]
                top_list = alt_cats[(l-outer_layers):l]
            elif l == 4 :
                print('WARNING: the number of altitude categories only allow for one layer per category!')
                precip_list = alt_cats[0:1]
                base_list = alt_cats[1:2]
                bulk_list = alt_cats[2:3]
                top_list = alt_cats[3:4]
            else:
                print('ERROR: two few altitude categories, check data')
                return
            return precip_list,base_list,bulk_list,top_list,alt_cats
        elif num_layer == 1:
            l_min = 2 + outer_layers # minimum number of layers is 2 times the number of outer layers and 1 layer for precip and one layer for bulk
            if l >= l_min:
                # there is enough layers to use the given number of outer layers
                precip_list = alt_cats[0:1]
                bulk_list = alt_cats[1:(l-outer_layers)]
                top_list = alt_cats[(l-outer_layers):l]
            elif l == 4 :
                print('WARNING: the number of altitude categories only allow for one layer per category!')
                precip_list = alt_cats[0:1]
                bulk_list = alt_cats[1:3]
                top_list = alt_cats[3:4]
            else:
                print('ERROR: two few altitude categories, check data')
                return
            return precip_list,bulk_list,top_list,alt_cats
    else:
        print('Creating categories, without precip layer')
        if num_layer == 2:
            l_min = 1 + (outer_layers*2) # minimum number of layers is 2 times the number of outer layers and one layer for bulk
            if l >= l_min:
                # there is enough layers to use the given number of outer layers
                base_list = alt_cats[0:outer_layers+1]
                bulk_list = alt_cats[outer_layers:(l-outer_layers+1)]
                top_list = alt_cats[(l-outer_layers):l]
            elif l == 3 :
                print('WARNING: the number of altitude categories only allow for one layer per category!')
                base_list = alt_cats[0:1]
                bulk_list = alt_cats[1:2]
                top_list = alt_cats[2:3]
            else:
                print('ERROR: two few altitude categories, check data')
                return
            return base_list,bulk_list,top_list,alt_cats
        elif num_layer == 1:
            l_min = 1 + outer_layers # minimum number of layers is 2 times the number of outer layers and one layer for bulk
            if l >= l_min:
                # there is enough layers to use the given number of outer layers
                bulk_list = alt_cats[0:(l-outer_layers)]
                top_list = alt_cats[(l-outer_layers):l]
            elif l == 3 :
                print('WARNING: the number of altitude categories only allow for one layer per category!')
                bulk_list = alt_cats[0:2]
                top_list = alt_cats[2:3]
            else:
                print('ERROR: two few altitude categories, check data')
                return
            return bulk_list,top_list,alt_cats
        