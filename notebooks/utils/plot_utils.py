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
    

   # coordinates of Kiruna
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


def plot_flight_obs(ds, ds_incloud, sic_max_ds,sic_min_ds, obs,ax=None, lat_bands='',title='', savefile = ''):
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
    if ax==None:
        fig = plt.figure(figsize=(15, 10))
        gs = GridSpec(1, 2, figure=fig)
        ax = fig.add_subplot(gs[0,0], projection=ccrs.NorthPolarStereo())

    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.BORDERS, linewidth=2)
    data_projection = ccrs.PlateCarree()

    # get the flightids
    flights = np.unique(ds.islasid.values)

    handles = [] # empty handles list
    labels = [] # empty labels list
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
            ax.scatter(obs_lon_values, obs_lat_values, marker='o',label=flight, c= c_flights[flight], alpha = 0.7, transform = data_projection)
        else:
            ax.scatter(lon_values, lat_values, marker='.', c=c_flights[flight], s = 30, alpha = 0.05, transform = data_projection, label = flight)

        #create linehandle proxy
        line_proxy = mlines.Line2D([0],[0], color = c_flights[flight], linestyle='-', linewidth=5, label=flight)
        handles.append(line_proxy)
        labels.append(flight)

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

    #handles, labels = ax.get_legend_handles_labels() # get exisiting labels
    title_proxy = Rectangle((0,0), 0, 0, color='w') # create second "title"
    # append handles and labels with new title
    handles.append(title_proxy)
    labels.append('Sea ice edge:')
    #append with sea ice information
    handles.append(contour_legend_max)
    max_date_obj = pd.to_datetime(sic_max_ds.attrs['date'], format='%Y%m%d')
    labels.append(f"Max: {max_date_obj.strftime('%b')} {max_date_obj.strftime('%d')}")
    handles.append(contour_legend_min)
    min_date_obj = pd.to_datetime(sic_min_ds.attrs['date'], format='%Y%m%d')
    labels.append(f"Min: {min_date_obj.strftime('%b')} {min_date_obj.strftime('%d')}")

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

# General function to create the heatmaps the heatmap plots
def plot_heatmap_ax(dist_df, labels_dict, ax, mask_na=False, val=0, annot_df = False,counts=False,col='Blue',ncol=6,ss=10,ticks="",reverse=False, v_extend=False, add_sections=False, altitude_bins="", temp_bins=""):
    # General function to create the heatmaps for article
    # REQUIRES: 
    #   -- matplotlib
    #   -- seaborn
    #   -- pandas
    # INPUT: 
    #   -- dist_df: dataframe to create the heatmap from
    #   -- labels_dict: dictionary containing labels for {xax_lab, yax_lab, cbar_lab}
    #   -- ax: axis to add the plot
    #   -- mask_na(DEFAULT:False): boolean, whether or not the nan values should be masked in the annotation
    #   -- val: number of digits in annotation
    #   -- annot_df (OPTIONAL): df of equal size of dist_df to use for annotating the cells in the heatmap
    #   -- counts (OPTIONAL): set 0 values to white
    #   -- col(OPTIONAL): color to use in plot, either "Blue", "Grey" or custom color palette
    #   -- ncol (OPTIONAL): number of discrete color values (default=6)
    #   -- ss(OPTIONAL): text size of plot (default=10)
    #   -- ticks(OPTIONAL): Array of values to use as ticks on colorbar. if empty ncol and max/min of data is used to set ticks
    #   -- v_extend(OPTIONAL): max value for colorbar

    # required functions
    import seaborn as sns
    import matplotlib.colors as mcolors
    import matplotlib.pyplot as plt
    import numpy as np
    
    # Set up plot options
    plt.rcParams.update({'font.size':ss}) # set global font size


    xax_lab = labels_dict['xax_lab'] # Get labels from dictionary
    yax_lab = labels_dict['yax_lab']
    cbar_lab = labels_dict['cbar_lab']    
    
    # Set colorpalette based on input
    # default = Blue
    if col=="Grey":
        cmap=sns.cubehelix_palette(ncol, hue=0, dark=.25, as_cmap=True)
    elif col=="Blue":
        cmap=sns.cubehelix_palette(ncol, rot=-.15, dark=.25, as_cmap=True)
    else:
        cmap = col

    if reverse==True:
        cmap=cmap.reversed()

    # handling of cbar values depending on whether specific ticks are given
    if isinstance(ticks,np.ndarray):
        # if an array is given as ticks, extract max and min from array
        ticks = ticks
        minv=ticks[0]
        maxv=ticks[-1]

    else:
        # ticks are not specificly set
        minv=0
        # get max for colorbar
        if v_extend:
            maxv = v_extend # if vextend exists use vextend as max
        else:
            maxv=np.nanmax(dist_df.values) # else use max of values
        
        col_bins = maxv/ncol # find the size of each colorbin based on max value and number of colors
        ticks = np.arange(minv, maxv + col_bins, col_bins) # get ticks for cbar

    

    
    # Set format of the values
    if abs(np.nanmax(dist_df.values))<1:
        format='%.2f' # if values less than 1, two digits
    else:
        format='%.0f' # else none
    
    # fix parts to make 0 white in some of the plots
    if counts==True:
        minv=1
    

    # set normalization of colorbar
    norm = mcolors.BoundaryNorm(ticks, cmap.N)

    # set location of colorbar
    loc = 'right' #'left'

    # Plot the heatmap with different settings
    if mask_na:
        # Mask away NA values
        nan_mask = dist_df.isna() # mask nan values for annotation
        
        if v_extend:
            # when the v_extend value should be used as the max
            if v_extend<np.nanmax(dist_df.values):
                if isinstance(annot_df, list):
                    # if more than one annotation, only relevant for one plot that fits these other parameteters
                    perc_annot_df = annot_df[1]
                    annot_df = annot_df[0]
                    pl = sns.heatmap(dist_df, annot=annot_df, fmt="", cmap=cmap,norm=norm, vmin= minv, vmax=v_extend,  mask=nan_mask, ax=ax, 
                        cbar_kws={"location" : loc, 'extend':'max','ticks':ticks, 'format':format, 'label':cbar_lab},
                        linewidths=0.5, annot_kws={'size':ss,'ha':'right'})
                    pl = sns.heatmap(dist_df, annot=perc_annot_df, fmt="", cmap=cmap,norm=norm, vmin= minv, vmax=v_extend,  mask=nan_mask, ax=ax, 
                        cbar=False,
                        linewidths=0.5, annot_kws={'size':ss,'ha':'left'})
                else:
                    pl = sns.heatmap(dist_df, annot=annot_df, fmt=f".{val}f", cmap=cmap,norm=norm, vmin= minv, vmax=v_extend,  mask=nan_mask, ax=ax, 
                        cbar_kws={"location" : loc, 'extend':'max','ticks':ticks, 'format':format, 'label':cbar_lab},
                        linewidths=0.5, annot_kws={'size':ss})

            else:
                pl = sns.heatmap(dist_df, annot=annot_df, fmt=f".{val}f", cmap=cmap, norm=norm,vmin= minv, vmax=v_extend,  mask=nan_mask, ax=ax, 
                    cbar_kws={"location" : loc,'ticks':ticks, 'format':format,'label':cbar_lab},
                    linewidths=0.5, annot_kws={'size':ss})
        else:
            pl = sns.heatmap(dist_df, annot=annot_df, fmt=f".{val}f", cmap=cmap,norm=norm,vmin=minv, mask=nan_mask, ax=ax, 
                cbar_kws={"location" : loc,'ticks':ticks, 'format':format,'label':cbar_lab},
                linewidths=0.5, annot_kws={'size':ss})
    else:
       if v_extend:
            if v_extend<np.nanmax(dist_df.values):
                pl = sns.heatmap(dist_df, annot=annot_df, fmt=f".{val}f", cmap=cmap,norm=norm, vmin= minv, vmax=v_extend, ax=ax, 
                    cbar_kws={"location" : loc, 'extend':'max','ticks':ticks, 'format':format,'label':cbar_lab},
                    linewidths=0.5, annot_kws={'size':ss})
            else:
                pl = sns.heatmap(dist_df, annot=annot_df, fmt=f".{val}f", cmap=cmap,norm=norm, vmin= minv, vmax=v_extend, ax=ax, 
                    cbar_kws={"location" : loc,'ticks':ticks, 'format':format,'label':cbar_lab},
                    linewidths=0.5, annot_kws={'size':ss})
       else:
           pl = sns.heatmap(dist_df, annot=annot_df, fmt=".0f", cmap=cmap,norm=norm,vmin=minv, ax=ax, 
                cbar_kws={"location" : loc,'ticks':ticks, 'format':format,'label':cbar_lab},
                linewidths=0.5, annot_kws={'size':ss})


    pl.set_xlabel(xax_lab, fontsize=ss) # set plot labels
    pl.set_ylabel(yax_lab, fontsize=ss)

    # colorbar options
    cax=pl.figure.axes[-1]
    cax.tick_params(labelsize=ss)  # Change the size of the colorbar ticks

    # tick adjustment
    # add last tick
    ncols = len(dist_df.columns)

    # Shift the x-ticks to the left edge of each cell
    new_x_ticks = np.arange(ncols + 1)  # Get new x-tick positions to align with the left edge of cells
    old_labels = [t.get_text() for t in pl.get_xticklabels()]
    labels = old_labels + ['1000']  

    pl.set_xticks(new_x_ticks)  # Set new ticks at the left side of cells
    pl.set_xticklabels(labels,fontsize=ss)  # Reuse the old labels

    # remove any decimals in the ytick label texts
    new_y_ticks = np.arange(len(dist_df))  # Get new x-tick positions to align with the left edge of cells
    pl.set_yticks(new_y_ticks)  # Set new ticks at the left side of cells

    # Set labels for y-axes based on temp or altitude
    if dist_df.index.name=='altitude_bin':
        y_labels=altitude_bins[1:len(dist_df)+1][::-1].astype(int)
        pl.set_yticklabels(y_labels,fontsize=ss, rotation=0)
    elif dist_df.index.name=='temp_bin':
        y_labels=temp_bins
        pl.set_yticklabels(y_labels,fontsize=ss, rotation=0)


    
    return 