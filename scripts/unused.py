
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