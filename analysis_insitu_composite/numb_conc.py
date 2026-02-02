#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  4 11:33:26 2024
Scripts related to number concentration
- normalization
- plots

@author: ninalar
"""

def unnormalize(count_value, binwidth):
    # Function to unnormalize a size spectra
    # INPUT:
        # - count_value: a size spectra/concentration in m^-4
        # - endbins: bin endpoints in micro-m 
    # OUTPUT:
        # - unnorm_count_value: the unnormalized size spectra/concentration (in m⁻3)
    unnorm_count_value = count_value*binwidth/1.0e6 # divide by 10e^6 to get m istead of micro-m 
    
    return(unnorm_count_value)
    

# --- Histogram for concentration per size bin
# Need the number concentration data for both instruments (CIP and CDP) and their bin information:
def hist_numb_conc(cdp_bulk_df, cdp_bins_df, cip_bulk_df, cip_bins_df):
    import pandas as pd
    import numpy as np

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
    # (Do not do this, makes gap between cdp and cip data)
    #cip_numb_conc_mean =  cip_numb_conc_mean[cip_numb_conc_mean['Bin midpoints (microns):'] >= 100]
  
    # the cip bin counts are normalized by bin width, unnormalize
    cip_numb_conc_mean['unnorm'] = unnormalize(cip_numb_conc_mean['count'], (cip_numb_conc_mean['Bin endpoints (microns):']-cip_numb_conc_mean['Bin startpoints (microns)']))
    # log normalize cip data
    cip_numb_conc_mean['count_norm'] = cip_numb_conc_mean['unnorm']/(np.log(cip_numb_conc_mean['Bin endpoints (microns):']*1.e-6)-np.log(cip_numb_conc_mean['Bin startpoints (microns)']*1.e-6))
    #Checking for what happens when I keep the original normalization
    # This makes the numberconcentrations for the cip too large and you do not get a nice transition from cdp in plots
    #cip_numb_conc_mean['count_norm'] = cip_numb_conc_mean['count']
    
    
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
    
    return(cdp_numb_conc_mean, cip_numb_conc_mean)

def cip_mean_norm_Nt(ds):
    """ Calculate mean log-normalized particle number per bin for CIP observations

    Parameters
    ----------
    ds
        A xarray.DataSet containing the parameter 'CONCENTRATION', with the attribute 'Bin_endpoints'. 
        This value is already normalized by bin width, but not log-normalized. 
    
    Returns
    -------
    cip_part_norm
        A xarray.DataArray that contains the log-normalized values of the CIP number concentration

    """
    import numpy as np

    # Get the binwidth from 'CONCENTRATION' attributes
    lower_limits = ds['CONCENTRATION'].attrs['Bin_endpoints'][0:-1]
    upper_limits = ds['CONCENTRATION'].attrs['Bin_endpoints'][1:]

    binwidth = (upper_limits*1.e-6)-(lower_limits*1.e-6) # change units from micrometers to m

    # unnormalize the values of 'CONCENTRATION'
    unnorm_conc = ds['CONCENTRATION'].T* binwidth 

    # log normalize the values
    log_norm_width = np.log(upper_limits*1.e-6)-np.log(lower_limits*1.e-6)

    #mean
    cip_part_mean = unnorm_conc.mean(dim='time')
    cip_part_mean_norm = cip_part_mean/log_norm_width  #normalize to bin width

    #median
    cip_part_med = unnorm_conc.median(dim='time')
    cip_part_med_norm = cip_part_med/log_norm_width  #normalize to bin width

    return cip_part_mean_norm, cip_part_med_norm

    
def cdp_mean_norm_Nt(ds):
    """ Calculate mean log-normalized particle number per bin for CDP observations

    Parameters
    ----------
    ds
        A xarray.DataSet containing the parameters: 
        -'CDP Bin Particle Count': 
        -'SV': Sample volume
        -'Size': Upper size edge of bin
        -'Bin min': Lower size edge of bin
        This value is already normalized by bin width, but not log-normalized. 
    
    Returns
    -------
    cdp_part_norm
        A xarray.DataArray that contains the log-normalized values of the CIP number concentration

    """
    import numpy as np
    
    # adjust the raw particle count by sample volume
    cdp_part_adj = (ds['CDP Bin Particle Count']/ds['SV'])
    print(cdp_part_adj.values)
    # summary statistics over time
    cdp_part_mean = cdp_part_adj.mean(dim='time')
    cdp_part_med = cdp_part_adj.median(dim='time')
    print(cdp_part_mean.values)
    # log normalize the cdp particle counts to width (Size = upper limit of bin, Bin_min = lower limit of bin)
    # bin units are in micrometers and must be adjusted to m
    log_norm_width = np.log(ds['Size'][0]*1.e-6)-np.log(ds['Bin_min'][0]*1.e-6)
    print(log_norm_width.values)
    cdp_part_mean_norm = cdp_part_mean/log_norm_width  #normalize to bin width
    cdp_part_med_norm = cdp_part_med/log_norm_width  #normalize to bin width

    print(cdp_part_mean_norm.values)

    
    return cdp_part_mean_norm.T, cdp_part_med_norm.T #return transposed to get the correct shape
