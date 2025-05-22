#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  6 11:30:33 2025

@author: ninalar
"""

# Alternative latitude band calculation
# saving if needed for lated. not associated with specific functions, plots or code

#----------------------------------------------------
# Investigating different latitude bands: set values for change between bands: 72 and 75

# Define latitudes to set as boundaries
# Here: max, min and the set values of 72 and 75
lat_min = ds_incloud.lat.values.min()
lat_max = ds_incloud.lat.values.max()
# separation points for making latitude bands
lat_b1 = 72
lat_b2 = 75

# set lat-bands to compute between (as an array)
lat_bands = [lat_min, lat_b1, lat_b2, lat_max]

# calculate the number of datapoints per latitude band
ds_set_val_high, ds_set_val_low, ds_set_val_mid, set_val_count_dict = lat_3band_select(lat_bands, ds_incloud)

# plot this variant of latitude bands:
plot_lat_bands(lat_bands, ds, 'set lat values: 75,72')

# -----------------------------------------------------

# Investigating different latitude bands: equal latitude-distance between the band edges

# Define latitudes to set as boundaries
# Here: max, min and the set values of 72 and 75
lat_min = ds_incloud.lat.values.min()
lat_max = ds_incloud.lat.values.max()
# separation points: 3 equally large bands
diff = lat_max - lat_min
lat_diff = diff/3

lat_b1 = lat_min + lat_diff
lat_b2 = lat_max - lat_diff

# set lat-bands to compute between (as an array)
lat_bands = [lat_min, lat_b1, lat_b2, lat_max]

# calculate the number of datapoints per latitude band
ds_eq_dist_high, ds_eq_dist_low, ds_eq_dist_mid, eq_dist_count_dict = lat_3band_select(lat_bands, ds_incloud)

# plot this variant of latitude bands:
plot_lat_bands(lat_bands, ds, 'equal lat distance')

#------------------------------------------------------

# Investigating different latitude bands: latitude distance based on spread of values (get equal number of values within bands)

# Get the latitude values as an array and sort Sort the DataArray based on latitude values
sorted_lat = np.sort(ds_incloud.lat.values)

# Calculate the indices for splitting into three equal parts
num_per_set = len(sorted_lat) // 3

split_index1 = num_per_set
split_index2 = 2 * num_per_set

# Find the latitude values that define the boundaries
lat_b1 = sorted_lat[split_index1].item()

# If num_points is not divisible by number of bands, add extra points to the middle band
if len(sorted_lat) % 3 != 0:
    lat_b2 = sorted_lat[split_index2 - 1 + len(sorted_lat) % 3].item()
else:
    lat_b2 = sorted_lat[split_index2].item()

lat_max = ds_incloud.lat.values.max()
lat_min = ds_incloud.lat.values.min()

lat_bands = [lat_min, lat_b1, lat_b2, lat_max]

# calculate the number of datapoints per latitude band
ds_eq_obs_high, ds_eq_obs_low, ds_eq_obs_mid, eq_obs_count_dict = lat_3band_select(lat_bands, ds_incloud)

# plot this variant of latitude bands:
plot_lat_bands(lat_bands, ds, 'equal # obs')