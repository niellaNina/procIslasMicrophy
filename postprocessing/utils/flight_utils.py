def get_safire_flightid(path):
    """ Get list of safire flight ids from folder names in path, and set up dictionary between safireid and islasid

    This function relies on the packages 're' and 'os' for datamanagement

    Parameters
    ----------
    path: str
        Path where the flight dependent folders can be found

    Returns
    -------
    cip_updated_xds
        xarray dataset from the CIP file updated with coordinates and meteorological parameters from the nav file
    """
    import os #get a list of all directories/files
    import re #regex

    drop_flights = ['as220005','as220006'] # flights to drop, (if not all are to be analysed 5 and 6 is in france)

    # -- Get foldernames that are flights (valid in both nav_main_path and cip_main_part)    
    # regex for only using folders that are flights
    patt = re.compile(r"as2200\d{2}") # flights have the pattern as2200 + 2 digits
        
    flights = [
        f for f in os.listdir(path) 
        if os.path.isdir(os.path.join(path, f)) and patt.fullmatch(f)
        ]
        
    # remove flights to drop using listcomprehension
    flights = [i for i in flights if i not in drop_flights] # list of folders/flights

    # safireid-islasid dictionary
    safire_to_islas = {
        'as220007':'IS22-02',
        'as220008':['IS22-03','IS22-04'], # two islas ids on the safireid as220008
        'as220009':'IS22-05',
        'as220010':'IS22-06',
        'as220011':'IS22-07',
        'as220012':'IS22-08',
        'as220013':'IS22-09',
        'as220014':'IS22-10',
        'as220015':'IS22-11'
        }
    
    return flights, safire_to_islas