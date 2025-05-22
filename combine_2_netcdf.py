#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 13:21:16 2025

@author: ninalar
"""

# imports from packages
import pandas as pd
import xarray as xr
import numpy as np
import warnings


# imports from files
import functions
import read_cdp
import read_cip_txt
#import read_lwc
import read_nav
import read_cip_nc
import numb_conc
import read_seaice


# surpress UserWarning connected to timezoneless np.datetime
warnings.filterwarnings("ignore", message="no explicit representation of timezones available for np.datetime64")
# surpress UserWrning connected to boolean series indexing (creating dataframe with null values)
warnings.filterwarnings("ignore", message="Boolean Series key will be reindexed to match DataFrame index.")

# --- Global formatting/settings/variables

# Threshold for in-cloud values
# following the korolev 22 paper: "In the present study the thresholds for liquid water content and ice water content (IWC) 
# were set as LWC > 0.01 g m−3, IWC > 0.01 g m−3, respectively. The phase composition of clouds was identified based on the 
# assessment of the ice water fraction mu = IWC∕(LWC + IWC). Thus, clouds with mu=0.9 were considered as ice, 
# clouds with Mu =0.1 were defined as liquid, 
# and clouds 0.1 ≤ 𝜇𝜇 ≤ 0.9 were determined as mixed-phase clouds."
in_cl_th = 0.01 # in-cloud threshold based on Korolev 2003
#path_store = '../Results_2022-islas/Processed/'
path_store = '../Results_2022-islas/Processed/LWC_th/' # path for when using LWC for incloud threshold
# ------------------------------------------------------------------------
# --- Data import

# Navigational data (nav_df: data variables, nav_stats_dict: statistics for each flight)
nav_df, nav_stats_dict, extra_info= read_nav.read_nav() # extra_info includes limits for the plots (campaign_cood_limits) and extra landing and takeoff times

# CDP data (cdp_bulk_df: Bulk variables per flight, cdp_bins_df: Bin details (max, min size)
#           cdp_var_df: Variable information (names, units), cdp_meta_df: Metadata/instrument settings)
cdp_bulk_df, cdp_bins_df, cdp_var_df, cdp_meta_df = read_cdp.read_cdp(nav_df)

# CIP data 
# nc file(bulk information) (cip_bulk_calc_df: Bulk variables per flight, cip_conc_df: Concentration per bin, 
#                            cip_varnc_df: Variable, longname and unit)
cip_bulk_calc_df, cip_conc_df, cip_varnc_df = read_cip_nc.read_cip_nc() 
cip_pb_df, cip_bins_df, cip_var_df, cip_proc_df = read_cip_txt.read_cip_txt()

# ---------------------------------------------------
# -- Prepare dataframe for calculations
# Join the relevant columns from the nav, the cip, and the cdp data
# CIP IWC, LWC etc have been calculated for particles >100 mum
cip_df = cip_bulk_calc_df[['time', 'NT (#/m3)','IWC (gram/m3)','LWC (gram/m3)', 'MVD (um)']].sort_values(by='time', axis=0)
cdp_df = cdp_bulk_df[['time', 'Number Conc corr (#/cm^3)', 'LWC corr (g/m^3)','MVD (um)','Number Conc (#/cm^3)', 'LWC (g/m^3)']].sort_values(by='time', axis=0)

# rename columns to identify instrument and standardize units
cip_df = cip_df.rename(columns={'NT (#/m3)':'cip NumConc (#/m^3)','IWC (gram/m3)':'cip IWC (g/m^3)','LWC (gram/m3)':'cip LWC (g/m^3)', 'MVD (um)':'cip MVD (um)'})
cdp_df = cdp_df.rename(columns={'Number Conc corr (#/cm^3)': 'cdp NumConc corr (#/cm^3)', 'LWC corr (g/m^3)':'cdp LWC corr (g/m^3)',
                                'MVD (um)': 'cdp MVD (um)','Number Conc (#/cm^3)': 'cdp NumConc (#/cm^3)', 'LWC (g/m^3)':'cdp LWC (g/m^3)'})

# select temperature and flightid from nav
nav_sel_df = nav_df[['Latitude (degree)', 'Longitude (degree)','Altitude (meter)','Temperature (Celsius)','TAS (m/s)','flightid', 'safireid']].sort_values(by='time', axis=0)

# join cip and cdp by time
meas_df = pd.merge_asof(cip_df, cdp_df, on = 'time', direction = 'nearest', suffixes=('_cip','_cdp'))
microphy_df = pd.merge_asof(meas_df, nav_sel_df, on = 'time', direction = 'nearest')

# Sea ice concentration
# -- Get sea_ice concentration along flight tracks from satellite data
seaice_df = read_seaice.read_seaice(microphy_df, extra_info)
# merge seaice_df with microphy
microphy_df = pd.merge(microphy_df, seaice_df, on=['time','Latitude (degree)','Longitude (degree)','flightid'], how='inner')

# -----------------------------------------------------------------------------------
# --- Define categories for selection (in-loud, surface conditions, cloud position)

# add manually set selection categories
microphy_df = functions.add_man_relevance(microphy_df) # relevant clouds: lower mixed phase
microphy_df = functions.add_man_cloud(microphy_df)     # cloudid: individual flight patterns from single flights

# prepare dataframe for later calculation of position in cloud and surface conditions:
microphy_df['Cloud_pos']=np.nan # empty column to be filled with cloud positions
microphy_df['Cloud_rel_alt']=np.nan # empty column to be filled with cloud relative altitude (0 = base 1 = top)
microphy_df['surface_cond']='sea' # set default to sea-ocean (following CF area type table)

microphy_df['surface_cond'] = microphy_df.apply(functions.update_land, axis=1) # Update surface_cond with land mask
microphy_df.loc[microphy_df["Sea Ice Conc. (Percent)"] >15, "surface_cond"] = 'sea-ice' # update surface_cond to 'sea-ice' if 'Sea Ice Conc. (Percent)' > 15 % (following CF area type table)

# ALTERNATIVE: Update surface cond for 'sea-ice' and marginal ice zone: 'MIZ'
# following Young et. al. MIZ for sea ice fraction between 10% and 90%
# microphy_df.loc[microphy_df["Sea Ice Conc. (Percent)"] >90, "surface_cond"] = 'sea-ice'
# microphy_df.loc[(microphy_df["Sea Ice Conc. (Percent)"] >10) & (microphy_df["Sea Ice Conc. (Percent)"] <=90), "surface_cond"] = 'MIZ'

# rearrange columns more logically: - Positional - Identifier - Ambient - Microphysical - Calculated
microphy_df = microphy_df[['time','Latitude (degree)','Longitude (degree)','Altitude (meter)',
                          'flightid', 'safireid',
                          'Temperature (Celsius)','TAS (m/s)',
                           'cip NumConc (#/m^3)','cdp NumConc (#/cm^3)','cdp NumConc corr (#/cm^3)',
                           'cip IWC (g/m^3)','cip LWC (g/m^3)','cdp LWC (g/m^3)','cdp LWC corr (g/m^3)',
                           'cip MVD (um)','cdp MVD (um)',
                           'Relevance','cloudid','Cloud_pos', 'Cloud_rel_alt', 'surface_cond']]

# ------------------------------------------------------------------------------
# Calculated parameters

# Total number concentration (adding CIP and CDP)
microphy_df['cip NumConc (#/cm^3)'] = microphy_df['cip NumConc (#/m^3)']*10**(-6) # adjust cip to equal units as cdp
# sum cip and cdp in #/cm3 to find total num conc
microphy_df['tot NumConc (#/cm3)'] = microphy_df['cip NumConc (#/cm^3)']+microphy_df['cdp NumConc corr (#/cm^3)']

# TWC - Total Water Content: estimate total water content from cdp LWC and CIP IWC 
microphy_df['TWC (gram/m3)'] = microphy_df['cdp LWC corr (g/m^3)'] + microphy_df['cip IWC (g/m^3)']

# Selection of in-cloud values (True or False based on threshold condition)
microphy_df['incloud']= microphy_df['cdp LWC corr (g/m^3)']>in_cl_th #direct boolean indexing (True if bigger, False if smaller)
#microphy_df['incloud']= microphy_df['TWC (gram/m3)']>in_cl_th #direct boolean indexing (True if bigger, False if smaller)

# -- incloud height calculations
# calculating in-cloud altitude dictionary for all named clouds:
cloud_alt_dict = functions.cloud_alt_pos(microphy_df, 'cloudid') # get the cloud top and base heights (in a dict)

# Calculating in-cloud relative altitude based on max and min altitude of cloud
cloudids = microphy_df[microphy_df['cloudid']!='nan']['cloudid'].unique() # get unique cloudids
microphy_df['Cloud_rel_alt']=microphy_df.apply(functions.rel_alt, args=(cloudids, cloud_alt_dict), axis=1)

# set category "Top-Bulk-Base", categorize data based on where in cloud:
# Apply the function row-wise to create the new column
microphy_df['Cloud_pos'] = microphy_df.apply(functions.set_c_pos_cat, cloud_pos_dict = cloud_alt_dict, axis=1)

# -- Calculate SLF (supercooled liquid fraction)
# estimate total water content from cdp as liquid and all from CIP as ice (use LWC from cdp and IWC from CIP)
microphy_df['TWC (gram/m3)'] = microphy_df['cdp LWC corr (g/m^3)']+microphy_df['cip IWC (g/m^3)']

# masking all values of TWC lower than in cloud threshold
#microphy_df['TWC (gram/m3)'] = microphy_df['TWC (gram/m3)'].mask(microphy_df['TWC (gram/m3)'] < in_cl_th)
# also mask cloud parameters for same time step
#microphy_df['cdp LWC corr (g/m^3)'] = microphy_df['cdp LWC corr (g/m^3)'].mask(np.isnan(microphy_df['TWC (gram/m3)']))
#microphy_df['cip IWC (g/m^3)'] = microphy_df['cip IWC (g/m^3)'].mask(np.isnan(microphy_df['TWC (gram/m3)']))
#microphy_df['tot NumConc (#/cm3)'] = microphy_df['tot NumConc (#/cm3)'].mask(np.isnan(microphy_df['TWC (gram/m3)']))

# -----
# optional masking all LWC instead of TWC
microphy_df['cdp LWC corr (g/m^3)'] = microphy_df['cdp LWC corr (g/m^3)'].mask(microphy_df['cdp LWC corr (g/m^3)'] < in_cl_th)

# also mask cloud parameters for same time step
microphy_df['TWC (gram/m3)'] = microphy_df['cdp LWC corr (g/m^3)'].mask(np.isnan(microphy_df['cdp LWC corr (g/m^3)']))
microphy_df['cip IWC (g/m^3)'] = microphy_df['cip IWC (g/m^3)'].mask(np.isnan(microphy_df['cdp LWC corr (g/m^3)']))
microphy_df['tot NumConc (#/cm3)'] = microphy_df['tot NumConc (#/cm3)'].mask(np.isnan(microphy_df['cdp LWC corr (g/m^3)']))
# -------

# calculate SLF by dividing LWC with TWC
microphy_df['SLF']= microphy_df['cdp LWC corr (g/m^3)']/microphy_df['TWC (gram/m3)']*100

# categorize cloud phase
# set up categories for phase determination
# list of conditions to select categories
SLF_conds = [
    (microphy_df['SLF'] <= 0.1),
    (microphy_df['SLF'] >= 0.9),
    (microphy_df['SLF'] > 0.1) & (microphy_df['SLF'] < 0.9)
]
# list of categories to return
phase = [
    'ice',
    'liquid',
    'mixed-phase'
]
microphy_df['cloud_phase']=np.select(SLF_conds,phase,"Outside of cloud")


# ----- Turning the df into a netcdf ---

for fi in microphy_df['flightid'].unique():
    
    # get dataframe fro one flight only and turn into basic xarray
    df = microphy_df[microphy_df['flightid']==fi]
    ds = xr.Dataset.from_dataframe(df)
    
    # set coordinates
    ds = ds.set_coords(("Latitude (degree)" , "Longitude (degree)", "time", "Altitude (meter)"))
    # use time as a dimension
    ds = ds.swap_dims({"index":"time"})
    # drop the index coordinate (this is only the location in the pandas dataframe)
    ds = ds.drop_vars("index")
    
    # rename coordinates
    ds = ds.rename({"Latitude (degree)":"lat" , "Longitude (degree)":"lon", "Altitude (meter)":"alt"})
    # update coordinate attributes (cf-standard_name and unit)
    ds.lat.attrs['standard_name']='Latitude'
    ds.lat.attrs['units']='degree_north'
    ds.lon.attrs['standard_name']='Longitude'
    ds.lon.attrs['units']='degree_east'
    ds.alt.attrs['standard_name']='Altitude'
    ds.alt.attrs['units']='m'

    # rename variables with too complicated names
    ds = ds.rename({"Temperature (Celsius)":"temp", "TAS (m/s)":"tas", 
                              'cip NumConc (#/m^3)':'N_ice_orig','cip NumConc (#/cm^3)':'N_ice', 
                              'cdp NumConc (#/cm^3)':'N_liq_orig','cdp NumConc corr (#/cm^3)':'N_liq','tot NumConc (#/cm3)':'N_tot',
                              'cip IWC (g/m^3)':'IWC', 'cip LWC (g/m^3)':'LWC_cip', 'TWC (gram/m3)': 'TWC',
                              'cdp LWC (g/m^3)':'LWC_orig', 'cdp LWC corr (g/m^3)':'LWC',
                              'cip MVD (um)':'mvd_cip','cdp MVD (um)':'mvd_cdp',
                              })

    ## update variable attributes
    ds.surface_cond.attrs['standard_name']='area_type'
    ds.surface_cond.attrs['values']='CF Area Type Table'
    ds.surface_cond.attrs['longname']= 'Surface condition'
    
    ds.temp.attrs['standard_name']='air_temperature'
    ds.temp.attrs['unit']='celsius'
    ds.temp.attrs['longname']='Air Temperature'
    
    ds.tas.attrs['standard_name']='platform_speed_wrt_air'
    ds.tas.attrs['unit']='m/s'
    ds.tas.attrs['longname']= 'True air speed'
    
    # Number concentration variables
    ds.N_ice_orig.attrs['standard_name']='number_concentration_of_ice_crystals_in_air'
    ds.N_ice_orig.attrs['unit']='#/m^3'
    ds.N_ice_orig.attrs['longname']= 'CIP Number concentration (#/m^3)'
    
    ds.N_ice.attrs['standard_name']='number_concentration_of_ice_crystals_in_air'
    ds.N_ice.attrs['unit']='#/cm^3'
    ds.N_ice.attrs['longname']= 'CIP Number concentration (#/cm^3)'
    
    ds.N_liq_orig.attrs['standard_name']='number_concentration_of_cloud_liquid_water_particles_in_air'
    ds.N_liq_orig.attrs['unit']='#/cm^3'
    ds.N_liq_orig.attrs['longname']= 'CDP Number concentration uncorrected'
    
    ds.N_liq.attrs['standard_name']='number_concentration_of_cloud_liquid_water_particles_in_air'
    ds.N_liq.attrs['unit']='#/cm^3'
    ds.N_liq.attrs['longname']= 'CDP Number concentration corrected by TAS'
    
    ds.N_tot.attrs['unit']='#/cm^3'
    ds.N_tot.attrs['longname']= 'Total number concentration'
    
    # Water content variables
    ds.IWC.attrs['standard_name']='atmosphere_mass_content_of_cloud_ice'
    ds.IWC.attrs['unit']='g/m^3'
    ds.IWC.attrs['longname']= 'CIP Ice water content'
    
    ds.LWC_cip.attrs['standard_name']='atmosphere_mass_content_of_cloud_liquid_water'
    ds.LWC_cip.attrs['unit']='g/m^3'
    ds.LWC_cip.attrs['longname']= 'CIP Liquid water content'
    
    ds.LWC_orig.attrs['standard_name']='atmosphere_mass_content_of_cloud_liquid_water'
    ds.LWC_orig.attrs['unit']='g/m^3'
    ds.LWC_orig.attrs['longname']= 'CDP Liquid water content, uncorrected'
    
    ds.LWC.attrs['standard_name']='atmosphere_mass_content_of_cloud_liquid_water'
    ds.LWC.attrs['unit']='g/m^3'
    ds.LWC.attrs['longname']= 'CDP Liquid water content, TAS corrected'
    
    ds.TWC.attrs['standard_name']='atmosphere_mass_content_of_cloud_condensed_water'
    ds.TWC.attrs['unit']='g/m^3'
    ds.TWC.attrs['longname']= 'Total water content, CIP and CDP combined'
    
    # Mean Volume Diameter variables
    ds.mvd_cip.attrs['unit']='$\mu$m'
    ds.mvd_cip.attrs['longname']= 'CIP Mean Volume Diameter'
    
    ds.mvd_cdp.attrs['unit']='$\mu$m'
    ds.mvd_cdp.attrs['longname']= 'CDP mean volume diameter'
    
    # Supercooled liquid fraction
    ds.SLF.attrs['longname']='Supercooled liquid fraction'
    ds.SLF.attrs['description'] = 'Fraction of liquid water over total water content'
    
    # set vars that are attrs to attrs and drop as variables
    ds.attrs['islasid'] = np.unique(ds.flightid.values)[0]
    ds = ds.drop_vars("flightid")
    ds.attrs['safireid'] = np.unique(ds.safireid.values)[0]
    ds = ds.drop_vars("safireid")

    ds.to_netcdf(f'{path_store}ISLAS_processed_{fi}.nc','w')