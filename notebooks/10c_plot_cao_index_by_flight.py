# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.2
#   kernelspec:
#     display_name: mc2-icepacks
#     language: python
#     name: python3
# ---

# %%
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.path as mpath
import matplotlib.gridspec as gridspec
from matplotlib import dates
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.patches import Polygon
from matplotlib.colors import LogNorm
import matplotlib.colors as colors
import matplotlib as mpl
from mpl_toolkits.axes_grid1 import make_axes_locatable

from cmcrameri import cm as cm_crameri

import netCDF4
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature

import glob
import datetime

import pandas as pd

from basepath import data_path_base
import sys

import scipy
import metpy
from metpy.units import units

import seaborn as sns

import cartopy.io.img_tiles as cimgt



###################################################################################
def get_sic_data(year, month, day):
    print('get sea ice for: ', year, month, day)
    sic_file = 'output_files/sea_ice/asi-n6250-'+str(year).zfill(4)+str(month).zfill(2)+str(day).zfill(2)+'-5.4_regridded.nc'

    ds = xr.open_dataset(sic_file)
    ds = ds.rename({'__xarray_dataarray_variable__': 'sic'})
    ds = ds.where(ds.lat >= 72., drop = True)
    ds.coords['lon'] = (ds.coords['lon'] + 180) % 360 - 180
    return(ds)

def find_closest_datetime(datetime_list, reference_datetime):

    closest_dt = min(datetime_list, key=lambda dt: abs(dt - reference_datetime))
    return(closest_dt)



# %%
flights = ['IS22-02', 'IS22-03', 'IS22-04', 'IS22-05', 'IS22-06', 'IS22-07', 'IS22-08', 'IS22-10', 'IS22-11']
dates = ['2022-03-22', '2022-03-24', '2022-03-24', '2022-03-26', '2022-03-26', '2022-03-29', '2022-03-30', '2022-04-03', '2022-04-03']

for flight, date in zip(flights, dates):

    print(flight, date)

    # read flight track with MCAO index
    ds_atr = xr.open_dataset('output_files/flight_tracks_with_mcao/'+date+'_'+flight+'_mcao_track.nc')

    # get era5 timecode
    dt_start = np.nanmin(ds_atr.time)
    ds_sst  = xr.open_mfdataset([data_path_base+'data/ERA5/3_hourly/2022/sst_3hourly_ERA5_202203_subarea-islas22_sl.nc',
                            data_path_base+'data/ERA5/3_hourly/2022/sst_3hourly_ERA5_202204_subarea-islas22_sl.nc'])
    era5_time = ds_sst.sel(valid_time = dt_start, method = 'nearest')['valid_time'].values
    
    # read MCAO index maps for flight day (closest to takeoff time)
    ds_mcao = xr.open_dataset('output_files/cao_maps/'+date+'_'+flight+'_mcao_map.nc')
    
    # read sea ice concentration for flight day
    ds_sic = get_sic_data(int(date[0:4]), int(date[5:7]), int(date[8:10]))

    fig = plt.figure(figsize = (8, 5), layout = 'constrained')
    ax_map = fig.add_subplot(1, 1, 1, projection=ccrs.LambertConformal(central_longitude = 20, standard_parallels = (60,70)))
    
    ax_map.set_extent([0, 30, 66, 80], crs=ccrs.PlateCarree()) # Set the global extent

    ax_map.coastlines(alpha=0.5)
    gl = ax_map.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, alpha = 0.25, crs = ccrs.PlateCarree())
    gl.bottom_labels = False
    gl.xlabel_style = {'color': 'white'}

    ax_map.add_feature(cfeature.BORDERS, linewidth=0.5, edgecolor='k', alpha = 0.4)

    ax_map.set_xlabel("Longitude [°E]")
    ax_map.set_ylabel("Latitude [°N]")
    
    props = dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor = "dimgrey")
    plt.suptitle(date+': '+flight, y = 0.94, bbox = props, color = 'dimgrey')
    

    xlim = [0, 30]
    ylim = [67, 80]

    rect = mpath.Path([[xlim[0], ylim[0]],
                    [xlim[1], ylim[0]],
                    [xlim[1], ylim[1]],
                    [xlim[0], ylim[1]],
                    [xlim[0], ylim[0]],
                    ]).interpolated(190)

    proj_to_data = ccrs.PlateCarree()._as_mpl_transform(ax_map) - ax_map.transData
    rect_in_target = proj_to_data.transform_path(rect)

    ax_map.set_boundary(rect_in_target)

    #################
    # plot sea ice concentration
    cs = ax_map.contour(ds_sic.lon, ds_sic.lat, ds_sic.sic, transform = ccrs.PlateCarree(), levels = [15.], linewidths = 3, colors = 'k', zorder = 20)


    #################
    # plot MCAO index map from ERA5
    cmap = cm_crameri.lapaz
    cmaplist = [cmap(i) for i in range(cmap.N)]
    cmaplist[0] = (.92, .92, .92, 1.0)                     # force the first color entry to be grey
    cmap = mpl.colors.LinearSegmentedColormap.from_list(
        'Custom cmap', cmaplist, cmap.N)
    bounds = np.linspace(-2, 10, 7)
    bounds = [-1, 0, 2, 4, 6, 8, 10, 12, 14, 16]
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

    cs_mcao = ax_map.pcolormesh(ds_mcao.lon, ds_mcao.lat, ds_mcao.mcao.T, cmap=cmap, norm = norm, transform=ccrs.PlateCarree())
    cbar_ax = fig.add_axes([0.02, 0.1, 0.3, 0.03]) 
    cbar_mcao = plt.colorbar(cs_mcao, cax = cbar_ax, orientation = 'horizontal')
    cbar_mcao.set_ticks([-1, 0, 4, 8, 12, 16])
    cbar_mcao.set_ticklabels(np.append([''], [f'{i} K' for i in [0, 4, 8, 12, 16]]), c = 'dimgrey')
    cbar_mcao.set_label('MCAO index', c = 'dimgrey', fontweight = 'bold')
    cbar_mcao.ax.xaxis.set_label_coords(1.23, 0.9)
    # Set the number of ticks
    #cbar.locator_params(nbins=5)

    # add ERA5 time
    ax_map.text(5., 80.2, 'ERA5: '+np.datetime_as_string(era5_time, unit='s'), fontsize = 6, c = 'dimgrey', transform = ccrs.PlateCarree())

    #################
    # add Kiruna
    krn_lon = 20.3346
    krn_lat = 67.8207
    ax_map.scatter(krn_lon, krn_lat, c='cyan', marker='^', s=50, label = 'Kiruna', zorder = 35, ec = 'k', linewidth = 0.5, transform = ccrs.PlateCarree())
    props = dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor = 'dimgrey')
    ax_map.text(krn_lon+1.25,krn_lat-0.2, 'Kiruna', fontsize = 7, c = 'k', bbox = props, transform = ccrs.PlateCarree())

    #################
    # add ATR track
    ax_map.plot(ds_atr.lon, ds_atr.lat, transform = ccrs.PlateCarree(), linewidth = 2.0, c = '#FF6B6B', alpha = 0.8, zorder = 30)              

    #################
    # add MCAO histogram along flight track
    divider = make_axes_locatable(ax_map)
    ax_plot = divider.new_horizontal(size="100%", pad=1.4, axes_class=plt.Axes)
    fig.add_axes(ax_plot)


    if np.nanmin(ds_atr.mcao.values) < 0:
        lowest_bin = np.nanmin(ds_atr.mcao.values)
    else:
        lowest_bin = -10
        
    neg_bins = np.array([lowest_bin, 0])
    bins = np.arange(0, 17, 2)

    hist_neg, edges_neg = np.histogram(ds_atr.mcao, neg_bins)
    hist_mcao, edges_mcao = np.histogram(ds_atr.mcao, bins)
    
    freq_neg = hist_neg/float(hist_neg.sum() + hist_mcao.sum())
    freq_mcao = hist_mcao/float(hist_neg.sum() + hist_mcao.sum())
    print(freq_neg.sum()+freq_mcao.sum())

    ax_plot.bar(-2, 100.*freq_neg, width=1, align="center", ec="k", color = 'grey')
    ax_plot.bar(bins[:-1], 100.*freq_mcao, width=2, align="edge", ec="k", color = '#006666', alpha = 0.7)
    
    bottom, top = plt.ylim()    # get y axis limits for text

    ax_plot.set_xticks(np.append([-2], bins), labels=np.append(['< 0'], [f'{i}' for i in [0, 2, 4, 6, 8, 10, 12, 14, 16]]))
    ax_plot.set_xlabel('MCAO index (K)')
    ax_plot.set_ylabel('Frequency (%)')
    ax_plot.text(1, top+6, r'Median: ' + r"$\bf{"+str(np.round(np.nanmedian(ds_atr.mcao.values[ds_atr.mcao > 0.]), 2)) + "}$" + ' K ', fontsize = 8, family = 'monospace')
    ax_plot.text(8.5, top+6, r'Max: ' + str(np.round(np.nanmax(ds_atr.mcao.values), 2)) + ' K', fontsize = 8, family = 'monospace')
    

    # Classification following Papritz and Spengler (2017)
    # weak (M < 4 K), moderate (4K < M < 8 K), strong (8 K < M < 12 K) and very strong (M > 12 K)
    ax_plot.plot([0, 0], [0, 100], linestyle = ':', linewidth = 0.8, c = 'dimgrey')
    ax_plot.plot([4, 4], [0, 100], linestyle = ':', linewidth = 0.8, c = 'dimgrey')
    ax_plot.plot([8, 8], [0, 100], linestyle = ':', linewidth = 0.8, c = 'dimgrey')
    ax_plot.plot([12, 12], [0, 100], linestyle = ':', linewidth = 0.8, c = 'dimgrey')
    ax_plot.text(1, top+2, 'weak', c = 'dimgrey', fontsize = 8, family = 'monospace')
    ax_plot.text(4.3, top+2, 'moderate', c = 'dimgrey', fontsize = 8, family = 'monospace')
    ax_plot.text(8.7, top+2, 'strong', c = 'dimgrey', fontsize = 8, family = 'monospace')
    ax_plot.text(12.3, top+2, 'very strong', c = 'dimgrey', fontsize = 8, family = 'monospace')

    ax_plot.set_ylim(0, top+5)
    sns.despine(ax = ax_plot)

    plt.savefig('figures/mcao_flights/'+date+'_'+flight+'_mcao.png', dpi = 300, bbox_inches = 'tight')

    plt.show()    
    
        


# %%

# %%
