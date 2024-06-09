import netCDF4 as nc
import json
import numpy as np
import json
import os
import sys
from datetime import date, datetime, timedelta

data_directory = "./data/" #shoudl end with /
sys.path.append(os.path.join(os.path.dirname(__file__), './import_functions'))


def get_station_settings(station_id):
    with open('static/config/fixed_stations.json') as f:
        stations = json.load(f)
        station = next((s for s in stations if s['id'] == station_id), None)
        
        return station

def get_url(url, date):
    return date.strftime(url)



def netcdf_lighthouse(url, variables, duration, station_id):
    try:
        try:
            dataset = nc.Dataset(get_url(url, date.today()))
        except:
            dataset = nc.Dataset(get_url(url, date.today() - timedelta(1)))
        
        #print(get_url(url, date.today()))

        times = dataset.variables['time'][:]
        
        current_time = times[-1]
        time_frame = current_time - duration * 3600
        mask = times >= time_frame

        station = get_station_settings(station_id)

        file_path = data_directory + station_id + "_" + str(duration) + "_" + str(current_time) + ".json"

        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
            
        else:
            data_points = []
            for i in range(len(times)):
                try:
                    if not mask[i]:
                        continue
                    data_point = {
                        'time': float(times[i]),
                        'lat': float(station['lat']),
                        'lon': float(station['lon']),
                        'airTemperature': float(dataset.variables[variables.get('airTemperature')][i]) if variables.get('airTemperature') else None,
                        'seaSurfaceTemperature': float(dataset.variables[variables.get('seaSurfaceTemperature')][i]) if variables.get('seaSurfaceTemperature') else None,
                        'windSpeed': float(dataset.variables[variables.get('windSpeed')][i]) if variables.get('windSpeed') else None,
                        'windDirection': float(dataset.variables[variables.get('windDirection')][i]) if variables.get('windDirection') else None,
                        'relativeHumidity': float(dataset.variables[variables.get('relativeHumidity')][i]) if variables.get('relativeHumidity') else None,
                    }


                    # Replace NaN with None
                    for key, value in data_point.items():
                        if isinstance(value, float) and np.isnan(value):
                            data_point[key] = None
                    #print(data_point)
                    data_points.append(data_point)

                except Exception as e:
                    print(f"Error processing data point at index {i}: {e}")
                    continue

            if not data_points:
                raise ValueError("No data points found within the specified timeframe.")

            latest_data = data_points[-1]
            track = [{'lat': dp['lat'], 'lon': dp['lon'], 'variable': dp} for dp in data_points]

            data_ready = {
                'lat': latest_data['lat'],
                'lon': latest_data['lon'],
                'windSpeed': latest_data['windSpeed'],
                'windDirection': latest_data['windDirection'],
                'track': track,
                'latest': latest_data  # Add latest data for the popup
            }

            with open(file_path, 'w') as f:
                json.dump(data_ready, f)
            
            return data_ready

    except Exception as e:
        print(f"Error processing NetCDF file: {e}")
        return None