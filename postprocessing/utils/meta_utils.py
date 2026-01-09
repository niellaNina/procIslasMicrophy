def attrs_from_list(xds, meta_dict):
    """ Function to create attributes for xarray from dictionary after checking if it exists first

    Requires 'datetime' to be installed
    Args:
        xds: xarray dataset 
        meta_dict; dictionary with kew value pairs equal to the metadata to be added

    Returns:
        the xds updated with metadata
    """
    from datetime import date
    #TODO: unit test and error handling (check type of the value to add)

    for key, value in meta_dict.items():
        if value == '': # do not add empty attributes
            continue
        
        # check if attr already exist
        if hasattr(xds.attrs, key):
            # the attribute exists, check if value is the same
            attr_value = xds.attrs.get(key)
            if isinstance(attr_value, list):
                #if value is a list check if the list is equal
                if set(attr_value) != set(value):
                    #if not equal join the two lists
                    new_list = list(set(attr_value + value))
                    print(f'{key} existed and is updatet to {new_list}')
                    xds.attrs[key]=new_list # add metadata to xds

            else:
                # check if value is the same, ask user which value to be used
                if attr_value != value:
                    # if not equal to the existing value prompt user to choose
                    print(f'Attribute {key} exists, but does not contain the same value.')
                    print('Replace the old with new?')
                    print(f'Old; {attr_value}')
                    print(f'New: {value}')
                    user_input = input()
                    if user_input.lower() == "yes" or user_input.lower() == "y":
                        print("Updating new metadata")
                        xds.attrs[key]=value # add metadata to xds
                    elif user_input.lower() == "no" or user_input.lower() == "n":
                        print("Keeping old metadata")
                    else:
                        print("Invalid input.")

        else:
            xds.attrs[key]=value # add metadata to xds
    # list time metadata was updated
    xds.attrs['date_metadata_modified']= date.today().strftime("%Y-%m-%d"), #ACDD:S

    return xds

def var_attrs_from_list(xds, meta_dict):
    """ Function to add attributes to xarray variables from dictionary

    Requires 'datetime' to be installed

    Args:
        xds: xarray dataset 
        meta_dict; dictionary with kew value pairs equal to the metadata to be added

    Returns:
        the xds updated with metadata
    """
    from datetime import datetime, date

    #TODO: unit test and error handling (check type of the value to add)
    # run through all variables in dataset
    for var_name in xds.data_vars:

        for key, value in meta_dict.items():
            xds[var_name].attrs[key] = value
    
    # list time metadata was updated
    xds.attrs['date_metadata_modified']= date.today().strftime("%Y-%m-%d"), #ACDD:S

    return xds

def meta_from_data(xds):
    """ 
    Function to create a dictionary of the acdd metadata items that can be created from the dataset coordinate elements

    Requires the 'datetime', 'isodate' and 'pandas' libraries to be installed

    Args:
        xds: xarray dataset 
        

    Returns:
        meta_from_data_dict: dictionary of key value pairs containing the data dependent metadata
    """
    import pandas as pd
    from datetime import date
    import isodate

    # TODO make this name independent

    # time management
    time_min = pd.to_datetime(xds.time.values.min())
    time_max = pd.to_datetime(xds.time.values.max())
    time_diff = isodate.duration_isoformat(time_max-time_min)

    # turn time resolution into ISO 8601:2004
    res = int(xds.attrs['RATE'])
    iso_res = 'PT'+str(res)+'S'
    
    meta_from_data_dict = {'geospatial_lat_max':xds.lat.values.max(),
                'geospatial_lat_min':xds.lat.values.min(),
                'geospatial_lon_max':xds.lon.values.max(),
                'geospatial_lon_min':xds.lon.values.min(),
                'geospatial_vertical_max':xds.alt.values.max(),
                'geospatial_vertical_min':xds.alt.values.min(),
                'time_coverage_duration':time_diff,
                'time_coverage_end':time_max.isoformat(),
                'time_coverage_resolution':iso_res,
                'time_coverage_start':time_min.isoformat(),
                'date_metadata_modified':date.today().strftime("%Y-%m-%d"), #ACDD:S
                }

    return meta_from_data_dict
