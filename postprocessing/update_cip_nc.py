def update_cip_nc():
    """updates the CIP nc with dims and coords from nav file

    Parameters
    ----------
    a : int
        The first number.
    b : int
        The second number.

    Returns
    -------
    int
        The sum of the two numbers.
    """
    import xarray as xr # read netcdf-files
    import glob # allows for wildcards in filemanagement
    import os #get a list of all directories/files
    import re #regex
    from pathlib import Path
    from . import config


    from utils.func_nc import nc_save_with_check
    from update_cip_nc import standardize_cip_netcdf

    # sample rate to process (current possibilities: 1,5,12 sek)
    sample_rate = 5
    # -- Paths to datafiles
    # Local disk path to nav data:
    nav_main_path = config.DATA_DIR # directory with flight data
    nav_file_struct_tdyn = '/*_TDYN_*.nc' # structure of nav TDYN file names
    nav_file_struct_nav = '/*_NAV_*.nc' # structure of nav NAV file names
    drop_flights = ['as220005','as220006'] # flights to drop, (if not all are to be analysed 5 and 6 is in france)
        
    # Local disk path to SODA processed CIP files
    cip_main_path = f'/home/ninalar/Documents/MC2/Results_2022-islas/{sample_rate}sAveraging/'

    cip_file_struct = '/*CIP.nc'

    # Save file path
    save_path = SAVE_FILES_PATH

    # -- Get foldernames that are flights (valid in both nav_main_path and cip_main_part)    
    # regex for only using folders that are flights
    patt = re.compile(r"as2200\d{2}") # flights have the pattern as2200 + 2 digits
        
    flights = [
        f for f in os.listdir(nav_main_path) 
        if os.path.isdir(os.path.join(nav_main_path, f)) and patt.fullmatch(f)
        ]
        
    # remove flights to drop using listcomprehension
    flights = [i for i in flights if i not in drop_flights] # list of folders/flights

    # safireid-islasid dictionary
    safire_to_islas = {
        'as220007':'IS22-02',
        'as220008':['IS22-03','IS22-04'],
        'as220009':'IS22-05',
        'as220010':'IS22-06',
        'as220011':'IS22-07',
        'as220012':'IS22-08',
        'as220013':'IS22-09',
        'as220014':'IS22-10',
        'as220015':'IS22-11'
        }
    # Process all flights in the folders
    for flight in flights:
        print(flight)
        # ---- Get CDP and NAV data from flight
        if flight == 'as220008':
            nav_tdyn_file = glob.glob(nav_main_path + flight + nav_file_struct_tdyn) 
            nav_nav_file = glob.glob(nav_main_path + flight + nav_file_struct_nav)
            # flight with safireid as 220008 has two islasids and must be addressed separately:
            for islasid in safire_to_islas['as220008']:
                cip_file = glob.glob(cip_main_path + flight + f'/{islasid}' + cip_file_struct) 
                print(f'Reading: {cip_file[0]}, {nav_nav_file[0]} and {nav_tdyn_file[0]}')
                cip_updated_xds = standardize_cip_netcdf(cip_file[0], nav_tdyn_file[0],nav_nav_file[0], islasid)

                # save to new netCDF
                savefile = save_path + f'CIP_update_{sample_rate}s_{islasid}.nc'
                nc_save_with_check(savefile, cip_updated_xds)

                
        else:
            nav_tdyn_file = glob.glob(nav_main_path + flight + nav_file_struct_tdyn) 
            nav_nav_file = glob.glob(nav_main_path + flight + nav_file_struct_nav)
            cip_file = glob.glob(cip_main_path + flight + cip_file_struct) # returns a list, must access with file[0]

            print(cip_main_path)
            print(flight)

            #cip_xds = xr.open_dataset(cip_file) # returns an xarray dataset
            print(f'Reading: {cip_file[0]}, {nav_nav_file[0]} and {nav_tdyn_file[0]}')
            islasid = safire_to_islas[flight]
            cip_updated_xds = standardize_cip_netcdf(cip_file[0], nav_tdyn_file[0],nav_nav_file[0], islasid)

            #Save to new netCDF
            savefile = save_path + f'CIP_update_{sample_rate}s_{islasid}.nc'      
            nc_save_with_check(savefile, cip_updated_xds)

def standardize_cip_netcdf(cip_nc_file, nav_tdyn_file,nav_nav_file, flight):
    """ Add NAV information to CIP nc file (coordinates, meteorological parameters)

    Parameters
    ----------
    cip_nc_file
        CIP NetCDF file from flight
    nav_file
        Navigation file from flight
    flight
        islasid of flight

    Returns
    -------
    cip_updated_xds
        xarray dataset from the CIP file updated with coordinates and meteorological parameters from the nav file
    """
    
    from datetime import date
    import xarray as xr
    import numpy as np
    import re
    from postprocessing.utils.func_nc import floor_to_sec_res
    
    cip_xds = xr.open_dataset(cip_nc_file) # returns an xarray dataset
    nav_tdyn_xds = xr.open_dataset(nav_tdyn_file) # returns an xarray dataset
    nav_nav_xds = xr.open_dataset(nav_nav_file) # the nav file containing pitch, roll etc

    # fix time dimension cip_xds
    cip_xds = cip_xds.rename_vars({'elapsed_time':'time'}) # elapsed time holds the correct time to use, change name to time for simplisity
    cip_xds = cip_xds.set_coords('time') # set as coordinate 
    cip_xds = cip_xds.swap_dims({'Time': 'time'}) # set as main dimension
    cip_xds = floor_to_sec_res(cip_xds,'time') # floor the times to sec for easier joining

    # drop duplicate time steps (in nav)
    index = np.unique(nav_tdyn_xds.time, return_index = True)[1]
    nav_tdyn_xds = nav_tdyn_xds.isel(time=index)
    index = np.unique(nav_nav_xds.time, return_index = True)[1]
    nav_nav_xds = nav_nav_xds.isel(time=index)
    

    # -- UPDATE COORDINATES based on NAV file
    datetimes = cip_xds.time.values                    #transform from seconds from midnight to datetimeobject     
    
    # select the NAV data from these times (for both nav files)
    sel_data_tdyn = nav_tdyn_xds.sel(time=datetimes, method = "nearest")           # "nearest" due to diffs in decimalseconds
    sel_data_nav = nav_nav_xds.sel(time=datetimes, method = "nearest")

    # Add NAV coordinates to the CIP xarray
    cip_updated_xds = cip_xds.assign_coords(sel_data_tdyn.coords)
    
    # change name of LWC ( to avoid confusion with cdp later)
    cip_updated_xds = cip_updated_xds.rename({'LWC': 'LWC_cip'})

    # add MET variables from Nav file: Temp, Pres, WS/WD, humidity parameters
    cip_updated_xds['T'] = sel_data_tdyn['TEMP1']
    cip_updated_xds['T'].attrs['origin file']=nav_tdyn_file

    cip_updated_xds['P'] = sel_data_tdyn['PRES']
    cip_updated_xds['P'].attrs['origin file']=nav_tdyn_file

    cip_updated_xds['WS'] = sel_data_tdyn['WS']
    cip_updated_xds['WS'].attrs['origin file']=nav_tdyn_file

    cip_updated_xds['WD'] = sel_data_tdyn['WD']
    cip_updated_xds['WD'].attrs['origin file']=nav_tdyn_file

    cip_updated_xds['DP1'] = sel_data_tdyn['DP1']
    cip_updated_xds['DP1'].attrs['origin file']=nav_tdyn_file

    cip_updated_xds['HABS1'] = sel_data_tdyn['HABS1']
    cip_updated_xds['HABS1'].attrs['origin file']=nav_tdyn_file

    cip_updated_xds['RH1'] = sel_data_tdyn['RH1']
    cip_updated_xds['RH1'].attrs['origin file']=nav_tdyn_file

    cip_updated_xds['HABS1'] = sel_data_tdyn['HABS1']
    cip_updated_xds['HABS1'].attrs['origin file']=nav_tdyn_file

    cip_updated_xds['ROLL'] = sel_data_nav['ROLL']
    cip_updated_xds['ROLL'].attrs['origin file']=nav_nav_file

    cip_updated_xds['THEAD'] = sel_data_nav['THEAD']
    cip_updated_xds['THEAD'].attrs['origin file']=nav_nav_file

    cip_updated_xds['PITCH'] = sel_data_nav['PITCH']
    cip_updated_xds['PITCH'].attrs['origin file']=nav_nav_file

    # calculate the gradient of the thead:
    time = sel_data_nav.time
    time_values = (time.dt.hour*3600+time.dt.minute*60+time.dt.second).values
    dfdx_thead= np.gradient(cip_updated_xds['THEAD'], time_values, axis = 0)
    cip_updated_xds['dfdx_thead'] = (('time',), dfdx_thead)
    cip_updated_xds['dfdx_thead'].attrs['description']='Gradient of THEAD'
    cip_updated_xds['dfdx_thead'].attrs['calculated from']=['THEAD','time']
   
    # change names of lat, lon and alt
    cip_updated_xds = cip_updated_xds.rename({'LATITUDE': 'lat','LONGITUDE': 'lon', 'ALTITUDE':'alt'})

    # Calculate SV for CIP and CDP
    #calculate the sample volume (sample area SA * TAS redused * sample time

    # sample area has one value per bin, and are already given in m2: test['SA'].values
    # sample time is given as seconds in the attribute 'RATE': test.attrs['RATE']
    # TAS should be the same as the one used for the rest of the variables: test['TAS'
    cip_updated_xds['SV_CIP'] = cip_updated_xds['SA']*cip_updated_xds['TAS']*cip_updated_xds.attrs['RATE']
    cip_updated_xds['SV_CIP'].attrs['longname']='Sample volume'
    cip_updated_xds['SV_CIP'].attrs['unit']='m3'
    cip_updated_xds['SV_CIP'].attrs['description']='Sample volume per size bin'
    cip_updated_xds['SV_CIP'].attrs['calculated from']=['SA', 'TAS', 'attrs:RATE']

    # -- UPDATE METADATA

    # Global metadata - campaign specifics
    safireid = re.search('as\d+', nav_tdyn_file)
    cip_updated_xds.attrs['safireid'] = safireid.group()
    cip_updated_xds.attrs['islasid'] = flight

    # Global metadata
    #ACDD Highly recommended (4 of 3)
    cip_updated_xds.attrs['title'] = f'CIP dataset from flight {flight} of the ISLAS campaign'
    cip_updated_xds.attrs['summary'] = f'SODA2 Processed CIP data from flight {flight} from the ISLAS 2022 campain. Updated with latitude, longitude, altitude and time coordinates from the flights NAV data'
    cip_updated_xds.attrs['keywords'] = ['Earth Science > Atmosphere > Clouds > Cloud Microphysics > Cloud Liquid Water/Ice',
                                        'Earth Science > Atmosphere > Clouds > Cloud Microphysics > Cloud Droplet Concentration/Size']
    cip_updated_xds.attrs['keywords_vocabulary'] = "GCMD Science Keywords"
    cip_updated_xds.attrs['Conventions'] = ['ACDD-1.3']
    # Filenames used to create this file
    navfilename = nav_tdyn_file.split('/')[-1]
    cip_updated_xds.attrs['NAV file']=navfilename
    cipfilename = cip_nc_file.split('/')[-1]
    cip_updated_xds.attrs['SODA NC file']=cipfilename

    # Global metadata - ACDD recommended

    # Global metadata - suggested
    cip_updated_xds.attrs['date_modified'] = date.today().strftime("%Y-%m-%d")
    cip_updated_xds.attrs['date_metadata_modified'] = date.today().strftime("%Y-%m-%d")


    cip_xds.close()
    nav_tdyn_xds.close()
    nav_nav_xds.close()
    
    return cip_updated_xds

if __name__ == "__main__":
    update_cip_nc()