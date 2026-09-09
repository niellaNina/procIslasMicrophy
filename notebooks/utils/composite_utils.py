def add_alt_bins(ds, altitude_bins):
    import numpy as np

    # digitize altitude data into bins
    alt_bin_indices = np.digitize(ds['alt'], bins = altitude_bins)

    ds = ds.assign_coords(altitude_bin=('time', alt_bin_indices)) # on 'time' dimension

    # Label bins by midpoints
    bin_labels = (altitude_bins[:-1] + altitude_bins[1:]) / 2
    ds['altitude_bin'].data = bin_labels[alt_bin_indices - 1]
    ds.coords['altitude_bin'] = ds.coords['altitude_bin'].astype(int)
    return ds

def add_dist_bins(ds, dist_bins):
    import numpy as np
    # digitize altitude data into bins
    dist_bin_indices = np.digitize(ds['distance_from_ice'], bins = dist_bins)
   
    ds = ds.assign_coords(dist_bin=('time', dist_bin_indices)) # on 'time' dimension

    # adjust indices to 0-based
    dist_bin_indices_adj = dist_bin_indices - 1

    # Only handle valid indices
    dist_bin_labels = np.full_like(dist_bin_indices_adj, fill_value=np.nan, dtype=float)
    valid_ind = dist_bin_indices_adj < len(dist_bins)
    dist_bin_labels[valid_ind] = dist_bins[dist_bin_indices_adj[valid_ind]]

    # Label data
    ds['dist_bin'].data = dist_bin_labels
    ds.coords['dist_bin'] = ds.coords['dist_bin'].astype(int)
    return ds

def add_t_bins(ds, temp_bins):
    import numpy as np
    # digitize altitude data into bins
    temp_bin_indices = np.digitize(ds['T'], bins = temp_bins)
   
    ds = ds.assign_coords(temp_bin=('time', temp_bin_indices)) # on 'time' dimension

    # adjust indices to 0-based
    temp_bin_indices_adj = temp_bin_indices - 1

    # Only handle valid indices
    temp_bin_labels = np.full_like(temp_bin_indices_adj, fill_value=np.nan, dtype=float)
    valid_ind = temp_bin_indices_adj < len(temp_bins)
    temp_bin_labels[valid_ind] = temp_bins[temp_bin_indices_adj[valid_ind]]

    # Label data
    ds['temp_bin'].data = temp_bin_labels
    ds.coords['temp_bin'] = ds.coords['temp_bin'].astype(int)
    return ds

def create_counts(ds, val, val_bins):
    # Function to create counts array tu use when making heatmaps. Keeps control of normalizations etc.
    # Input: 
    # --- ds: dataset, that at least have 'base_time' and an altitude as parameters
    # --- val: Value to use for grouping
    # --- val_bins: bins of val to group by
    # output:
    # --- count_df: df ouf number of observations per latitudebin and altitude bin for the given dataset

 
    grouped_data = ds['base_time'].groupby_bins(val, bins =val_bins)
    
    count_data = grouped_data.map(lambda group: group.groupby('altitude_bin').count())
    
    # reorganize data before plotting heatmap
    # - turn into dataframe - unstack to get correct array structure  
    count_df = count_data.to_dataframe().unstack()
    
    # - transpose to get altitude on y-axis - reset index and drop outer index(base_time)
    count_df = count_df.T.reset_index(level=0, drop = True)
    # -  make sure all possible altitude bins are represented, fill with 0 - reverse order of altitudes
    count_df = count_df.reindex(bin_labels, fill_value=0).iloc[::-1] #
    count_df = count_df.fillna(0) # set nan to 0 (for easier plot management)
    count_df = count_df.astype(int) # set the count to int
    count_df = count_df.iloc[:, ::-1] # reverse the columns to get the northern most values to the left
    #fix labels 
    new_labels = [f"[{label.right}, {label.left})" for label in count_df.columns]
    count_df.columns = new_labels
    
    return count_df
'''
def add_slf_bins(ds, slf_bins):
    import numpy as np
    
    # digitize slf data into bins
    slf_clipped = ds["SLF"].clip(min=0, max=100) # clip to make sure 0 and 100 is included
    slf_bin_indices = np.digitize(slf_clipped, bins = slf_bins, right=True)
    
    ds = ds.assign_coords(slf_bin=('time', slf_bin_indices)) # on 'time' dimension

    # adjust indices to 0-based
    slf_bin_indices_adj = slf_bin_indices - 1
  
    # Only handle valid indices
    slf_bin_labels = np.full_like(slf_bin_indices_adj, fill_value=np.nan, dtype=float)
    valid_ind = slf_bin_indices_adj < len(slf_bins)
    slf_bin_labels[valid_ind] = slf_bins[slf_bin_indices_adj[valid_ind]]

    # Label data
    ds['slf_bin'].data = slf_bin_labels
    ds.coords['slf_bin'] = ds.coords['slf_bin'].astype(int)
    return ds
'''
def add_slf_bins(ds, slf_edges, slf_labels, slf_param):
    import numpy as np
    
    #Clip data to [0, 100]
    slf_clipped = ds[slf_param].clip(min=0, max=100)

     # Digitize: right=False ⇒ (edges[i-1], edges[i]]
    #    0   → (-inf, 0]       → index 0
    #    100 → (100, 105]? no, 100 ≤ 100 so → index len(edges)-1
    slf_bin_indices = np.digitize(slf_clipped, bins=slf_edges, right=False)

    # Convert to 0-based bin index and CLIP into valid range
    #    indices are in [0, len(edges)] → we want 0..len(labels)-1
    slf_bin_indices_adj = np.clip(slf_bin_indices - 1, 0, len(slf_labels) - 1)

    # Map indices to lower-edge labels: 0, 5, ..., 95
    slf_bin_labels = slf_labels[slf_bin_indices_adj]

    # Attach to dataset
    ds = ds.assign_coords(slf_bin=("time", slf_bin_labels.astype(int)))

    # add attributes
    ds['slf_bin'] = ds['slf_bin'].assign_attrs(
                long_name = 'Binning varaibale for SLF',
                description = f'SLF bins, 0,5,...95, based on {slf_param}',
            )

    return ds