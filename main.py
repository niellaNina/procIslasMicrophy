#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 28 11:17:28 2024

@author: ninalar
"""
# imports from packages
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# imports from files
import functions
import read_cdp
import read_cip_txt
import read_lwc
import read_nav
import read_cip_nc
import plots
import numb_conc
import in_cloud_detect


# --- Data import
nav_df, nav_stats_dict = read_nav.read_nav()
cdp_bulk_df, cdp_bins_df, cdp_var_df, cdp_meta_df = read_cdp.read_cdp(nav_df)                                            # CDP: data and bin information
cip_binneddata_df, cip_bins_df, cip_var_df, cip_proc_dict = read_cip_txt.read_cip_txt()   # CIP:  conc per bin, from txt file
cip_bulk_calc_df, cip_conc_df, cip_varnc_df = read_cip_nc.read_cip_nc()    # CIP calculated bulk information                                                                 #       variable information, processing information
#lwc_bulk_df, lwc_meta_df, lwc_chan_dict = read_lwc.read_lwc()                                                                                     

# ---- Plots for slingle flights
flight='as220014' #flight filter

#test = in_cloud_detect.all_detect(cip_bulk_calc_df,'MVD (um)')
test = in_cloud_detect.single_detect(cip_bulk_calc_df,'LWC (gram/m3)', flight)
#map_plot = plots.map_LWC_single(nav_df,cip_bulk_calc_df,flight) #plot the LWC from CIP on the flight path (interactive html)

# Get a single cloud from the flight
# for now (with flight as220014) use times found by viewing plots
# Todo: get cloud based on algoritm

# guess on edges of cloud: 1400-2100

# first filter on flight
cip_flight_df = cip_binneddata_df[cip_binneddata_df['flightid']==flight]
nav_flight_df = nav_df[nav_df['flightid']==flight]

# then filter on just the concentration in bins:
filter_col = [col for col in cip_flight_df if col.startswith(('Conc','UTC'))]
cip_numb_conc = cip_flight_df[filter_col]

# then filter on time
# TODO: build algoritm to set this!
cloud_cip_numconc_df = cip_numb_conc[cip_numb_conc['UTC Seconds'].between(32500, 36000)]
cloud_nav_df = nav_flight_df[nav_flight_df['UTC Seconds'].between(32500, 36000)]

# set UTC Seconds as index
cloud_cip_numconc_df = cloud_cip_numconc_df.set_index('UTC Seconds')
# These data are in 1 sec timesteps. create a rolling mean for the dataframe
t_step = 2 # set the timestep to mean over (start with 2 and experiment)

c_cip_nc_rolling_df = cloud_cip_numconc_df.rolling(2).mean()

#----------------------------------------
# rolling mean on pandas to mean over given set of values:
#df = df.rolling(2).mean() 
#df = df.iloc[::2, :]
#----------------------------------------

#filter on flight
test_df = cip_bulk_calc_df[cip_bulk_calc_df['flightid']==flight]
testplot = plots.simpleplot(test_df['time'], test_df['MVD (um)'], flight)
'''
fig, ax = plt.subplots()

ax.plot(cloud_nav_df['UTC Seconds'], cloud_nav_df['Altitude (meter)'])

plt.show
'''
# ------------------------Testing




'''
# the heatmapstyle plot tests
# plot information from chatgpt
plt.imshow(c_cip_nc_rolling_df.T, cmap='hot', aspect='auto', interpolation='none')

# Set the x-axis and y-axis tick labels
#plt.xticks(np.arange(len(c_cip_nc_rolling_df.columns)), c_cip_nc_rolling_df.columns)
#plt.yticks(np.arange(len(c_cip_nc_rolling_df.index)), c_cip_nc_rolling_df.index)

# Set the colorbar
plt.colorbar(label='Value')

# Add labels to the x-axis and y-axis
plt.xlabel('Seconds')
plt.ylabel('Bin Number')
plt.yscale('log')

# Display the plot
plt.show()
''' # end of heatstyle plot testing

'''

# ---- Plots for multiple/all flights
#numb_conc_hist = plots.numbconc_hist_all(cdp_bulk_df,cip_binneddata_df, cdp_bins_df, cip_bins_df)
#lwc_plot = plots.lwc_cip_cdp_plot(cdp_bulk_df,cip_bulk_calc_df)


# filter value in cloud
ic_lwc_filter = 0.1 #LWC to designate "in cloud"


plt.figure()
ax = plt.subplot()

# plot the CIP LWC and IWC
ax.plot(test_df['UTC Seconds'],test_df['LWC (gram/m3)'], label = 'CIP LWC')

ax.set_ylabel('gram/m3')

ax.set_xlabel('Sec since midnight')
ax.set_title('test')
ax.legend()
# filter on in cloud
test_df = test_df[test_df['LWC (gram/m3)']>ic_lwc_filter]
plt.figure()
ax2 = plt.subplot()

# plot the CIP LWC and IWC
ax2.plot(test_df.index,test_df['LWC (gram/m3)'], label = 'CIP LWC')

ax2.set_ylabel('gram/m3')

ax2.set_xlabel('Sec since midnight')
ax2.set_title('test2')
ax2.legend()
'''