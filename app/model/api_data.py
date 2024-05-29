
import pandas as pd
import numpy as np
import requests
from datetime import *

#openmeteo imports
import openmeteo_requests

import requests_cache
from retry_requests import retry

numdays = 40 #Number of past days needed to make the prediction

#Setting up start and end days for data fetching
today = date.today() - timedelta(days = 10)
d = timedelta(days = numdays)
start_day = (today - d).strftime("%Y-%m-%d")
end_day = today.strftime("%Y-%m-%d")


#create lags function

def make_lags(ts, lags):
    return pd.concat(
        {
            f'y_lag_{i}': ts.shift(i)
            for i in lags
        },
        axis=1)

# collecting energy data from the last X days, applying transformations and creating features from the data
def get_DK2_energy(numdays = numdays):

    response = requests.get(f"https://api.energidataservice.dk/dataset/ProductionConsumptionSettlement?offset=0&start={start_day}T00:00&end={end_day}T00:00&sort=HourUTC%20DESC")
    data = response.json()
    df = pd.DataFrame(data['records'])

    # selecting the required fields
    DK2= df[df['PriceArea'] == 'DK2']
    DK2_solar =DK2[['HourDK','SolarPowerLt10kW_MWh']]
    DK2_solar

    #changing index to datetime
    DK2_solar["HourDK"]=pd.to_datetime(DK2_solar['HourDK'])
    DK2_solar.set_index("HourDK", inplace=True)

    
    #resampling and fixing any errors in the data
    DK2_solar = DK2_solar[~DK2_solar.index.duplicated(keep='first')]  # Keep first occurrence
    DK2_solar = DK2_solar.resample('H').ffill()
    DK2_solar_daily = DK2_solar['SolarPowerLt10kW_MWh'].resample('D').sum()
    print("pre transformation", DK2_solar_daily, DK2_solar_daily.shape)

    # adding Lag features
    lags = make_lags(DK2_solar_daily, lags=[1,2,3,4,5,6,7,8,15,22,37,40])
    print("lag shape", lags, lags.shape)
    #adding a month feature
    lags["month"]=lags.index.month
    lags = lags.fillna(0.0)

    #merging features
    full_features = lags

    #Standardising the datetime region
    full_features.index = full_features.index.tz_localize('Europe/Berlin')
    full_features.index = full_features.index.normalize()

    return full_features

# collecting weather data from the last X days and transforming it to be added to faetures
def get_weather_data(numdays = numdays):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": 55.6759,
        "longitude": 12.5655,
        "start_date": start_day,
        "end_date": end_day,
        "hourly": ["temperature_2m", "dew_point_2m"],
        "daily": ["daylight_duration", "sunshine_duration", "precipitation_sum", "rain_sum"],
        "timezone": "Europe/Berlin"
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_dew_point_2m = hourly.Variables(1).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["dew_point_2m"] = hourly_dew_point_2m

    hourly_dataframe = pd.DataFrame(data = hourly_data)
    print(hourly_dataframe)

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_daylight_duration = daily.Variables(0).ValuesAsNumpy()
    daily_sunshine_duration = daily.Variables(1).ValuesAsNumpy()
    daily_precipitation_sum = daily.Variables(2).ValuesAsNumpy()
    daily_rain_sum = daily.Variables(3).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
        end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = daily.Interval()),
        inclusive = "left"
    )}
    daily_data["daylight_duration"] = daily_daylight_duration
    daily_data["sunshine_duration"] = daily_sunshine_duration
    daily_data["precipitation_sum"] = daily_precipitation_sum
    daily_data["rain_sum"] = daily_rain_sum

    daily_dataframe = pd.DataFrame(data = daily_data)

    #resampling data to ensure consistency with original features
    daily_dataframe["date"]=pd.to_datetime(daily_dataframe['date'])
    daily_dataframe.set_index("date", inplace=True)
    daily_dataframe = daily_dataframe.resample('H').ffill()

    #standardising the datetime region
    daily_dataframe = daily_dataframe.resample('D').mean()
    daily_dataframe.index = daily_dataframe.index.tz_convert('Europe/Berlin')
    daily_dataframe.index = daily_dataframe.index.normalize()

    return daily_dataframe


def create_sequences(df, time_steps=40):
    Xs = []
    
    for i in range(len(df) - time_steps + 1):
        Xs.append(df.iloc[i:i + time_steps].values)

    Xs = np.array(Xs)

    return Xs

def get_features(numdays = numdays):
    original_features = get_DK2_energy(numdays)
    
    weather_features = get_weather_data(numdays)

    d_X = pd.merge(original_features, weather_features, left_index=True, right_index=True)

    d_X = create_sequences(d_X)

    return d_X