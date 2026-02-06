import os
import xarray as xr
import numpy as np
from scipy.spatial import cKDTree

def step_against_wind(lon, lat, wind_direction, step_distance=32):
    """steps against the wind direction using simple approximation"""

    # Convert step distance from km to degrees based on latitude
    step_lon = step_distance / (111.111 * np.cos(np.radians(lat)))

    new_lon = lon + step_lon * np.sin(np.radians(wind_direction-180))
    new_lat = lat + step_distance / 111.111 * np.cos(np.radians(wind_direction-180))
    return new_lon, new_lat

def step_with_wind(lon, lat, wind_direction, step_distance=32):
    """steps with the wind direction using simple approximation"""

    # Convert step distance from km to degrees based on latitude
    delta_lon = step_distance * np.sin(np.radians(wind_direction)) / (111.111 * np.cos(np.radians(lat)))
    delta_lat = step_distance * np.cos(np.radians(wind_direction)) / 111.111

    new_lon = lon + delta_lon
    new_lat = lat + delta_lat

    return new_lon, new_lat

def get_lon_lat_for_steps_upwind(ds_flight, wind_dir, steps, step_distance):
    """Get lon and lat for each step upwind from flight path"""

    # Find nearest wind direction grid point for each flight point
    time_idx = np.argmin(np.abs(ds_flight.time.values - wind_dir.time.values[:, np.newaxis]), axis=0)
    lon_idx = np.argmin(np.abs(ds_flight.lon.values - wind_dir.lon.values[:, np.newaxis]), axis=0)
    lat_idx = np.argmin(np.abs(ds_flight.lat.values - wind_dir.lat.values[:, np.newaxis]), axis=0)
    wind_dir_flight_at_time = wind_dir[time_idx]
    wind_dir_flight = wind_dir.values[time_idx, lat_idx, lon_idx]

    lon_flight = ds_flight.lon
    lat_flight = ds_flight.lat
    lon_i = lon_flight.values 
    lat_i = lat_flight.values 
    wind_dir_i = wind_dir_flight

    # Initialize lists to store lon and lat at each step
    lons = [lon_i] # Starting point
    lats = [lat_i] # Starting point
    for k in range(steps):
        # One step against the wind direction
        lon_i, lat_i = step_against_wind(lon_i, lat_i, wind_dir_i, step_distance=step_distance)
        lons.append(lon_i)
        lats.append(lat_i)

        # find new wind direction at the new location
        lon_idx = np.argmin(np.abs(lon_i - wind_dir_flight_at_time.lon.values[:, np.newaxis]), axis=0)
        lat_idx = np.argmin(np.abs(lat_i - wind_dir_flight_at_time.lat.values[:, np.newaxis]), axis=0)
        wind_dir_i = wind_dir.values[time_idx, lat_idx, lon_idx]

    # Convert lists to numpy arrays
    lons = np.array(lons)
    lats = np.array(lats)
    return lons, lats

def get_lon_lat_for_steps_downwind(ds_flight, wind_dir, steps, step_distance):
    """Get lon and lat for each step downwind from flight path"""

    # Find nearest wind direction grid point for each flight point
    time_idx = np.argmin(np.abs(ds_flight.time.values - wind_dir.time.values[:, np.newaxis]), axis=0)
    lon_idx = np.argmin(np.abs(ds_flight.lon.values - wind_dir.lon.values[:, np.newaxis]), axis=0)
    lat_idx = np.argmin(np.abs(ds_flight.lat.values - wind_dir.lat.values[:, np.newaxis]), axis=0)
    wind_dir_flight_at_time = wind_dir[time_idx]
    wind_dir_flight = wind_dir.values[time_idx, lat_idx, lon_idx]

    lon_flight = ds_flight.lon
    lat_flight = ds_flight.lat
    lon_i = lon_flight.values 
    lat_i = lat_flight.values 
    wind_dir_i = wind_dir_flight

    # Initialize lists to store lon and lat at each step
    lons = [lon_i]
    lats = [lat_i]
    for k in range(steps):
        # One step with the wind direction
        lon_i, lat_i = step_with_wind(lon_i, lat_i, wind_dir_i, step_distance=step_distance)
        lons.append(lon_i)
        lats.append(lat_i)

        # find new wind direction at the new location
        lon_idx = np.argmin(np.abs(lon_i - wind_dir_flight_at_time.lon.values[:, np.newaxis]), axis=0)
        lat_idx = np.argmin(np.abs(lat_i - wind_dir_flight_at_time.lat.values[:, np.newaxis]), axis=0)
        wind_dir_i = wind_dir.values[time_idx, lat_idx, lon_idx]

    # Convert lists to numpy arrays
    lons = np.array(lons)
    lats = np.array(lats)
    return lons, lats




def save_distance_from_seaice(ds_sea_ice, ds_flight, lons_upwind, lats_upwind, lons_downwind, lats_downwind, step_distance, flight_folder, filename):
    """Saves distance from sea ice to flight dataset for all measurements"""

    # Store true lon values before adjustment for KDTree
    true_lons_upwind = lons_upwind.copy()
    true_lons_downwind = lons_downwind.copy()

    # Adjust longitudes for KDTree calculation
    lons_upwind = lons_upwind * np.cos(np.radians(lats_upwind))
    lons_downwind = lons_downwind * np.cos(np.radians(lats_downwind))

    # Initialize coordinates for KDTree for the sea ice dataset
    lat_seaice = ds_sea_ice['lat'].values
    lon_seaice = ds_sea_ice['lon'].values
    lon_seaice = lon_seaice * np.cos(np.radians(lat_seaice))
    lons_seaice_flat = lon_seaice.flatten()
    lats_seaice_flat = lat_seaice.flatten()
    coords_seaice = np.column_stack((lons_seaice_flat, lats_seaice_flat))

    # Create KDTree for sea ice coordinates
    tree = cKDTree(coords_seaice)

    # Query the KDTree for each point in the flight path steps
    points_upwind = np.column_stack((lons_upwind.flatten(), lats_upwind.flatten()))
    points_downwind = np.column_stack((lons_downwind.flatten(), lats_downwind.flatten()))
    distances, indices_upwind = tree.query(points_upwind)
    distances, indices_downwind = tree.query(points_downwind)

    # Get the sea ice value for the closest match on the original grid
    mask_results_upwind = ds_sea_ice.values.flatten()[indices_upwind].reshape(lons_upwind.shape)
    mask_results_downwind = ds_sea_ice.values.flatten()[indices_downwind].reshape(lons_downwind.shape)

    # Find the first index where sea ice dataset is true (along the steps)
    first_true_index_upwind = np.argmax(mask_results_upwind, axis=0)

    # Find the first index where sea ice dataset is not true (along the steps)
    first_true_index_downwind = np.argmax(~mask_results_downwind, axis=0)

    # Use first downwind step to hit ocean if original point over sea ice else first upwind to hit sea ice
    first_true_index_final = np.where(first_true_index_upwind==0, -first_true_index_downwind, first_true_index_upwind)
    distance_from_ice = np.where(np.all(mask_results_upwind == False, axis=0), np.nan, first_true_index_final*step_distance)

    # Save distance from ice and step coordinates to flight dataset
    ds_flight["distance_from_ice"] = xr.DataArray(distance_from_ice, dims=["time"], coords={"time": ds_flight.time})
    ds_flight["distance_from_ice"].attrs["units"] = "km"
    ds_flight["lon_step_upwind"] = xr.DataArray(true_lons_upwind, dims=["step", "time"], coords={"time": ds_flight.time})
    ds_flight["lat_step_upwind"] = xr.DataArray(lats_upwind, dims=["step", "time"], coords={"time": ds_flight.time})
    ds_flight["lon_step_downwind"] = xr.DataArray(true_lons_downwind, dims=["step", "time"], coords={"time": ds_flight.time})
    ds_flight["lat_step_downwind"] = xr.DataArray(lats_downwind, dims=["step", "time"], coords={"time": ds_flight.time})

    ds_flight.to_netcdf(flight_folder + "with_distance_from_ice/" + filename)


def main():
    step_distance = 25 # distance between each step in km
    steps = 200 # number of steps upwind and downwind
    sea_ice_threshold = 0.2 # threshold for sea ice concentration to consider as sea ice
    sea_ice_lon_lat = xr.open_dataset(f"/uio/kant/geo-geofag-u1/fslippe/data/land_sea_ice_mask/nimbus/with_lonlat/NSIDC0051_SEAICE_PS_N25km_20200302_v2.0.nc")
    merra_folder = "/mn/vann/fslippe/MERRA/" # path to MERRA-2 data
    flight_folder = "/scratch/fslippe/CAO_flights/" # path to flight data
    files = [f for f in os.listdir(flight_folder) if f.endswith(".nc")]

    for filename in files:
        print(filename)
        # load flight and sea ice data
        ds_flight = xr.open_dataset(f"{flight_folder}{filename}")
        date_of_flight = str(ds_flight.time[0].values)[:10].replace("-", "")
        ds_sea_ice = xr.open_dataset(f"/uio/kant/geo-geofag-u1/fslippe/data/land_sea_ice_mask/nimbus/NSIDC0051_SEAICE_PS_N25km_{date_of_flight}_v2.0.nc").isel(time=0).F17_ICECON
        
        # assign lon and lat coordinates
        ds_sea_ice["lon"] = sea_ice_lon_lat["lon"] 
        ds_sea_ice["lat"] = sea_ice_lon_lat["lat"]

        # create sea ice mask
        sea_ice_wo_land = ((ds_sea_ice >sea_ice_threshold) & (ds_sea_ice<=1)) # sea ice mask without land
        sea_ice_land = ((ds_sea_ice>1.01) & (ds_sea_ice.lat>=75)) # consider land north of 75N (i.e. Svalbard)
        east_of_50 = ((ds_sea_ice>1.01) & (ds_sea_ice.lon>=50)) # consider land east of 50E (i.e. Novaya Zemlya)
        ds_sea_ice =( sea_ice_wo_land | sea_ice_land | east_of_50) # total sea ice mask

        # load wind data and calculate wind direction
        ds_wind = xr.open_dataset(f"{merra_folder}/{date_of_flight[:4]}/MERRA2_400.tavg1_2d_slv_Nx.{date_of_flight}.SUB.nc")
        ds_wind["wind_dir"] = np.degrees(np.arctan2(ds_wind.U10M, ds_wind.V10M))
        ds_wind["wind_dir"] = (ds_wind["wind_dir"] + 360) % 360
        wind_dir = ds_wind.wind_dir

        # get lon and lat for each step upwind and downwind
        lons_upwind, lats_upwind = get_lon_lat_for_steps_upwind(ds_flight, wind_dir, steps, step_distance)
        lons_downwind, lats_downwind = get_lon_lat_for_steps_downwind(ds_flight, wind_dir, steps, step_distance)

        # save distance from sea ice to flight dataset
        save_distance_from_seaice(ds_sea_ice, ds_flight, lons_upwind, lats_upwind, lons_downwind, lats_downwind, step_distance, flight_folder, filename)

if __name__ == "__main__":
    main() 

