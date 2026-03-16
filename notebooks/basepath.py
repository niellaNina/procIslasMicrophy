import socket
name=socket.gethostname()
if '10f6c923-2d0d0b' in name:
    data_path_base='/mnt/mcc-ns9600k'
elif 'nird' in name:
    data_path_base='/projects/NS9600K/'
elif 'Tims-MacBook' in name:
    data_path_base='/Users/timcar/Documents/data_analysis'