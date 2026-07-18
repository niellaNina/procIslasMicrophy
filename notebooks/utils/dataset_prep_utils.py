def preselect(ds, rm_cirrus = True, rm_c_T = -35, marine = True, m_lat = 70, rm_roll = True, roll_th = 5, rm_head = True, head_th = 1, rm_dist=""):
    """ Function to preselect the dataset to use in composite analysis

    This function relies on the "pandas" package

    Parameters
    ---------- 
        ds: Xarray.DataSet
            xarray dataset 
        rm_cirrus: Boolean, Default True
            Option to remove cirrus by temperature
        rm_c_T: Int
            Temperature to use in selection of values to remove if rm_cirrus=True
        marine: Boolean, Default True
            Option to only select marine values by latitude minimum
        m_lat: Int
            Lowest latitude to use in selection of values to remove marine values
        rm_roll: Boolean, Default True
            Option to only use values where Roll is less than threshold
        roll_th: Int, Default 5
            Roll threshold
        rm_head: Boolean, Default True
            Option to remove observations where the gradient of the heading exceeds threshold
        head_th: Int, Default 1
            Tead threshold
        rm_dist: Int, Default ""
            distances to remove from dataset
    
    Returns
    ----------
        ds: Xarray.DataSet
            the original ds with the time_dim floored to closest whole seconds
    """
    pre_text = ""  #text to potentially use for setting attributes in dataset

    ds_relevant = ds

    if marine == True:
        pre_text = pre_text + f'only marine (lat>70), '
        marinelat_mask = (ds_relevant['lat']>=m_lat).compute()
        ds_relevant = ds_relevant.where(marinelat_mask, drop = True)

    if rm_cirrus == True:
        pre_text = pre_text + f'Cirrus removed (>{rm_c_T}), ' 
        # select only values where temperature is higher than selected temperature (avoid cirrus)
        cirrusT_mask = (ds_relevant['T']>=rm_c_T).compute()
        ds_relevant = ds_relevant.where(cirrusT_mask, drop = True)
    
    if rm_roll == True:
        pre_text = pre_text + f'Roll removed, '
        # select only values where roll is less than selected threshold
        roll_mask = (abs(ds_relevant['ROLL'])<=roll_th).compute()
        ds_relevant = ds_relevant.where(roll_mask, drop=True)

    if rm_head == True:
        pre_text = pre_text + f'Head removed, '
        # select only values where the gradient of the heading is less than selected threshold
        head_mask = (abs(ds_relevant['dfdx_thead'])<=head_th).compute()
        ds_relevant = ds_relevant.where(head_mask, drop=True)

    if isinstance(rm_dist, int):
        # remove distances larger than 975 km (to remove the areas not covering complete clouds.)
        mask_large_dist = (ds['distance_from_ice']<rm_dist).compute()
        ds_relevant = ds_relevant.where(mask_large_dist,drop=True)

    return ds_relevant, pre_text


def nc_save_with_check(savefile ,xds):
    """Check if a netCDF file exists. Overwrite existing if user accepts, create new if not existing.

    This function relies on the 'os' package for path management.

    Parameters
    ----------  
        savefile: str
            Path to netCDF file
        xds: xarray.DataSet 
            Dataset to write to savefile

    """
    import os

    # Check if the file exists
    if os.path.exists(savefile):
        overwrite = input(f'The file {savefile} exists. Do you want to overwrite it?(y/n)')
        if overwrite.lower() in ["yes", "y"]:
            print(f'Saving to {savefile}')
            xds.to_netcdf(path=savefile, mode='a')
        else:
            print("Exiting...")
    else:
        xds.to_netcdf(path=savefile, mode='w')
        print(f'Saving to {savefile}')
        
    return

def incloud_select(ds, lwc, iwc,  th_method='LWC_IWC_th',lwc_th = 0.01, iwc_th = 0.01,n_ice_th = 0.1,n_drp_th = 2):
    """ Function to preselect the dataset to use in composite analysis

    This function relies on the "pandas" package

    Parameters
    ---------- 
        ds: Xarray.DataSet
            xarray dataset 
        lwc: namev of LWC parameter to use
        iwc: name of IWC parameter to use
        th_method: str, Default 'LWC_IWC_th'
            Method used to decide in-cloud values. 
            Options:
            - 'LWC_th' based on only LWC
            - 'TWC_th' based on only TWC
            - 'LWC_IWC_th' based on LWC and IWC
            - 'N_th' based on number concentration from both CDP and CIP
        lwc_th: float, Default = 0.01
            LWC/TWC threshold value
        iwc_th: float, Default = 0.01
            IWC threshold value
        n_ice_th: float, Default = 0.1
        n_drp_th: float, Default = 2

        ----- Water content threshold
        For either TWC, LWC or IWC+LWC, following the korolev 22 paper: "In the present study the thresholds for liquid water content and ice water content (IWC) 
        were set as LWC > 0.01 g m−3, IWC > 0.01 g m−3, respectively. The phase composition of clouds was identified based on the 
        assessment of the ice water fraction mu = IWC∕(LWC + IWC). Thus, clouds with mu=0.9 were considered as ice, 
        clouds with Mu =0.1 were defined as liquid, 
        and clouds 0.1 ≤ 𝜇𝜇 ≤ 0.9 were determined as mixed-phase clouds."

        ----- Number concentration threshold
        Following table 2 from Evans et al 2025:
        Ice concentration threshold to define ice = 0.1 L-1 (or m-3) (NT100 is given in m-3)
        Cdp drop concentration to define liquid = 2 cm-3 (numb conc corrected is given in cm-3)
   
    Returns
    ----------
        ds_incloud: Xarray.DataSet
            xarray dataset with only in-cloud values based on in-cloud selection method
    
    """

    # ---- Second selection: what should be considered in-cloud?
    # th_method is used to selecting the selection criteria and is added to saved plots for organizing
    if th_method == 'LWC_th':
        # only lwc have to be larger than threshold, use lwc mask
        incloud_mask = ((ds[lwc]>= lwc_th)).compute() # mask the values based on twc
        #th = f'{lwc_th} m^-3, (LWC)'
    elif th_method == 'TWC_th':
        # twc have to be larger than threshold value, use twc mask
        incloud_mask = ((ds['TWC']>= lwc_th)).compute() # mask the values based on twc
        #th = f'{lwc_th} m^-3, (TWC)'
    elif th_method == 'LWC_IWC_th':
        # either lwc or iwc needs to be larger than the threshold, use lwc_iwc_mask
        incloud_mask = ((ds[lwc]>= lwc_th)|(ds[iwc]>= iwc_th)).compute() # mask the values based on lwc or iwc according to threshold
        #th = f'{lwc_th} m^-3, (LWC or IWC)'
    elif th_method == 'N_th':
        incloud_mask = ((ds['Number Conc calc']>= n_drp_th)|(ds['NT100']>= n_ice_th)).compute() # using calc instead of corr
        #th = f'Nt_cdp>{n_drp_th} cm^-3, Nt_cip100>{n_ice_th} L^-1'
    else:
        print('WARNING: in-cloud threshold method not defined!')

    # create the selected dataset based on selected mask
    ds_incloud = ds.where(incloud_mask, drop = True)

    return ds_incloud, th_method, iwc_th 


def sea_ice_from_sat(sic_path, sic_file_struct, dates):
    """Get sea ice concentration from satellite dat
    This function relies on the xarray package
    Parameters
    ----------  
        sic_path: str
            Path to netCDF files
        sic_file_struct: str 
            Filename structure of file to get
        dates: list
            list of dates in 'YYYYMMDD' format to get sea ice information from
    Returns
    ----------
        sics: list
            list of xarrays with sea ice concentration, one per date in dates

    """

    import xarray as xr

    sics = []
    for date in dates:
        # Get sea ice information from the given date
        sic_ds = xr.open_dataset(sic_path  + date + sic_file_struct)

        # rename data variable and update attributes
        sic_ds['sic'] = sic_ds['__xarray_dataarray_variable__'].assign_attrs(units="Percent", description="Sea Ice Concentration")
        sic_ds = sic_ds.drop_vars(['__xarray_dataarray_variable__'])

        # add some attributes
        sic_ds.attrs['date'] = date
        sic_ds.attrs['file'] = f'asi-n6250-{date}-5.4_regridded.nc'

        sics.append(sic_ds)

        sic_ds.close() # close connection


    return sics
