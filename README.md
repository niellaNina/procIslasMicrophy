# Processing ISLAS Cloud Particle Data
Processing (microphysics) cloud particle data from the 2022 flight campaign ISLAS. Cloud particle data is from the following instruments:
CIP: Cloud Image Probe - 
CDP: Cloud Droplet Probe


Preprocessing:
- Create TAS files from Nav files TODO: document and add scripts here)
- Process CIP files with SODA2 (TODO: describe how this is done here, with settings)
- CDP preprocessing:
    - Run CDP_to_NC notebook to get CDP observations in netCDF format, also transforms from safireid to islasid
- CIP preprocessing: 
    - Run Expand_CIP_NC notebook to add coordinates and meteorological parameters from the NAV files, also transforms from safireid to islasid

- Run Updated_NC_to_Joint_NC notebook to join the CDP and CIP observations into one file with the same sample rate

