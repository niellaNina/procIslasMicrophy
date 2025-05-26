#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  8 13:13:30 2025

@author: ninalar
"""

# ---Packages---
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import cartopy.crs as ccrs
import cartopy.feature as cfeature


import notebooks.read_nav as read_nav


def read_seaice(df, campaign_coord_limits, plot_all=False):
   
      
    
    # Get sea ice information for each flight
    islas_sic_df = []  # empty list for appending all data to one structure
    print('----Reading sea-ice files')
    for flight in df['flightid'].unique():
    
        # Information from single flight
        flight_ds = df[df.flightid==flight] # dataset only from flight
        timestamp = pd.Timestamp(flight_ds.time.iloc[0]) # get date from first line of flight_ds
        date = timestamp.strftime('%Y%m%d')
        
        # get lat and lon from the flight as numpy arrays
        lat = np.array(flight_ds['Latitude (degree)'])
        lon = np.array(flight_ds['Longitude (degree)'])
        
        print(f'Flight: {flight}, date: {date}')
        
        # --- Data from satellite: sea ice concentration
    
        sic_ds = xr.open_dataset('sea_ice_satellite/asi-n6250-' + date + '-5.4_regridded.nc')
        sic_ds.close()
    
        # rename data variable and update attributes
        sic_ds['sic'] = sic_ds['__xarray_dataarray_variable__'].assign_attrs(units="Percent", description="Sea Ice Concentration")
        sic_ds = sic_ds.drop_vars(['__xarray_dataarray_variable__'])
    
        # limit data-area to campaign area:
        islas_sic_ds = sic_ds.sel(lat=slice(int(campaign_coord_limits['lat_min']),
                                        int(campaign_coord_limits['lat_max'])),
                    lon=slice(int(campaign_coord_limits['lon_min']),
                              int(campaign_coord_limits['lon_max'])))
        # --- Get the sea ice concentration value from a specific lat and lon
        # create as own dataarrays with new dimention z
        lats = xr.DataArray(lat, dims = 'z')
        lons = xr.DataArray(lon, dims = 'z')
    
        # get nearest sic value to the lat-lon combos
        data = islas_sic_ds.sel(lat=lats, lon=lons, method='nearest')
        
        # Create a pandas dataframe with: Flight, lat, lon and sic to add to microphy_df
        sic_df = pd.DataFrame({'time': flight_ds['time'],'Latitude (degree)': lat, 'Longitude (degree)': lon, 'Sea Ice Conc. (Percent)': data.sic.values})
        sic_df['flightid']=flight
        
        islas_sic_df.append(sic_df) # append list with the new dataframe
        
        # Plot if plot_all=True
        if plot_all:
            # --- Plot interesting part of sea ice concentration
            # the area I am looking at are: 
            
            lon_min = int(campaign_coord_limits['lon_min'])
            lon_max = int(campaign_coord_limits['lon_max'])
            lat_min = int(campaign_coord_limits['lat_min'])
            lat_max = int(campaign_coord_limits['lat_max'])
            
            plt.figure(figsize=(10,5))
            ax = plt.axes(projection=ccrs.PlateCarree())
            ax.coastlines()
            
            # fixing longitude and latitude
            ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())  # Longitude and latitude
            ax.set_xticks(range(lon_min, lon_max, 5))
            ax.set_yticks(range(lat_min, lat_max, 2))
            sic = sic_ds['sic'].plot(ax=ax, cmap='Blues_r')
            cs = ax.contour(sic_ds['lon'], sic_ds['lat'], sic_ds['sic'], transform = ccrs.PlateCarree(),levels = [15.], colors = 'greenyellow')
            fl = ax.plot(flight_ds['Longitude (degree)'], flight_ds['Latitude (degree)'], transform = ccrs.PlateCarree(), c='r', label='Flight path')
            
            # Adding manual legend entry for contour
            contour_legend = mlines.Line2D([], [], color='greenyellow', label='15% Sea Ice \n concentration')
            ax.add_artist(ax.legend(handles=[contour_legend, fl[0]], loc='lower left'))
            ax.set_title(f'Sea Ice Concentration from {date} and flight path of flight {flight}')
            
            plt.savefig(f'sea_ice_conc_flight{flight}.png')
        
    islas_sic_df = pd.concat(islas_sic_df)
    
    return islas_sic_df