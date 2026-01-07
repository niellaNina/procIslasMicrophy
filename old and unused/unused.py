
def cip_mean_norm_Nt_alt(ds):

    import numpy as np

    # calculate the mean log-normalized particle number per bin (for histogram plotting) Based on the 
    # raw particle count (ds['COUNT'])
    # this function works, but does not give the correct values because the SA wich the SV_CIP is calculated from
    # has values 0 for the two largest size bins.
    
    # adjust the raw particle count by sample voluem
    cip_part_adj = (ds['COUNTS']/ds['SV_CIP'])

    # summary statistics over time
    cip_part_mean = cip_part_adj.mean(dim='time')

    # log normalize the cip particle counts to width (bin limits are found in COUNTS attributes (array of len 65))
    lower_limits = ds['COUNTS'].attrs['Bin_endpoints'][0:-1]
    upper_limits = ds['COUNTS'].attrs['Bin_endpoints'][1:]
     # bin units are in micrometers and must be adjusted to m
    log_norm_width = np.log(upper_limits*1.e-6)-np.log(lower_limits*1.e-6)
    cip_part_norm = cip_part_mean/log_norm_width  #normalize to bin width

    return cip_part_norm



#--------------------------------------------------------------------------

#TODO needs to be moved somewhere sensible
# plotting the Mean area ratio for the flight
mar_2d_array = np.stack(cip_updated_xds.MEAN_AREARATIO.values)

print(mar_2d_array.shape)

bin_endpoints = cip_updated_xds.MEAN_AREARATIO.attrs['Bin_endpoints']
bin_endpoints = bin_endpoints[1:] # remove the first item as this is the first bin startpoint (to get lenght equal)

mar_2d_xda = xr.DataArray(
    mar_2d_array,
    coords=[bin_endpoints,cip_updated_xds["time"]],
    dims=["end_bins","time",]
)

mar_2d_xda.attrs['long_name'] = cip_updated_xds.MEAN_AREARATIO.attrs['long_name']
mar_2d_xda.coords['end_bins'].attrs['long_name'] = 'size bin'
mar_2d_xda.coords['end_bins'].attrs['unit'] = 'um'

# Filter DataArray to include only end_bins > 100
mar_2d_xda_filtered = mar_2d_xda.sel(end_bins=mar_2d_xda.end_bins > 100)

#mar_2d_xda.plot(figsize=(14,5))
mar_2d_xda_filtered.plot(figsize=(14, 5))

plt.title(f'CIP Mean area ratio per bin for bin sizes > 100 um \n (flight {cip_updated_xds.attrs['islasid']})')
plt.savefig('100MeanAreaRatio_IS22-01.png')
#---------------------------------------------------------------------------------

#TODO needs to be moved somewhere sensible
# plotting the Mean aspect ratio for the flight

mas_2d_array = np.stack(cip_updated_xds.MEAN_ASPECTRATIO.values)

bin_endpoints = cip_updated_xds.MEAN_ASPECTRATIO.attrs['Bin_endpoints']
bin_endpoints = bin_endpoints[1:] # remove the first item as this is the first bin startpoint (to get lenght equal)

mas_2d_xda = xr.DataArray(
    mas_2d_array,
    coords=[bin_endpoints,cip_updated_xds["time"]],
    dims=["end_bins","time",]
)

mas_2d_xda.attrs['long_name'] = cip_updated_xds.MEAN_ASPECTRATIO.attrs['long_name']
mas_2d_xda.coords['end_bins'].attrs['long_name'] = 'size bin'
mas_2d_xda.coords['end_bins'].attrs['unit'] = 'um'

# Filter DataArray to include only end_bins > 100
mas_2d_xda_filtered = mas_2d_xda.sel(end_bins=mas_2d_xda.end_bins > 100)

#mas_2d_xda.plot(figsize=(14,5))
mas_2d_xda_filtered.plot(figsize=(14, 5))

plt.title(f'CIP Mean aspect ratio per bin for bin sizes > 100 um \n (flight {cip_updated_xds.attrs['islasid']})')
plt.savefig('100MeanAspectRatio_IS22-01.png')

#------------------------------------------------------------