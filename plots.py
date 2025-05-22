#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 15:58:06 2024

@author: ninalar
"""
def simpleplot(time, variable, flight):
    # A simple plotting function that takes time and a variable and plots it. 
    # Time should be in datetime format, this plot only plots time on the xaxis (mdates, xformatter, gcf coding)
    
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    
    xformatter = mdates.DateFormatter('%H:%M') # define a formatter for only showing the time of a datetime object
    
    Var = variable.name
    fig, ax = plt.subplots()

    ax.plot(time, variable)
    
    plt.title(f'{Var} from flight {flight}')
    plt.ylabel(f'{Var}')
    plt.xlabel('Time')
    
    plt.gcf().axes[0].xaxis.set_major_formatter(xformatter)
    plt.show
    
    
    
def map_LWC_single(islas_nav_df,cip_nc_df,flight):
    # plot CIP LWC/IWC on map for single fligth
    print(f'Plotting LWC on map for flight: {flight}')
    #NB need extra stuff for using plotly in spyder. check for this later
    # --- Packages ----
    import plotly.express as px
    import pandas as pd 
     
    # select only the data relating to the given flight
    cip_df = cip_nc_df[cip_nc_df['flightid']==flight]
    nav_df = islas_nav_df[islas_nav_df['flightid']==flight]
    
    # adding NAV information to the cdp data by merging on nearest UTC Seconds. 
    cip_nav_df = pd.merge_asof(cip_df, nav_df, on = 'time', direction = 'nearest')
    
    # --- Plotly map ----
    fig = px.scatter_mapbox(cip_nav_df,
                           lon= cip_nav_df['Longitude (degree)'],
                           lat = cip_nav_df['Latitude (degree)'],
                            center=dict(lat=cip_nav_df['Latitude (degree)'].mean(),lon=cip_nav_df['Longitude (degree)'].mean()),
                           zoom = 4,
                           color = cip_nav_df['LWC %'],
                            size = cip_nav_df['TWC (gram/m3)'],
                           width = 900,
                           height = 600,
                           title = f'Flight {flight}: CIP TWC along flight track'
                           )
    fig2 = px.line_mapbox(nav_df, lon= nav_df['Longitude (degree)'],
                           lat = nav_df['Latitude (degree)'], zoom=8)
    fig.add_trace(fig2.data[0])
    fig.update_layout(mapbox_style='open-street-map')
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":10})
    #save image as interactive html
    fig.write_html(f"LWC_CIP_onMap_{flight}.html")
    
def numbconc_hist_all(cdp_bulk_df,cip_bulk_df, cdp_bins_df, cip_bins_df):
    import matplotlib.pyplot as plt
    import pandas as pd
    import numb_conc #function to prepare numb con for making histogram
    
    # --- Create histograms from the number concetrations from CIP and CDP for all the flights
    print('Plotting histogram over number concentration for CIP and CDP')
    # --initialize faceting
    group_values = list(cdp_bulk_df['flightid'].unique()) #group on flightid
    # set number of columns in the plot
    ncols=3
    #calculate number of rows in the plot
    nrows = len(group_values) // ncols + (len(group_values) % ncols > 0)

    # -- define the plot
    plt.figure(figsize = (9,9))
    plt.subplots_adjust(hspace=0.5, wspace=0.5)
    plt.suptitle('ISLAS: CDP and CIP mean counts per bin', fontsize = 16, y=0.95)

    # go through each flight
    for n, col in enumerate(group_values):
        # add a new subplot at each iteration using nrows and cols
        ax = plt.subplot(nrows, ncols, n + 1)
        
        # Filter the cdp and cip dataframes for each flight
        #cdp_df = cdp_bulk_df.query("Flightid == @col")
        cdp_df = cdp_bulk_df[cdp_bulk_df["flightid"]==col]
        cip_df = cip_bulk_df[cip_bulk_df["flightid"]==col]
        
        # prepare the cip and cdp data for number concentration plotting
        cdp_numb_conc, cip_numb_conc = numb_conc.hist_numb_conc(cdp_df, cdp_bins_df, cip_df, cip_bins_df)
        
        # ignore bins with end points lower than 125 (midpoint lower than 100) 
        #cip_numb_conc_mean =  cip_numb_conc_mean[cip_numb_conc_mean['Bin midpoints (microns):'] >= 100]
        cdp_numb_conc_mean = pd.DataFrame(cdp_numb_conc.mean(), columns = ['count'])
        cip_numb_conc_mean = pd.DataFrame(cip_numb_conc.mean(), columns = ['count'])
        
        # plot the CDP and CIP values 
        ax.hist(cdp_numb_conc_mean['Size (microns)'], weights = cdp_numb_conc_mean['count_norm'], bins=cdp_numb_conc_mean['Size (microns)'], label = "CDP", histtype='step')
        ax.hist(cip_numb_conc_mean['Bin midpoints (microns):'], weights = cip_numb_conc_mean['count_norm'], bins=cip_numb_conc_mean['Bin midpoints (microns):'], label = "CIP", histtype='step')
        
        # chart formatting and anotations
        plt.yscale('log')
        plt.xscale('log')

        ax.set_ylabel('dN/dlogDp (#/m4)')
        ax.set_xlabel('Dp ($\mu$m)')
        ax.set_title(col)
        ax.legend()
        
    plt.savefig('ISLAS_particlecountAllBins.png')
    
    
def lwc_cip_cdp_plot(cdp_bulk_df,cip_nc_df):
    # plot the LWC from the CDP together with the LWC and the IWC from the CIP. 
    # 
    import matplotlib.pyplot as plt
    
    print('Plotting LWC and IWC for CIP and CDP')
    # --initialize faceting
    group_values = list(cdp_bulk_df['flightid'].unique()) #group on flightid
    # set number of columns in the plot
    ncols=3
    #calculate number of rows in the plot
    nrows = len(group_values) // ncols + (len(group_values) % ncols > 0)

    # liquid water content plot
    # -- define the plot
    plt.figure(figsize = (9,9))
    plt.subplots_adjust(hspace=0.5, wspace=0.5)
    plt.suptitle('ISLAS: LWC and IWC from CDP and CIP', fontsize = 16, y=0.95)

    # go through each flight
    for n, col in enumerate(group_values):
        # add a new subplot at each iteration using nrows and cols
        ax = plt.subplot(nrows, ncols, n + 1)
        
        # Filter the cdp and cip dataframes for each flight
        cdp_df = cdp_bulk_df[cdp_bulk_df["flightid"]==col]
        cip_df = cip_nc_df[cip_nc_df["flightid"]==col]
       
        # plot the CIP LWC and IWC
        ax.plot(cip_df.index,cip_df['LWC (gram/m3)'], label = 'CIP LWC')
        ax.plot(cip_df.index,cip_df['IWC (gram/m3)'], label = 'CIP IWC')
        ax.plot(cdp_df['UTC Seconds'],cdp_df['LWC corr (g/m^3)'], label = 'CDP LWC')
        
        ax.set_ylabel('gram/m3')
        ax.set_xlabel('Sec since midnight')
        ax.set_title(col)
        ax.legend()
        
    plt.savefig('ISLAS_LWC_IWC.png')
    
#------ Figure management functions -----
def letter_annotation(ax, xoffset, yoffset, letter, size=12):
    # function to add letter/text formatted in a specific way
    # works within nested subfigure
        ax.text(xoffset, yoffset, letter, transform=ax.transAxes,size=size, weight='bold')
        
        
# Plotting lat and lon on map
def plot_map(nav_df, c_flights, flight = "", file_str = ""):
    # Function to create a map showing the flight paths. Uses set colors and area to plot in. 
    # INPUT arguments:
    #   nav_df: dataframe that contains at least the two columns: 'Longitude (degree)' and 'Latitude (degree)'
    # OPTIONAL INPUT arguments:
    #   flight: name of single flight to plot. If no flight is added, all flights are plotted.
    #   file_str: name of file to print plot to. If no file string is added, the plot is not saved.
    # Additional information:
    #   Uses global variable: c_flights

    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    #-- Map initialization based on flight info --

    # Find the max and min lat and lon in the dataset
    inc = 1
    lat_max = nav_df['Latitude (degree)'].max() + inc
    lat_min = nav_df['Latitude (degree)'].min() - inc
    lon_max = nav_df['Longitude (degree)'].max() + inc
    lon_min = nav_df['Longitude (degree)'].min() - inc
    
    # coordinates of Andøya
    #lat_and = 69.3073
    #lon_and = 16.1312
    
    # coordinates of Kiruna
    lat_kir = 67.8256
    lon_kir = 20.3351

    # --- Set up figure
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.NorthPolarStereo())
    
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linewidth=2)
    data_projection = ccrs.PlateCarree()
    
    if flight == "":
        # plot all the flights from ISLAS if "flight" is empty
        for flight in nav_df['flightid'].unique().sort_values():
            sel_df = nav_df[nav_df['flightid']==flight] # filtrate on flight
            date = sel_df.index[0].date() # get the date of the flight
            ax.plot(sel_df['Longitude (degree)'], sel_df['Latitude (degree)'],
                label = f'{flight} ({date})', c =c_flights[flight], transform = data_projection)
    else:
        # Plot only the given flight if "flight" contains a flightid
        try:
            sel_df = nav_df[nav_df['flightid']==flight] # filtrate on flight
            date = sel_df.index[0].date() # get the date of the flight
            ax.plot(sel_df['Longitude (degree)'], sel_df['Latitude (degree)'],
                    label = f'{flight} ({date})', c =c_flights[flight], transform = data_projection)
        except ValueError:
            print(f'Flightid: {flight} is not a valid flightid. Needs to be in the format "IS22-XX" where X is a number between 02 and 11')
     
    
    #Plot Andøya on map
    #ax.plot(lon_and, lat_and, marker='o', color='tab:red', transform=data_projection)
    #ax.annotate('Andøya', (lon_and, lat_and))
    
    #Plot Kiruna on map
    ax.plot(lon_kir, lat_kir, marker='o', color='tab:red', transform=data_projection)
    #Add text "Kiruna" at the plotted point
    offset_lon = 0.7  # adjust the horizontal offset
    offset_lat = -0.7  # adjust the vertical offset
    ax.text(lon_kir + offset_lon, lat_kir + offset_lat, "Kiruna", transform=data_projection, ha='right', va='bottom')
    
    
    # --- Drawing a dashed box
    #lons = [16, 22, 22, 16, 16]
    #lats = [74, 74, 76, 76, 74]
    #ax.plot(lons, lats, linestyle='--', color='black', transform=ccrs.PlateCarree())
    # ---
    
    ax.set_extent([lon_min, lon_max, lat_min, lat_max])
    plt.legend(loc='best')
    
    # save figure if filestring is given
    if file_str !="":
        plt.savefig(file_str) 

def plot_lat_bands1(lat_bands, ds, title, savefile = ''):
    # Function to plot latitude bands used for further analysis
    # Input: 
    # --- lat_bands: array of the the latitudes used for separation, should include at least min and max latitude
    # --- ds: full original dataset for plotting flightpaths
    # --- title: title to add to plot
    # --- savefile(optional): path and filename to save plot into

    # functions
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec # gridspec for nested subfigures

    # coordinates of Kiruna
    lat_kir = 67.8256
    lon_kir = 20.3351
    
    # --- Set up figure
    fig = plt.figure(figsize=(15, 6))
    gs = GridSpec(1, 2, figure=fig)
    ax = fig.add_subplot(gs[0,0], projection=ccrs.NorthPolarStereo())

    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linewidth=2)
    data_projection = ccrs.PlateCarree()

    # get datavalues for plotting
    lat_values = ds['lat'].values
    lon_values = ds['lon'].values
    incloud_values = ds['in_cloud'].values 

    # select out just where incloud is set to true
    sel_mask = (ds['in_cloud'] == True).compute()
    sel_ds = ds.where(sel_mask, drop=True)
    sel_lat_values = sel_ds['lat'].values
    sel_lon_values = sel_ds['lon'].values

    #ax.scatter(lon_values, lat_values, marker='.',c=incloud_values, transform = data_projection)
    ax.scatter(lon_values, lat_values, marker='.',c='darkgrey', label='Flight path', transform = data_projection)
    ax.scatter(sel_lon_values, sel_lat_values, marker='o',c='navy', label='In cloud', transform = data_projection)

    # Draw latitude bands
    for lat_band in lat_bands:
        ax.plot(range(0, 51, 5), [lat_band]*11, color='k', transform=ccrs.PlateCarree())
        if lat_band in [lat_min, lat_max]:
            lat_text = round(lat_band, 2)
        else:
            lat_text = lat_band
        ax.text(28, lat_band-0.7, f"{lat_text:.2f}°", transform=ccrs.PlateCarree(), ha='center', va='bottom', fontsize=15, color='blue',
            bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))

    #Plot Kiruna 
    ax.plot(lon_kir, lat_kir, marker='o', color='tab:red', transform=data_projection)
    offset_lon = 0.7  # adjust the horizontal offset
    offset_lat = -0.7  # adjust the vertical offset
    ax.text(lon_kir + offset_lon, lat_kir + offset_lat, "Kiruna", transform=data_projection, ha='right', va='bottom')

    # set extent of the plot to the full area covered by the dataset +/- an increment of 1
    ax.set_extent([ds.lon.values.min()-1, ds.lon.values.max()+1, ds.lat.values.min()-1, ds.lat.values.max()+1])
    
    ax.set_title(f'Latitude bands: {title}')

    plt.legend()
    
    if savefile !='':
        plt.savefig(savefile)
        
def lat_3band_select(lat_bands, ds):
    # Function to extract information about the content of the latitude bands
    # Input: 
    # --- lat_bands: array of the the latitudes used for separation, should include min, max and two other latitudes
    # --- ds: dataset to do the summarization on, that includes 'lat'

    lat_min, lat_b1, lat_b2, lat_max = lat_bands # unpack lat selection
    
    # count number of values between different latitudes and add do dictionary
    lat_values = ds['lat']  # Access the latitude coordinate
    count_dict = {'count_low': ((lat_values >= lat_min) & (lat_values <= lat_b1)).sum().item(),
                  'count_mid': ((lat_values >= lat_b1) & (lat_values <= lat_b2)).sum().item(),
                  'count_high': ((lat_values >= lat_b2) & (lat_values <= lat_max)).sum().item(),
                 'lat_bands': lat_bands}

    #print(f'count_low: {count_dict['count_low']},count_mid: {count_dict['count_mid']},count_high: {count_dict['count_high']}')

    # Compute the boolean masks for latitude conditions
    lat_mask_high = (ds['lat'] < lat_max) & (ds['lat'] >= lat_b2)
    lat_mask_mid = (ds['lat'] < lat_b2) & (ds['lat'] >= lat_b1)
    lat_mask_low = (ds['lat'] < lat_b1) & (ds['lat'] >= lat_min)

    # Filter the dataset on masks
    ds_filtered_high = ds.where(lat_mask_high, drop=True)
    ds_filtered_mid = ds.where(lat_mask_mid, drop=True)
    ds_filtered_low = ds.where(lat_mask_low, drop=True)

    print(f'number of values in 3 bands defined by {lat_bands}:')
    print(f'count_low: {len(ds_filtered_low.lat)},count_mid: {len(ds_filtered_mid.lat)},count_high: {len(ds_filtered_high.lat)}')
    
    return ds_filtered_high, ds_filtered_low, ds_filtered_mid, count_dict
def lat_2band_select(lat_bands, ds):
    # Function to extract information about the content of the latitude bands
    # Input: 
    # --- lat_bands: array of the the latitudes used for separation, should include min, max and one other latitude
    # --- masks: masks to use to select data

    lat_min, lat_mid, lat_max = lat_bands # unpack lat selection
    
    # count number of values between different latitudes and add to dictionary
    lat_values = ds['lat']  # Access the latitude coordinate
    count_dict = {'count_south': ((lat_values >= lat_min) & (lat_values <= lat_mid)).sum().item(),
                  'count_north': ((lat_values >= lat_mid) & (lat_values <= lat_max)).sum().item(),
                 'lat_bands': lat_bands}

    # Compute the boolean masks for latitude conditions
    lat_mask_north = (ds['lat'] < lat_max) & (ds['lat'] >= lat_mid)
    lat_mask_south = (ds['lat'] < lat_mid) & (ds['lat'] >= lat_min)

    # Filter the dataset on masks
    ds_filtered_north = ds.where(lat_mask_north, drop=True)
    ds_filtered_south = ds.where(lat_mask_south, drop=True)

    print(f'number of values in 2 bands defined by {lat_bands}:')
    print(f'count_south: {len(ds_filtered_south.lat)},count_north: {len(ds_filtered_north.lat)}')
    
    #return ds_filtered_north, ds_filtered_south, count_dict
    return lat_mask_north, lat_mask_south, count_dict