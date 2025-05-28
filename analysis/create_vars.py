
def add_alt_bins(ds, bin_width = 300):
    """Function to create categorical altitude variable based on altitude values
    Parameters
    ----------
    ds
        xarray dataset with all microphy values
    bin_width
        How wide the altitude bins shoud be, default: 300 m

    Returns
    -------
    ds
        xarray dataset, with the added parameter 'altitude bin'
    altitude_bins
        List, The bin edges for the binned altitude
    bin_labels
        List, labels for each bin: middle value of the altitudes included in the bin
    """
    import numpy as np

    # Define the bin edges for the altitude 
    altitude_bins = np.arange(0, ds['alt'].max() + bin_width, bin_width) # based on max values in data

    # digitize altitude data into bins
    alt_bin_indices = np.digitize(ds['alt'], bins = altitude_bins)

    ds = ds.assign_coords(altitude_bin=('time', alt_bin_indices)) # on 'time' dimension

    # Label bins by midpoints
    bin_labels = (altitude_bins[:-1] + altitude_bins[1:]) / 2
    ds['altitude_bin'].data = bin_labels[alt_bin_indices - 1]
    ds.coords['altitude_bin']=ds.coords['altitude_bin'].astype(int)

    return ds, altitude_bins, bin_labels


def lat_2band_select(lat_bands, ds):
    """Function to greate masks for two latitude bands defined by the latitudes in lat_bands
      Parameters
    ----------
    ds
        xarray dataset with all microphy values
    lat_bands
        array of 3 values: lat_min, lat_mid, lat_max, defining the edges of the two lat bands

    Returns
    -------
    lat_mask_north
        mask to select values in ds that is within the northern latitude band
    lat_mask_south
        mask to select values in ds that is within the southern latitude band
    count_dict
        dictionary with following information:
            - count_south: number of observations in the southern region
            - count_north: number of observations in the northern region
            - lat_bands: array of the latitudes used to define the two regions

    """
    lat_min, lat_mid, lat_max = lat_bands # unpack lat selection
    
    # count number of values between different latitudes and add to dictionary
    lat_values = ds['lat']  # Access the latitude coordinate
    count_dict = {'count_south': ((lat_values >= lat_min) & (lat_values <= lat_mid)).sum().item(),
                  'count_north': ((lat_values >= lat_mid) & (lat_values <= lat_max)).sum().item(),
                 'lat_bands': lat_bands}

    # Compute the boolean masks for latitude conditions
    lat_mask_north = (ds['lat'] < lat_max) & (ds['lat'] >= lat_mid)
    lat_mask_south = (ds['lat'] < lat_mid) & (ds['lat'] >= lat_min)

    # Example of filtering a dataset on masks
    ds_filtered_north = ds.where(lat_mask_north, drop=True)
    ds_filtered_south = ds.where(lat_mask_south, drop=True)

    print(f'number of values in 2 bands defined by {lat_bands}:')
    print(f'count_south: {len(ds_filtered_south.lat)},count_north: {len(ds_filtered_north.lat)}')
    
    #return ds_filtered_north, ds_filtered_south, count_dict

    return lat_mask_north, lat_mask_south, count_dict