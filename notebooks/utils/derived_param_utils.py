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
    import numpy as np

    if ds[iwc_param].attrs['parameterization']=='Heymsfield2010_general':
        suffix='H10'
    elif ds[iwc_param].attrs['parameterization']=='Brown and Francis 1995':
        suffix = 'BF95'
    else:
        print('Parametrization not defined')
        return
    
    twc_name = f'TWC_{suffix}'
    slf_name = f'SLF_{suffix}'
    
    ds[twc_name] = (ds[iwc_param]+ds[lwc_param]).where(ds['incloud_flag'], np.nan) # first calculate TWC
    # update TWC attributes
    ds[twc_name].attrs['longname']='Total Water Content'
    ds[twc_name].attrs['unit']='g/m^3'
    ds[twc_name].attrs['description']='Sum of Liquid and Ice Water Content'
    ds[twc_name].attrs['calculated from']=[iwc_param,lwc_param]
    ds[twc_name].attrs['Ice mass parameterization'] = ds[iwc_param].attrs['parameterization']

    ds[slf_name] = ((ds[lwc_param]/ds[twc_name])*100).where(ds['incloud_flag'], np.nan) # calculate SLF in percent
    ds[slf_name].attrs['longname']='Supercooled Liquid Fraction'
    ds[slf_name].attrs['units']='Percent'
    ds[slf_name].attrs['description']='Liquid Water Content divided by Total Water Content'
    ds[slf_name].attrs['calculated from']=[lwc_param, twc_name]
    ds[slf_name].attrs['Ice mass parameterization'] = ds[iwc_param].attrs['parameterization']

    
    return ds

def mass_param(param, xds, name_add=""):
    # Function to calculate the mass and IWC based on the given mass-parametrization scheme
    # Input: 
    # --- param: str
    #       parametrization scheme to use, available options: Heymsfield2010, Brown&Francis, Heymsfield2010_general, CRYSTAL
    # --- xds: xarray DataSet
    #        xarray containing the original CIP bins, sizes and concentrations. The sizing method used when preprocessing the 2Dprobe data will affect
    #        the results from this function. 
    #        Following Wu and McFarquhar (2016) the diameter of smallest circle enclosing the particle is recommended, and used for the ISLAS dataset.  
    # --- varname: str
    #        string to add to 'MASS' and 'IWC' to set variable names (to use for identification if multiple parametrizations are used on one dataset)
    #        Default: ""           
    # Returns:
    # --- xds: xarray DataSet
    #        original xarray updated with the new parameters
    #
    # Example runs: 
    # ---
    #     f_cip_xds, massdim_param = mass_param('Heymsfield2010',f_cip_xds,'_H10')
    #     f_cip_xds, massdim_param = mass_param('Brown&Francis95',f_cip_xds,'_BF95')
    #     f_cip_xds, massdim_param = mass_param('Heymsfield2001',f_cip_xds,'_H01')

    # parametrization options
    massdim_param = {'Heymsfield2010': {'a':0.0121, 'b':1.9, 
                                        'description': 'CIP particle mass calculated from the Heymsfield (2010) mass-dimention relationship for warm clouds (T > -25°C). Computed the using alpha=0.0121, beta=1.9.',
                                        'doi': ""},
                 'Brown&Francis95': {'a':0.00294, 'b':1.9,
                                     'description': 'CIP particle mass calculated from the Brown and Francis 1978 mass-dimention relationship. Computed the using alpha=0.00294, beta=1.9.',
                                     'doi': ""},
                 'Heymsfield2010_general': {'a':0.00528,'b':2.1,
                                    'description': 'CIP particle mass calculated from Heymsfield et. al 2010. (also an option in SODA) General relationship to use for all ice cloud types. (when formation mechanisms and temperatures are not known)',
                                    'doi': "10.1175/2010JAS3507.1"}, #this one is technically also from 2010
                 'CRYSTAL': {'a':0.0061,'b':2.05,
                             'description':'CIP particle-mass parametrisation from the CRYSTAL dataset, convectively generated cirrus anvils',
                             'doi': "10.1175/1520-0469(2004)061<0982:EIPDDF>2.0.CO;2"}}


    # get coefficients from parametrization param
    a = massdim_param[param]['a']
    b = massdim_param[param]['b']

    # mass calculation: M = a*D^b
    mvar_name = 'MASS' + name_add
    xds[mvar_name] = a*(xds['MIDBINS']/1.0e4)**b # in m from um, MIDBINS are 25,50,75, ...,1600
    # update metadata for variable
    xds[mvar_name] = xds[mvar_name].assign_attrs({'long_name':f'Mass from {param}',
                                                    'source':'CIP',
                                                    'units':'g',
                                                    'parameterization': param,
                                                    'parameterization info': massdim_param[param]})

    # IWC calculation
    var_name = 'IWC' + name_add # adjust parameter name to account for multiple parametrizations in one dataset
    binwidth = xds['MIDBINS'][0].values[1] - xds['MIDBINS'][0].values[0]
    spec = xds['CONCENTRATION']*(binwidth/1.0e6) # unnormalize the concentration
    lwc_per_bin = spec*xds[mvar_name] 
    xds[var_name] = lwc_per_bin.sum(dim='Vector64')

    # update metadata for variable
    xds[var_name] = xds[var_name].assign_attrs({'long_name':f'Ice Water Content from {param}',
                                                    'instrument':'CIP',
                                                    'units':'gram/m3',
                                                    'parameterization': param,
                                                    'parameterization info': massdim_param[param] })
    
    
    return xds

