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
def letter_annotation(ax, xoffset, yoffset, letter):
    # function to add letter/text formatted in a specific way
    # works within nested subfigure
        ax.text(xoffset, yoffset, letter, transform=ax.transAxes,size=12, weight='bold')
        
        
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