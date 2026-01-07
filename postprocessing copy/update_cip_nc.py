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
    from func_nc import floor_to_sec_res
    
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