def create_derived_vars(xds):
    """ Function that creates the following derived variables from exisiting variables in cdp file:
        Sample volume, Mass, Number Conc per bin, Number Conc calc, LWC per bin calc, LWC calc

    This function relies on the 'math' and 're' packages

    Parameters
    ----------
    xds: xr.DataSet
        xarray containing original cdp variables

    Returns
    ----------
    xds: xr.DataSet
        the original xarray, with added new derived variables
    """
    import math
    import re

    # extract values from metadata
    sa = float(xds.attrs['Sample Area (mm^2)'])/1e6 # get sample area in m^2
    st = int(re.findall(r"(\d+) sec",xds.attrs['Sample Time'])[0]) # get sample time in sec

    # calculate sample volume
    xds['SV_cdp'] = sa * xds['TAS1'] * st
    xds['SV_cdp'] = xds['SV_cdp'].assign_attrs(
        units = 'm^3', 
        long_name = 'CDP Sample Volume', 
        description = 'Sample Volume calculated from attrs:"Sample Area", attrs:"Sample Time" and data_vars:"TAS1"',
        source = 'CDP')
    
    # Mass of individual droplet in bin = water density times volume of droplet. Size is the diameter of the droplet(largest size).
    xds['Mass'] = (1000*4*math.pi/3)*(0.5*xds['Size']*10**(-6))**3
    xds['Mass'] = xds['Mass'].assign_attrs(
        long_name = 'Mass of individual droplet in bin',
        units = 'kg',
        description = 'Derived mass of droplet, water density (1000 kg/m3) times volume of droplet, calculated from "Size"',
        source = 'CDP')
    
    # Compute the number concentration in m-3 of each bin (counts per bin per sample volume)
    xds['Number Conc per bin'] = xds['CDP Bin Particle Count']/xds['SV_cdp']
    xds['Number Conc per bin'] = xds['Number Conc per bin'].assign_attrs(
        long_name = 'Number concentration per bin',
        units = '#/m3',
        description = 'Derived Number concentration per bin. Counts per sample volume. Derived from "CDP Particle Count" and "SV"',
        source = "CDP")

    # Compute the total number concentration per time (sum of bin counts per sample volume) for bins larger than 6 mum (equal to bin 3)
    # divide by 1000000 to turn m3 to cm3
    xds['Number Conc calc']=((xds['CDP Bin Particle Count'][:,3:].sum(dim='CDP_Bin'))/xds['SV_cdp'])/1e6
    xds['Number Conc calc'] = xds['Number Conc calc'].assign_attrs(
        long_name = 'Total Number concentration >6$\mu$ m',
        units = '#/cm3',
        description = 'Derived Total Number concentration for particles larger than 6 micrometer. Sum of counts for bins 7-30, per sample volume. Derived from "CDP Biin Particle Count" and "SV"',
        source = "CDP")

    # calculate the LWC per bin
    xds['LWC per bin calc'] = xds['Number Conc per bin']*xds['Mass']
    xds['LWC per bin calc'] = xds['LWC per bin calc'].assign_attrs(
        long_name = 'LWC per bin',
        units = 'kg/m3',
        description = 'Derived Liquid Water Content calculated from mass and number concentration, per bin. Derived from "Mass Particle count" and "Number Conc per bin"',
        source = "CDP")
    
    # calculate the total LWC per time 
    # multiply by 1000 to get g/m3
    xds['LWC calc'] = 1000*xds['LWC per bin calc'].sum(dim='CDP_Bin')
    xds['LWC calc'] = xds['LWC calc'].assign_attrs(
        long_name = 'LWC',
        units = 'g/m3',
        description= 'Derived Total Liquid Water Content for particles larger than micrometers. Derived from "LWC per bin calc"',
        source = "CDP")

    return xds