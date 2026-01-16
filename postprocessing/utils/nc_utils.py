#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  23 13:30:26 2025
Scripts related to handling netcdfs in the islas processing

@author: ninalar
"""

def nc_save_with_check(savefile ,xds):
    """Check if a netCDF file exists. Overwrite existing if user accepts, create new if not existing.

    This function relies on the 'os' package for path management.

    Parameters
    ----------  
        savefile: str
            Path to netCDF file
        xds: xarray.DataSet 
            Dataset to write to savefile

    """
    import os

    # Check if the file exists
    if os.path.exists(savefile):
        overwrite = input(f'The file {savefile} exists. Do you want to overwrite it?(y/n)')
        if overwrite.lower() in ["yes", "y"]:
            print(f'Saving to {savefile}')
            xds.to_netcdf(path=savefile, mode='a')
        else:
            print("Exiting...")
    else:
        xds.to_netcdf(path=savefile, mode='w')
        print(f'Saving to {savefile}')
        
    return

def cdp_to_df(filelist, flight):
    """
    Function to turn the CDP csv-files into pandas dataframes ready to use in NetCDF creation 

    This function relies on the 'pandas' package, and needs to import the 'read_chunky_csv' function from nc_utils and the 'resolve_date' from func_nc

    Parameters
    ----------
    filelist: list
        list of filenames to extract cdp information from
    flight: str
        Flightid the data are supposed to come from

    Returns
    ----------
    total_cdp_df: pd.DataFrame
        dataframe containing the CDP variables
    filenames: list
        list of filenames uest to make the df
    meta_df: pd.DataFrame
        dataframe containing metadata for the instruments
    chan_list: list
        List containing channel setup for the instrument
    pads_info_df: pd.DataFrame
        dataframe containing informaiton about pads settings
    bins_df: pd.DataFrame
        dataframe with settings and limits for the cdp bins
    """
    import pandas as pd
    from utils.nc_utils import read_chunky_csv
    from utils.func_nc import resolve_date

    # initiation lists and dicts
    total_cdp_df = []  # empty list for appending all data to one structure
    #meta_dict = {}
    filenames = []

    #in each directory there is a CDP-csv file
    for i,file in enumerate(filelist):
        print('Reading: ' + file) 
        # reading in csv data without metadata, csv file structured with empty line between different chuncks   
        cdp_list = read_chunky_csv(file)
        
        # --- Get data information from 2th chunk. Turn this into a dataframe:
        data = cdp_list[2]
        data.pop(0) # remove separator line
        header = data.pop(0) #get header
        cdp_df = pd.DataFrame(data) # turn into dataframe
        cdp_df = cdp_df.astype(float) # change from string to float
        cdp_df.columns = header #add header information to df
        cdp_df["safireid"]=flight # add flight information
    
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
            
        # Turn bin_list (list of strings) into dataframe of bin information
        # Take entry that includes size or threes, remove the parts of the string that is not values, turn into list
        size_list = [i for i in bin_list if 'Size' in i][0].replace("Sizes=<30>","",1).split(" ")
        thr_list = [i for i in bin_list if 'Thres' in i][0].replace("Thresholds=<30>","",1).split(" ")
        
        # Make list of lower edges
        # lower edge of the first bin is in the metadata, the rest is the same as the size list -last entry
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


        #extract only filename from file and add to list of filenames
        filename = file.split('/')[-1]
        filenames.append(filename)
        #flight_dict[i]={'filename':filename,'islasids':flight, 'pads info': cdp_list[1], 'instrument info': meta_df, 'channel info':chan_list}
        total_cdp_df.append(cdp_df) # append list with the new dataframe


    # Join the results from all the files into one df
    total_cdp_df = pd.concat(total_cdp_df)

    # remove empthy columns ('Spare #')
    total_cdp_df = total_cdp_df.loc[:,~total_cdp_df.columns.str.startswith('Spare')]

     # Update index and remove duplicates from dataframe
    total_cdp_df['time']=pd.to_datetime(total_cdp_df['time'])
    total_cdp_df['time']=total_cdp_df['time'].dt.floor('s') # floor to second for easier handling
    total_cdp_df = total_cdp_df.set_index('time')
    
    #remove any duplicates in the dataframe
    total_cdp_df = total_cdp_df[~total_cdp_df.index.duplicated(keep='first')]


    # check that only one safireid and that it is equal to the given one
    test_ids = total_cdp_df['safireid'].unique()

    if len(test_ids) == 1:
        #check that only one flight id is given
        if test_ids == flight:
            #test that it is equal to the one chosen
            #if everything ok drop safireid from dataframe
            total_cdp_df = total_cdp_df.drop('safireid',axis=1)
    else:
        print('more than one safireid in dataframe')

    return total_cdp_df, filenames, meta_df, chan_list, pads_info_df, bins_df

def add_cdp_df_to_xds(xds, df, meta_df, pads_df):
    """
    Function to add CDP dfs to existing xds inpreparation for NetCDF 

    This function relies on the 'xarray' and 're' package

    Parameters
    ----------
    xds: xarray DataSet
        xarray with coordinates and temperature from the related nav file
    df: pandas Dataframe
        dataframe containing the observational variables from the cpd
    meta_df: pandas Dataframe
        dataframe containing metadata for instruments
    pads_df: pandas Dataframe
        dataframe containing metadata for pads setup

    Returns
    ----------
    cdp_xds: Xarray.Dataset
        xarray updated with the variables from df
    """
    import xarray as xr
    import re

    ds_from_df = xr.Dataset.from_dataframe(df) # create xr.dataset from the original df

    # set joint metadata for variables
    for var_name, variable in ds_from_df.data_vars.items():
        ds_from_df[var_name].attrs['source'] = 'CDP' # update data variables

    # Selecting only the times from the nav where the cdp has values
    cdp_xds = xr.merge([ds_from_df,xds], join='inner')

    # add metadata as global attributes to the xds
    for index, row in meta_df.iterrows():
        cdp_xds.attrs[row['Metadata']]=row['Value']

    for index, row in pads_df.iterrows():
        cdp_xds.attrs[row['Info']]=row['Value'] 

    #-- Update metadata
    # Update metadata: units from units in name
    # get list of data variable names
    var_list = list(cdp_xds.data_vars)

    for var in var_list:
        unit = var[var.find("(")+1:var.find(")")]
        if var[0:-1]!=unit:
            cdp_xds[var].attrs['units']= unit
            no_parentheses = re.match(r'[^())]*',var)
            cdp_xds[var].attrs['long_name'] = no_parentheses.group(0).strip() # longname is name without unit
            # rename vars to name without unit
            cdp_xds = cdp_xds.rename_vars({var:no_parentheses.group(0)})


    return cdp_xds

def binned_cdp_to_xds(bins_df, cdp_bin_df):
    """
    Function to turn the binned CDP variables (counts) saved in pandas dataframes into an xarray structure 

    This function relies on the 'xarrat' package

    Parameters
    ----------
    bins_df: pandas Dataframe
        dataframe with bin information: 'Bin_min', 'Size', 'Threshold', 'Width' per CDP_bin 1-30
    cdp_bin_df: pandas Dataframe
        dataframe containing the particle counts per size bin, index: 'time'

    Returns
    ----------
    bins_xds: Xarray.Dataset
        xarray with dimenstions 'time' and 'CDP_bin'
    """
    import xarray as xr
    
    # Create xarray of bins_df and add to cdp_xds
    bins_xds = xr.Dataset({                                                 
                'Bin_min':xr.DataArray(data = bins_df['Min size'], dims = ['CDP_Bin'], coords = {'CDP_Bin': bins_df.index},attrs = {'unit': 'um', 'description':'Lower bin size'}),
                'Size':xr.DataArray(data = bins_df['Size (microns)'], dims = ['CDP_Bin'], coords = {'CDP_Bin': bins_df.index},attrs = {'unit': 'um', 'description':'Upper bin size'}),
                'Threshold':xr.DataArray(data = bins_df['Threshold'], dims = ['CDP_Bin'], coords = {'CDP_Bin': bins_df.index},attrs = {'description':'Upper ADC Threshold'}),
                'Width':xr.DataArray(data = bins_df['Width'], dims = ['CDP_Bin'], coords = {'CDP_Bin': bins_df.index},attrs = {'description':'Bin width'}),
                'CDP Bin Particle Count': xr.DataArray(data = cdp_bin_df,
                                                dims = ['time','CDP_Bin'],
                                                coords = {'CDP_Bin': bins_df.index, 'time': cdp_bin_df.index},
                                                attrs = {'description': 'Number of particles detected in each of the CDP sizing bins during the current sampling interval.'})   
                })
    return bins_xds

def read_chunky_csv(textfile, sep=[]):
    """
    Function that splits information of csv files with different "chucks" of data into a list of lists
    Each chunck gets its own list. The number of lines for each chunck does not matter. 

    This function relies on the 'csv' package

    Parameters
    ----------
    textfile: str
        path to csv-file
    sep: str
        separator to split on: default empty list[]

    Returns
    ----------
    sublists: list of lists
        List of lists where each list is one "chunck" of the file
    """
    import csv
    
    # read in file as a list of lines
    with open(textfile, encoding='ISO-8859-1') as infile:
        data_list = list(csv.reader(infile))  

    # The cdp datafiles are composed of 5 different "chunks" of information separated by an empty line: 
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
        'SV': xr.DataArray(data = cdp_nav_df['SV (m^3)'], dims = ['time'], coords = coords,attrs={'name':'Sample volume',
                                    'unit':'m^3',
                                    'description': 'Sample volume calculated (sample area SA * TAS * sample time (1 sek))',
                                    'parent variables':['TAS'],
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
    print(f'{path_store}CDP_updated_{ds.attrs["islasid"]}.nc')
    ds.to_netcdf(f'{path_store}CDP_updated_{ds.attrs["islasid"]}.nc','w')
    
    return ds

# NOTE: This is the new, simplified version that only adds 
def update_cip_nc(cip_nc_file, nav_nav_file, flight):
    """ Add coordinates(from nav) and metadata to CIP nc file

    This function relies on the packages 'xarray','numpy' and 're' for datamanagement and calculations,
    the date function from datetime for date management and the local function floor_to_sec_res from utils_func.nc.

    Parameters
    ----------
    cip_nc_file
        CIP NetCDF file from flight
    nav_file
        Navigation file from flight
    flight
        islasid of flight

    Returns
    -------
    cip_updated_xds
        xarray dataset from the CIP file updated with coordinates from the core nav file
    """
    import xarray as xr # read netcdf-files
    import numpy as np
    import re #regex
    from datetime import date
    from utils.func_nc import floor_to_sec_res
    from utils.meta_utils import attrs_from_list, var_attrs_from_list
    
    cip_xds = xr.open_dataset(cip_nc_file) # the cip xarray (from soda)
    nav_nav_xds = xr.open_dataset(nav_nav_file) # the nav file xarray

    # CIP preparations: fix time dimension cip_xds
    cip_xds = cip_xds.rename_vars({'elapsed_time':'time'}) # elapsed time holds the correct time to use, change name to time for simplicity
    cip_xds = cip_xds.set_coords('time') # set as coordinate 
    cip_xds = cip_xds.swap_dims({'Time': 'time'}) # set as main dimension
    cip_xds = floor_to_sec_res(cip_xds,'time') # floor the times to sec for easier joining

    # NAV preparations: drop duplicate time steps (in nav)
    index = np.unique(nav_nav_xds.time, return_index = True)[1]
    nav_nav_xds = nav_nav_xds.isel(time=index)
    nav_nav_xds = floor_to_sec_res(nav_nav_xds,'time') # floor the times to sec for easier joining
    

    # -- UPDATE COORDINATES based on NAV file
    datetimes = cip_xds.time.values                         
    sel_data_nav = nav_nav_xds.sel(time=datetimes, method = "nearest") # select the NAV data from times in CIP
    cip_updated_xds = cip_xds.assign_coords(sel_data_nav.coords)  # Add NAV coordinates to the CIP xarray
    
    # -- CIP variable updates and calculations
    
    # Variable renaming for easier access in analysis
    cip_updated_xds = cip_updated_xds.rename({'LWC': 'LWC_cip'}) #change name of LWC (to avoid confusion with cdp later)
    cip_updated_xds = cip_updated_xds.rename({'LATITUDE': 'lat','LONGITUDE': 'lon', 'ALTITUDE':'alt'})

    # Calculate SV
    # Sample Volume = Sample Area ('SA') * TAS * sample time (.attrs['RATE'])
    cip_updated_xds['SV_CIP'] = cip_updated_xds['SA']*cip_updated_xds['TAS']*cip_updated_xds.attrs['RATE']
    cip_updated_xds['SV_CIP'].attrs['longname']='Sample volume'
    cip_updated_xds['SV_CIP'].attrs['unit']='m3'
    cip_updated_xds['SV_CIP'].attrs['description']='Sample volume per size bin'
    cip_updated_xds['SV_CIP'].attrs['calculated from']=['SA', 'TAS', 'attrs:RATE']

    # -- Update metadata
    meta_inst = {'instrument': 'CIP' #AC
                 } 

    # Variable dependent metadata
    cip_updated_xds = var_attrs_from_list(cip_updated_xds, meta_inst )

    cip_xds.close()
    nav_nav_xds.close()
    
    return cip_updated_xds

#Old version
def standardize_cip_netcdf(cip_nc_file, nav_tdyn_file,nav_nav_file, flight):
    """ Add NAV information to CIP nc file (coordinates, meteorological parameters)

    This function relies on the packages 'xarray','numpy' and 're' for datamanagement and calculations,
    the date function from datetime for date management and the local function floor_to_sec_res from utils_func.nc.

    Parameters
    ----------
    cip_nc_file
        CIP NetCDF file from flight
    nav_file
        Navigation file from flight
    flight
        islasid of flight

    Returns
    -------
    cip_updated_xds
        xarray dataset from the CIP file updated with coordinates and meteorological parameters from the nav file
    """
    import xarray as xr # read netcdf-files
    import numpy as np
    import re #regex
    from datetime import date
    from utils.func_nc import floor_to_sec_res
    
    cip_xds = xr.open_dataset(cip_nc_file) # returns an xarray dataset
    nav_tdyn_xds = xr.open_dataset(nav_tdyn_file) # returns an xarray dataset
    nav_nav_xds = xr.open_dataset(nav_nav_file) # the nav file containing pitch, roll etc

    # fix time dimension cip_xds
    cip_xds = cip_xds.rename_vars({'elapsed_time':'time'}) # elapsed time holds the correct time to use, change name to time for simplisity
    cip_xds = cip_xds.set_coords('time') # set as coordinate 
    cip_xds = cip_xds.swap_dims({'Time': 'time'}) # set as main dimension
    cip_xds = floor_to_sec_res(cip_xds,'time') # floor the times to sec for easier joining

    # drop duplicate time steps (in nav)
    index = np.unique(nav_tdyn_xds.time, return_index = True)[1]
    nav_tdyn_xds = nav_tdyn_xds.isel(time=index)
    index = np.unique(nav_nav_xds.time, return_index = True)[1]
    nav_nav_xds = nav_nav_xds.isel(time=index)
    

    # -- UPDATE COORDINATES based on NAV file
    datetimes = cip_xds.time.values                    #transform from seconds from midnight to datetimeobject     
    
    # select the NAV data from these times (for both nav files)
    sel_data_tdyn = nav_tdyn_xds.sel(time=datetimes, method = "nearest")           # "nearest" due to diffs in decimalseconds
    sel_data_nav = nav_nav_xds.sel(time=datetimes, method = "nearest")

    # Add NAV coordinates to the CIP xarray
    cip_updated_xds = cip_xds.assign_coords(sel_data_tdyn.coords)
    
    # change name of LWC ( to avoid confusion with cdp later)
    cip_updated_xds = cip_updated_xds.rename({'LWC': 'LWC_cip'})

    # add MET variables from Nav file: Temp, Pres, WS/WD, humidity parameters
    cip_updated_xds['T'] = sel_data_tdyn['TEMP1']
    cip_updated_xds['T'].attrs['origin file']=nav_tdyn_file

    cip_updated_xds['P'] = sel_data_tdyn['PRES']
    cip_updated_xds['P'].attrs['origin file']=nav_tdyn_file

    cip_updated_xds['WS'] = sel_data_tdyn['WS']
    cip_updated_xds['WS'].attrs['origin file']=nav_tdyn_file

    cip_updated_xds['WD'] = sel_data_tdyn['WD']
    cip_updated_xds['WD'].attrs['origin file']=nav_tdyn_file

    cip_updated_xds['DP1'] = sel_data_tdyn['DP1']
    cip_updated_xds['DP1'].attrs['origin file']=nav_tdyn_file

    cip_updated_xds['HABS1'] = sel_data_tdyn['HABS1']
    cip_updated_xds['HABS1'].attrs['origin file']=nav_tdyn_file

    cip_updated_xds['RH1'] = sel_data_tdyn['RH1']
    cip_updated_xds['RH1'].attrs['origin file']=nav_tdyn_file

    cip_updated_xds['HABS1'] = sel_data_tdyn['HABS1']
    cip_updated_xds['HABS1'].attrs['origin file']=nav_tdyn_file

    cip_updated_xds['ROLL'] = sel_data_nav['ROLL']
    cip_updated_xds['ROLL'].attrs['origin file']=nav_nav_file

    cip_updated_xds['THEAD'] = sel_data_nav['THEAD']
    cip_updated_xds['THEAD'].attrs['origin file']=nav_nav_file

    cip_updated_xds['PITCH'] = sel_data_nav['PITCH']
    cip_updated_xds['PITCH'].attrs['origin file']=nav_nav_file

    # calculate the gradient of the thead:
    time = sel_data_nav.time
    time_values = (time.dt.hour*3600+time.dt.minute*60+time.dt.second).values
    dfdx_thead= np.gradient(cip_updated_xds['THEAD'], time_values, axis = 0)
    cip_updated_xds['dfdx_thead'] = (('time',), dfdx_thead)
    cip_updated_xds['dfdx_thead'].attrs['description']='Gradient of THEAD'
    cip_updated_xds['dfdx_thead'].attrs['calculated from']=['THEAD','time']
   
    # change names of lat, lon and alt
    cip_updated_xds = cip_updated_xds.rename({'LATITUDE': 'lat','LONGITUDE': 'lon', 'ALTITUDE':'alt'})

    # Calculate SV for CIP and CDP
    #calculate the sample volume (sample area SA * TAS redused * sample time

    # sample area has one value per bin, and are already given in m2: test['SA'].values
    # sample time is given as seconds in the attribute 'RATE': test.attrs['RATE']
    # TAS should be the same as the one used for the rest of the variables: test['TAS'
    cip_updated_xds['SV_CIP'] = cip_updated_xds['SA']*cip_updated_xds['TAS']*cip_updated_xds.attrs['RATE']
    cip_updated_xds['SV_CIP'].attrs['longname']='Sample volume'
    cip_updated_xds['SV_CIP'].attrs['unit']='m3'
    cip_updated_xds['SV_CIP'].attrs['description']='Sample volume per size bin'
    cip_updated_xds['SV_CIP'].attrs['calculated from']=['SA', 'TAS', 'attrs:RATE']

    # -- UPDATE METADATA

    # Global metadata - campaign specifics
    safireid = re.search('as\d+', nav_tdyn_file)
    cip_updated_xds.attrs['safireid'] = safireid.group()
    cip_updated_xds.attrs['islasid'] = flight

    # Global metadata
    #ACDD Highly recommended (4 of 3)
    cip_updated_xds.attrs['title'] = f'CIP dataset from flight {flight} of the ISLAS campaign'
    cip_updated_xds.attrs['summary'] = f'SODA2 Processed CIP data from flight {flight} from the ISLAS 2022 campain. Updated with latitude, longitude, altitude and time coordinates from the flights NAV data'
    cip_updated_xds.attrs['keywords'] = ['Earth Science > Atmosphere > Clouds > Cloud Microphysics > Cloud Liquid Water/Ice',
                                        'Earth Science > Atmosphere > Clouds > Cloud Microphysics > Cloud Droplet Concentration/Size']
    cip_updated_xds.attrs['keywords_vocabulary'] = "GCMD Science Keywords"
    cip_updated_xds.attrs['Conventions'] = ['ACDD-1.3']
    # Filenames used to create this file
    navfilename = nav_tdyn_file.split('/')[-1]
    cip_updated_xds.attrs['NAV file']=navfilename
    cipfilename = cip_nc_file.split('/')[-1]
    cip_updated_xds.attrs['SODA NC file']=cipfilename

    # Global metadata - ACDD recommended

    # Global metadata - suggested
    cip_updated_xds.attrs['date_modified'] = date.today().strftime("%Y-%m-%d")
    cip_updated_xds.attrs['date_metadata_modified'] = date.today().strftime("%Y-%m-%d")


    cip_xds.close()
    nav_tdyn_xds.close()
    nav_nav_xds.close()
    
    return cip_updated_xds