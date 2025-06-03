#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  4 11:33:26 2024
Creating histograms that include both CIP and CDP data.

@author: ninalar
"""

# imports from packages
import pandas as pd
import numpy as np


# imports from files
import analysis.functions as functions


# --- Histogram for concentration per size bin
# Need the number concentration data for both instruments (CIP and CDP) and their bin information:
def hist_numb_conc(cdp_bulk_df, cdp_bins_df, cip_bulk_df, cip_bins_df):
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
    cip_numb_conc_mean =  cip_numb_conc_mean[cip_numb_conc_mean['Bin midpoints (microns):'] >= 100]
  
    # the cip bin counts are normalized by bin width, unnormalize
    cip_numb_conc_mean['unnorm'] = functions.unnormalize(cip_numb_conc_mean['count'], (cip_numb_conc_mean['Bin endpoints (microns):']-cip_numb_conc_mean['Bin startpoints (microns)']))
    # log normalize cip data
    cip_numb_conc_mean['count_norm'] = cip_numb_conc_mean['unnorm']/(np.log(cip_numb_conc_mean['Bin endpoints (microns):']*1.e-6)-np.log(cip_numb_conc_mean['Bin startpoints (microns)']*1.e-6))
    #Checking for what happens when I keep the original normalization
    cip_numb_conc_mean['count_norm'] = cip_numb_conc_mean['count']
    
    
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