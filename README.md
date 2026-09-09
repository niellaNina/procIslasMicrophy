# Processing ISLAS Cloud Particle Data
Code for creating plots and analyisis from Larsgård et. al 2026. 

Processing (microphysics) cloud particle data from the 2022 flight campaign ISLAS. Cloud particle data is from the following instruments:
CIP: Cloud Image Probe - 
CDP: Cloud Droplet Probe


Postprocessing (all code in "postprocessing"):
- Create TAS files from Nav files, for using together with the instrument datafiles in SODA2
    TAS_csv_from_nav_nc.ipynp: creates a csv in the correct format from the nav NetCDF file for a given flight
- Process CIP files with SODA2 
    Settings used for the ISLAS2022 flights:

- CDP preprocessing
    CDP_to_NC.ipynp: creates netCDF from inital CDP csv file. Adds metadata including islasid.
- CIP preprocessing: 
    Expand_CIP_NC.ipynp: adds coordinates, meteorological parameters from the NAV files,  and metadata
- Joint file for analysis
    Updated_NC_to_Joint_NC.ipynp: joins the CDP and CIP into one file with same sample rate. Updates metadata


Analysis (all code in "notebooks"):
- analysis and plots are in islas2022_microphysics.ipynb

