#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 26 08:44:27 2024

@author: ninalar
"""

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
    result = algo.predict(pen=30)       # returns rows where the changes are detected,
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
    plt.gcf().axes[0].xaxis.set_major_formatter(xformatter)