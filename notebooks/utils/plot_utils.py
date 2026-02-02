def plot_lat_bands(lat_bands, ds, ds_incloud,sic_max_ds,sic_min_ds, title, savefile = ''):
    # Function to plot the observations per flight, and indicate the norhtern and southern region
    # Input: 
    # --- lat_bands: array of the the latitudes used for separation, should include at least min and max latitude
    # --- ds: full original dataset for plotting flightpaths
    # --- title: title to add to plot
    # --- savefile(optional): path and filename to save plot into

    # functions
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec # gridspec for nested subfigures
    import matplotlib.lines as mlines
    from matplotlib.patches import Rectangle
    import pandas as pd 
    

   # coordinates of Kiruna TODO: remove?
    lat_kir = 67.8256
    lon_kir = 20.3351

    # set colors
    n_col='tab:blue'
    s_col='tab:red'
    
    # --- Set up figure
    fig = plt.figure(figsize=(20, 10))
    gs = GridSpec(1, 2, figure=fig)
    ax = fig.add_subplot(gs[0,0], projection=ccrs.NorthPolarStereo())

    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linewidth=2)
    data_projection = ccrs.PlateCarree()

    # get datavalues for plotting
    lat_values = ds['lat'].values
    lon_values = ds['lon'].values

    # select out northern marine in cloud values
    n_mask = (ds_incloud['region'] == 'north').compute()
    n_ds = ds_incloud.where(n_mask, drop=True)
    n_lat_values = n_ds['lat'].values
    n_lon_values = n_ds['lon'].values
    
    # select out southern marine in cloud values
    s_mask = (ds_incloud['region'] == 'south').compute()
    s_ds = ds_incloud.where(s_mask, drop=True)
    s_lat_values = s_ds['lat'].values
    s_lon_values = s_ds['lon'].values


    ax.scatter(lon_values, lat_values, marker='.',c='darkgrey', label='Flight path', transform = data_projection)
    ax.scatter(n_lon_values, n_lat_values, marker='o',c=n_col, label=f'Northern marine region \n in-cloud ({len(n_lon_values)} obs)', transform = data_projection)
    ax.scatter(s_lon_values, s_lat_values, marker='o',c=s_col, label=f'Southern marine region \n in-cloud ({len(s_lon_values)} obs)', transform = data_projection)

    # Draw latitude bands
    for lat_band in lat_bands:
        ax.plot(range(0, 51, 5), [lat_band]*11, color='k', transform=ccrs.PlateCarree())
        if lat_band in [lat_min, lat_max]:
            lat_text = round(lat_band, 2)
        else:
            lat_text = lat_band
        ax.text(28, lat_band-0.9, f"{lat_text:.2f}°", transform=ccrs.PlateCarree(), ha='center', va='bottom', fontsize=20, color='k', 
                rotation=30, bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))

    # Text for northern and southern marine

    ax.text(30, 75.5, "Northern \n marine region", transform=ccrs.PlateCarree(), ha='center', va='bottom', fontsize=20, color=n_col, 
                rotation=30)
    ax.text(30, 71.5, "Southern \n marine \n region", transform=ccrs.PlateCarree(), ha='center', va='bottom', fontsize=20, color=s_col, 
                rotation=30)

    # add sea ice concentration
    cs = ax.contour(sic_max_ds['lon'],sic_max_ds['lat'],sic_max_ds['sic'], transform=ccrs.PlateCarree(),levels=[25.], colors='tab:grey', linestyles='dashed')
    contour_legend_max = mlines.Line2D([], [], color='tab:grey',linestyle='--', label='25% Sea Ice \n concentration')
    cs_m = ax.contour(sic_max_ds['lon'],sic_min_ds['lat'],sic_min_ds['sic'], transform=ccrs.PlateCarree(),levels=[25.], colors='tab:grey', linestyles='dashdot')
    contour_legend_min = mlines.Line2D([], [], color='tab:grey',linestyle='-.', label='25% Sea Ice \n concentration')
    
    #Plot Kiruna 
    ax.plot(lon_kir, lat_kir, marker='^',markersize=16, color='red', transform=data_projection)
    offset_lon = 0.95  # adjust the horizontal offset
    offset_lat = -0.95  # adjust the vertical offset
    ax.text(lon_kir + offset_lon, lat_kir + offset_lat, "Kiruna", transform=data_projection, ha='right', va='bottom',
            bbox=dict(facecolor='white', alpha=1, edgecolor='black', pad=5), fontsize=16)

    # set extent of the plot to the full area covered by the dataset +/- an increment of 1
    ax.set_extent([ds.lon.values.min()-5, ds.lon.values.max()+1, ds.lat.values.min()-1.5, ds.lat.values.max()+1])
    
    ax.set_title(f'{title}', fontsize = 25)

    handles, labels = ax.get_legend_handles_labels() # get exisiting labels
    title_proxy = Rectangle((0,0), 0, 0, color='w') # create second "title"
    # append handles and labels with new title
    handles.append(title_proxy)
    labels.append('Sea ice edge:')
    #append with sea ice information
    handles.append(contour_legend_max)
    max_date_obj = pd.to_datetime(sic_max_ds.attrs['date'], format='%Y%m%d')
    labels.append(f'Max: {max_date_obj.strftime('%b')} {max_date_obj.strftime('%d')}')
    handles.append(contour_legend_min)
    min_date_obj = pd.to_datetime(sic_min_ds.attrs['date'], format='%Y%m%d')
    labels.append(f'Min: {min_date_obj.strftime('%b')} {min_date_obj.strftime('%d')}')

    plt.legend(handles=handles, labels=labels, loc='lower left', fontsize=16)
    plt.tight_layout()
    if savefile !='':
        plt.savefig(savefile, bbox_inches='tight')


def plot_flight_obs(ds, ds_incloud, sic_max_ds,sic_min_ds, obs, lat_bands='',title='', savefile = ''):
    # Function to plot latitude bands used for further analysis
    # Input: 
    # --- lat_bands: array of the the latitudes used for separation, should include at least min and max latitude
    # --- ds: full original dataset for plotting flightpaths
    # --- title: title to add to plot
    # --- savefile(optional): path and filename to save plot into

    # functions
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec # gridspec for nested subfigures
    import matplotlib.lines as mlines
    from matplotlib.patches import Rectangle
    import pandas as pd 
    import numpy as np

    # coordinates of Kiruna
    lat_kir = 67.8256
    lon_kir = 20.3351

    #colors for flights (for consistent coloring in plots)
    c_flights = {'IS22-01':'wheat',
              'IS22-02':'tab:orange',
              'IS22-03':'tab:cyan',
              'IS22-04':'tab:purple',
              'IS22-05':'tab:pink',
              'IS22-06':'tab:brown',
              'IS22-07':'tab:red',
              'IS22-08':'tab:olive',
              'IS22-09':'tab:grey',
              'IS22-10':'tab:blue',
              'IS22-11':'tab:green'}

    
    # --- Set up figure
    fig = plt.figure(figsize=(15, 10))
    gs = GridSpec(1, 2, figure=fig)
    ax = fig.add_subplot(gs[0,0], projection=ccrs.NorthPolarStereo())

    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.BORDERS, linewidth=2)
    data_projection = ccrs.PlateCarree()

    # get the flightids
    flights = np.unique(ds.islasid.values)

    for flight in flights:
        
        # Select out the data connected with the flight
        f1_mask = (ds['islasid']==flight).compute()
        ds_f = ds.where(f1_mask, drop = True)
        f1_mask = (ds_incloud['islasid']==flight).compute()
        ds_incloud_f = ds_incloud.where(f1_mask, drop = True)


        # get datavalues for plotting lines
        lat_values = ds_f['lat'].values
        lon_values = ds_f['lon'].values

        # get datavalues for plotting incloud values
        obs_lat_values = ds_incloud_f['lat'].values
        obs_lon_values = ds_incloud_f['lon'].values
        
        if obs == True:
            # plot all lat-lon points and where incloud obs
            ax.scatter(lon_values, lat_values, marker='.', c=c_flights[flight], alpha=0.01, transform = data_projection)
            ax.scatter(obs_lon_values, obs_lat_values, marker='o',label=flight, c= c_flights[flight], transform = data_projection)
        else:
            ax.scatter(lon_values, lat_values, marker='.', c=c_flights[flight], transform = data_projection, label = flight)

    if lat_bands!='':
        # Draw latitude bands
        for lat_band in lat_bands:
            ax.plot(range(0, 51, 5), [lat_band]*11, color='k', transform=ccrs.PlateCarree())
            if lat_band in [lat_min, lat_max]:
                lat_text = round(lat_band, 2)
            else:
                lat_text = lat_band
            ax.text(28, lat_band-0.9, f"{lat_text:.2f}°", transform=ccrs.PlateCarree(), ha='center', va='bottom', fontsize=20, color='k', 
                    rotation=30, bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))

        # Text for northern and southern marine

        ax.text(30, 75.5, "Northern \n marine region", transform=ccrs.PlateCarree(), ha='center', va='bottom', fontsize=20, color='tab:blue', 
                    rotation=30)
        ax.text(30, 71.5, "Southern \n marine \n region", transform=ccrs.PlateCarree(), ha='center', va='bottom', fontsize=20, color='tab:red', 
                    rotation=30)
    
    # add sea ice concentration
    cs = ax.contour(sic_max_ds['lon'],sic_max_ds['lat'],sic_max_ds['sic'], transform=ccrs.PlateCarree(),levels=[25.], colors='tab:grey', linestyles='dashed')
    contour_legend_max = mlines.Line2D([], [], color='tab:grey',linestyle='--', label='25% Sea Ice \n concentration')
    cs_m = ax.contour(sic_max_ds['lon'],sic_min_ds['lat'],sic_min_ds['sic'], transform=ccrs.PlateCarree(),levels=[15.], colors='tab:grey', linestyles='dashdot')
    contour_legend_min = mlines.Line2D([], [], color='tab:grey',linestyle='-.', label='25% Sea Ice \n concentration')
    
    #Plot Kiruna 
    ax.plot(lon_kir, lat_kir, marker='^',markersize=16, color='red', transform=data_projection)
    offset_lon = 0.95  # adjust the horizontal offset
    offset_lat = -0.95  # adjust the vertical offset
    ax.text(lon_kir + offset_lon, lat_kir + offset_lat, "Kiruna", transform=data_projection, ha='right', va='bottom',
            bbox=dict(facecolor='white', alpha=1, edgecolor='black', pad=5), fontsize=16)
    
    # set extent of the plot to the full area covered by the dataset +/- an increment of 1
    ax.set_extent([ds.lon.values.min()-5, ds.lon.values.max()+1, ds.lat.values.min()-1.5, ds.lat.values.max()+1])
    
    if title!='':
        ax.set_title(f'{title}', fontsize = 25)

    handles, labels = ax.get_legend_handles_labels() # get exisiting labels
    title_proxy = Rectangle((0,0), 0, 0, color='w') # create second "title"
    # append handles and labels with new title
    handles.append(title_proxy)
    labels.append('Sea ice edge:')
    #append with sea ice information
    handles.append(contour_legend_max)
    max_date_obj = pd.to_datetime(sic_max_ds.attrs['date'], format='%Y%m%d')
    labels.append(f'Max: {max_date_obj.strftime('%b')} {max_date_obj.strftime('%d')}')
    handles.append(contour_legend_min)
    min_date_obj = pd.to_datetime(sic_min_ds.attrs['date'], format='%Y%m%d')
    labels.append(f'Min: {min_date_obj.strftime('%b')} {min_date_obj.strftime('%d')}')

    plt.legend(handles=handles, labels=labels, loc='lower left', fontsize=16,)
    plt.tight_layout()
    if savefile !='':
        plt.savefig(savefile, bbox_inches='tight', dpi=100)

def plot_flight_obs_single(full_extent, ds, ds_incloud, sic_ds, ax):
    # Function to plot latitude bands used for further analysis
    # Input: 
    # --- ds: full original dataset for plotting flightpaths
    # --- title: title to add to plot
    # --- savefile(optional): path and filename to save plot into

    # functions
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec # gridspec for nested subfigures
    import matplotlib.lines as mlines
    from matplotlib.patches import Rectangle
    import pandas as pd 
    import numpy as np

    # coordinates of Kiruna
    lat_kir = 67.8256
    lon_kir = 20.3351

    #colors for flights (for consistent coloring in plots)
    c_flights = {'IS22-01':'wheat',
              'IS22-02':'tab:orange',
              'IS22-03':'tab:cyan',
              'IS22-04':'tab:purple',
              'IS22-05':'tab:pink',
              'IS22-06':'tab:brown',
              'IS22-07':'tab:red',
              'IS22-08':'tab:olive',
              'IS22-09':'tab:grey',
              'IS22-10':'tab:blue',
              'IS22-11':'tab:green'}


    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linewidth=2)
    data_projection = ccrs.PlateCarree()

    # get the flightids
    flight = np.unique(ds.islasid.values)[0]

    # get datavalues for plotting lines
    lat_values = ds['lat'].values
    lon_values = ds['lon'].values

    # get datavalues for plotting incloud values
    obs_lat_values = ds_incloud['lat'].values
    obs_lon_values = ds_incloud['lon'].values
        
    # plot all lat-lon points and where incloud obs
    #ax.scatter(lon_values, lat_values, marker='.', c=c_flights[flight], alpha=0.01, transform = data_projection, label=f'Flightpath')

    # ALTERNATIVE: set c=c_flights[flight] in the two plots below (and edgecolor black)
    ax.scatter(obs_lon_values, obs_lat_values, marker='o', s=5, edgecolors='k',label='In-cloud obs.', c='k', transform = data_projection,zorder=2)
    ax.plot(lon_values, lat_values, c='tab:orange',linewidth=10,alpha=1, transform = data_projection, label=f'Flightpath:{flight}',zorder=1)

    
    # add sea ice concentration
    cs = ax.contour(sic_ds['lon'],sic_ds['lat'],sic_ds['sic'], transform=ccrs.PlateCarree(),levels=[25.], colors='tab:red', linestyles='dashed', linewidths=2.5)
    contour_legend = mlines.Line2D([], [], color='tab:red',linestyle='--', linewidth=2.5, label='25% Sea Ice \n concentration')

    #Plot Kiruna 
    ax.plot(lon_kir, lat_kir, marker='^',markersize=16, color='red', transform=data_projection)
    offset_lon = 0.95  # adjust the horizontal offset
    offset_lat = -0.95  # adjust the vertical offset
    ax.text(lon_kir + offset_lon, lat_kir + offset_lat, "Kiruna", fontsize=20, transform=data_projection, ha='right', va='bottom',
            bbox=dict(facecolor='white', alpha=1, edgecolor='black', pad=5))

    # set extent of the plot to the full area covered by the dataset +/- an increment of 1
    ax.set_extent(full_extent)
    ax.gridlines()

    handles, labels = ax.get_legend_handles_labels() # get exisiting labels
    #append with sea ice information
    handles.append(contour_legend)
    date_obj = pd.to_datetime(sic_ds.attrs['date'], format='%Y%m%d')
    labels.append(f'Sea ice edge') #: {date_obj.strftime('%b')} {date_obj.strftime('%d')}')

    plt.legend(handles=handles, labels=labels, loc='lower left', fontsize=11, framealpha=1)

    return c_flights[flight], handles, labels # return the color for the flight to be used in other plots