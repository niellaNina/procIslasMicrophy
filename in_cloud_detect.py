#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 26 08:44:27 2024

@author: ninalar
"""
def detect_by_limit(limit):
    test = limit

def detect_from_report(nav_df, report_cloud_df):
    import numpy as np
    import pandas as pd
    
    # find time in cloud
    flight = 'as220008' # testing with one flight. Some flights does not have accurate cloud in cloud out listings in flight report

    cloud_df = []


    # select nav data from flight
    nav_test = nav_df[nav_df['flightid']==flight]
    # select data from cloud_report
    cloud_test = report_cloud_df[report_cloud_df['flightid']==flight]

    if cloud_test['title'].iloc[0]=='cloud_in': #check if the first entry is going into a cloud
        for i, g in cloud_test.groupby(np.arange(len(cloud_test)) // 2):
            cloud = i
            cloud_in = g['date'].iloc[0],
            cloud_out = g['date'].iloc[1],
            total_cloud_time = g['date'].iloc[1]-g['date'].iloc[0],
            
            df =  pd.DataFrame({'cloud#': [cloud],
                                'cloud_in': cloud_in[0],
                                'cloud_out': cloud_out[0],
                                'total_cloud_time': total_cloud_time[0],
                                'flightid': flight
                                    })
            cloud_df.append(df)
            
    else:
        print('Did you start the flight in a cloud?')

    # concatenate all the flight dataframes in the list to a new dataframe containing all flights
    cloud_df = pd.concat(cloud_df)

def all_detect(df,var):
    # Function to detect changepoints in a dataset (using ruptures)
    # Input: 
        # df: dataframe of one or more variables, and the flights
        # var: name of column/variable to use
        
    #import pandas as pd
    #import numpy as np
    import matplotlib.pyplot as plt
    import ruptures as rpt
    import matplotlib.dates as mdates

    xformatter = mdates.DateFormatter('%H:%M') # define a formatter for only showing the time of a datetime object              
                          
    # --Facet over all the fligths
    # --initialize faceting
    group_values = list(df['flightid'].unique()) #group on flightid
    # set number of columns in the plot
    ncols=3
    #calculate number of rows in the plot
    nrows = len(group_values) // ncols + (len(group_values) % ncols > 0)

    # -- define the plot
    plt.figure(figsize = (9,9))
    plt.subplots_adjust(hspace=0.5, wspace=0.5)
    plt.suptitle(f'Changeplots of {var}', fontsize = 16, y=0.95)

    # go through each flight
    for n, col in enumerate(group_values):
        # add a new subplot at each iteration using nrows and cols
        ax = plt.subplot(nrows, ncols, n + 1)
         
        # Filter the dataframe for each flight
        flight_df = df[df["flightid"]==col]
        
        # set up ruptures algoritm to find change points
        algo = rpt.Pelt(model='rbf').fit(flight_df[var].values)
        result = algo.predict(pen=30)       # returns rows where the changes are detected,
                                            # Penalty decides the sensitivity of the algoritm
                                            # high number detects less points, low number detects more
        ax.plot(flight_df[var], color = 'tab:red')
        for r in result:
            ax.axvline(x=r, color='k', linestyle='--')
            
        # chart formatting and anotations
        ax.set_ylabel(f'{var}')
        ax.set_xlabel('timesteps (s)')
        ax.set_title(col)
        plt.gcf().axes[0].xaxis.set_major_formatter(xformatter)
        
def single_detect(df,var,flight):
    # Function to detect changepoints in a dataset (using ruptures)
    # Input: 
        # df: dataframe of one or more variables, and the flights
        # var: name of column/variable to use
        
    #import pandas as pd
    #import numpy as np
    import matplotlib.pyplot as plt
    import ruptures as rpt
    import matplotlib.dates as mdates

    xformatter = mdates.DateFormatter('%H:%M') # define a formatter for only showing the time of a datetime object              
     
    # Filter the dataframe for each flight
    flight_df = df[df["flightid"]==flight]
        
    # set up ruptures algoritm to find change points
    algo = rpt.Pelt(model='rbf').fit(flight_df[var].values)
    result = algo.predict(pen=20)       # returns rows where the changes are detected,
                                        # Penalty decides the sensitivity of the algoritm
                                        # high number detects less points, low number detects more
    # define the plot
    fig, ax = plt.subplots()
    ax.plot(flight_df[var], color = 'tab:red')
    for r in result:
        ax.axvline(x=r, color='k', linestyle='--')
            
    # chart formatting and anotations
    ax.set_ylabel(f'{var}')
    ax.set_xlabel('timesteps (s)')
    ax.set_title(f'Changeplots of {var} on flight {flight}')
    #plt.gcf().axes[0].xaxis.set_major_formatter(xformatter)
    
    return(result)