def calculate_slf(ds, iwc_param, lwc_param):
    """Calculate Supercooled liquid fraction(SLF) from given IWC and LWC parameters

    Parameters
    ----------
    ds
        xarray dataset that includes at least one IWC parameter and at least one LWC parameter
    iwc_param
        Name of IWC parameter to use for calculation of SLF
    lwc_param
        Name of LWC parameter to use for calculation of SLF

    Returns
    -------
    ds
        Updated xarray dataset that includes TWC and SLF calculated from the given IWC and LWC parameters
    """
    import xarray as xr
    
    ds['TWC'] = ds[iwc_param]+ds[lwc_param] # first calculate TWC
    # update TWC attributes
    ds['TWC'].attrs['longname']='Total Water Content'
    ds['TWC'].attrs['unit']='g/m^3'
    ds['TWC'].attrs['description']='Sum of Liquid and Ice Water Content'
    ds['TWC'].attrs['calculated from']=[iwc_param,lwc_param]

    ds['SLF'] = (ds[lwc_param]/ds['TWC'])*100 # calculate SLF in percent
    ds['SLF'].attrs['longname']='Supercooled Liquid Fraction'
    ds['SLF'].attrs['unit']='Percent'
    ds['SLF'].attrs['description']='Liquid Water Content divided by Total Water Content'
    ds['SLF'].attrs['calculated from']=[lwc_param, 'TWC']

    
    return ds