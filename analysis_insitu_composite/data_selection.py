def preselect_ds(ds, remove_cirrus_T = -30, marine_lat = 70):
    """Function to remove cirrus (from temperature) and land values (from latitude)

    Parameters
    ----------
    ds
        xarray dataset with all microphy values
    save_path
        str, path to where plots should be saved
    remove_cirrus_T
        Temperature, default = -30. Remove cirrus by only using values above this temperature threshold
        Everything is included if set to ""
    marine_lat
        Latitude value to include. only latitudes above this threshold is included.
        Everything is included if set to ""
    
    Returns
    -------
    presel_ds
        xarray dataset with only the preselected values
    presel_info_txt
        list of text for plots etc: [0]-> short descr (for filenames) [1]-> long description
    """

    short_txt = ''
    long_txt = ''


    # masks for preselection
    if marine_lat != "":
        marinelat_mask = (ds['lat']>=marine_lat).compute()
        ds = ds.where(marinelat_mask, drop = True)
        short_txt = short_txt + f'_lat{marine_lat}'
        long_txt = long_txt + f' Lat<{marine_lat} removed, '
    else:
        short_txt = short_txt + f'_latall'
        long_txt = long_txt + f'All lat included, '

    if remove_cirrus_T != "":
        cirrusT_mask = (ds['T']>=remove_cirrus_T).compute()
        ds = ds.where(cirrusT_mask, drop = True)
        short_txt = short_txt + f'_T{remove_cirrus_T}'
        long_txt = long_txt + f' Temp<{remove_cirrus_T}C removed, '
    else:
        short_txt = short_txt + f'_Tall'
        long_txt = long_txt + f'All T included, '
    
    # Define presel_info_txt
    presel_info_txt = [short_txt, long_txt] 

    return ds, presel_info_txt


def sel_incloud_values(ds, th_method = 'LWC_IWC_th'):
    """Function to select out dataset that only includes incloud values according to settings

    Parameters
    ----------
    ds
        xarray dataset with all microphy values
    th_method
        str, which method should be used for determining incloud values
            - 'LWC_IWC_th' based on LWC and IWC (Default)
            - 'LWC_th' based on only LWC
            - 'TWC_th' based on only TWC
            - 'N_th' based on number concentration from both CDP and CIP


    Returns
    -------
    incloud_ds
        xarray dataset with only the incloud values
    incloud_info
        long description of threshold used (for plots etc.)
    """

    # Define masking of ds based on th_method selection
    if th_method == 'LWC_IWC_th':
        # ----- Water content threshold

        # following the korolev 22 paper: "In the present study the thresholds for liquid water content and ice water content (IWC) 
        # were set as LWC > 0.01 g m−3, IWC > 0.01 g m−3, respectively. The phase composition of clouds was identified based on the 
        # assessment of the ice water fraction mu = IWC∕(LWC + IWC). Thus, clouds with mu=0.9 were considered as ice, 
        # clouds with Mu =0.1 were defined as liquid, 
        # and clouds 0.1 ≤ 𝜇𝜇 ≤ 0.9 were determined as mixed-phase clouds."
        
        lwc_th = 0.01
        
        # either lwc or iwc needs to be larger than the threshold, use lwc_iwc_mask
        incloud_mask = ((ds['LWC corr']>= lwc_th)|(ds['IWC100']>= lwc_th)).compute() # mask the values based on lwc or iwc according to threshold

        long_txt = f'{lwc_th} m^-3, (LWC or IWC)'

    elif th_method == 'LWC_th':
        # only lwc have to be larger than threshold, use lwc mask
        lwc_th = 0.01

        incloud_mask = (ds['LWC corr']>=lwc_th).compute() # mask the values based on lwc according to threshold
        long_txt = f'{lwc_th} m^-3, (LWC)'

    elif th_method == 'TWC_th':
        # twc have to be larger than threshold value, use twc mask
        lwc_th = 0.01

        incloud_mask = (ds['TWC']>=lwc_th).compute() # mask the values based on twc according to threshold
        long_txt = f'{lwc_th} m^-3, (TWC)'


    elif th_method == 'N_th':
        # ----- Number concentration threshold
        # Following table 2 from Evans et al 2025:
        # Ice concentration threshold to define ice = 0.1 L-1 (or m-3) (NT100 is given in m-3)
        # Cdp drop concentration to define liquid = 2 cm-3 (numb conc corrected is given in cm-3)

        n_ice_th = 0.1
        n_drp_th = 2
        
        incloud_mask = ((ds['Number Conc corr']>= n_drp_th)|(ds['NT100']>= n_ice_th)).compute()

        long_txt = f'Nt_cdp>{n_drp_th} cm^-3, Nt_cip100>{n_ice_th} L^-1'

    else:
        print('WARNING: in-cloud threshold method not defined!')
        return

    # create the selected dataset based on selected mask
    incloud_ds = ds.where(incloud_mask, drop = True)

    incloud_info = [th_method, long_txt]
    
    return incloud_ds, incloud_info

