import sys
import os

# Dynamically add the root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
import logging
from unittest.mock import patch, mock_open
from source.datasource.datasource import DataSource
import pandas as pd


# Concrete subclass for testing
class MockDataSource(DataSource):
    def fetch_station_data(self, station_id):
        return {"id": station_id, "name": "Test Station"}

    def fetch_realtime_data(self, station_id):
        return {"station_id": station_id, "temperature": 25.5}

    def fetch_timeseries_data(self, station_id, start_time, end_time):
        return {"station_id": station_id, "start_time": start_time, "end_time": end_time, "data": []}

    def transform_realtime_data(self, raw_data, station_id):
        return {"station_id": station_id, "processed_temperature": raw_data.get("temperature")}

    def transform_timeseries_data(self, raw_data, station_id):
        return {"station_id": station_id, "processed_data": raw_data.get("data")}

    def is_station_online(self, station_id):
        return True if station_id == "123" else False


# Fixtures
@pytest.fixture
def data_source():
    """Fixture to create an instance of MockDataSource."""
    return MockDataSource(api_key="test_api_key")


# Tests
def test_initialization(data_source):
    """Test initialization of DataSource."""
    assert data_source.api_key == "test_api_key"
    assert isinstance(data_source.logger, logging.Logger)


def test_fetch_station_data(data_source):
    """Test fetch_station_data method."""
    result = data_source.fetch_station_data("123")
    assert result == {"id": "123", "name": "Test Station"}


def test_fetch_realtime_data(data_source):
    """Test fetch_realtime_data method."""
    result = data_source.fetch_realtime_data("123")
    assert result == {"station_id": "123", "temperature": 25.5}


def test_fetch_timeseries_data(data_source):
    """Test fetch_timeseries_data method."""
    result = data_source.fetch_timeseries_data("123", "2023-01-01T00:00:00Z", "2023-01-02T00:00:00Z")
    assert result == {
        "station_id": "123",
        "start_time": "2023-01-01T00:00:00Z",
        "end_time": "2023-01-02T00:00:00Z",
        "data": [],
    }


def test_transform_realtime_data(data_source):
    """Test transform_realtime_data method."""
    raw_data = {"temperature": 25.5}
    result = data_source.transform_realtime_data(raw_data, "123")
    assert result == {"station_id": "123", "processed_temperature": 25.5}


def test_transform_timeseries_data(data_source):
    """Test transform_timeseries_data method."""
    raw_data = {"data": [1, 2, 3]}
    result = data_source.transform_timeseries_data(raw_data, "123")
    assert result == {"station_id": "123", "processed_data": [1, 2, 3]}


def test_is_station_online(data_source):
    """Test is_station_online method."""
    assert data_source.is_station_online("123") is True
    assert data_source.is_station_online("999") is False


@patch.object(logging.Logger, "error")
def test_handle_error(mock_error, data_source):
    """Test _handle_error method."""
    error = Exception("Test error")
    data_source._handle_error(error)
    mock_error.assert_called_once_with("Error occurred: Test error")


# Test for df_to_timeserie method
def test_df_to_timeserie(data_source):
    """Test conversion of DataFrame to time series observations."""
    # Create a sample DataFrame
    data = {
        'timestamp': pd.to_datetime(['2025-02-08T17:00:00.000', '2025-02-08T18:00:00.000']),
        'airTemperature': [-5.4, -5.8],
        'windDirection': [205, 205],
        'windSpeed': [7.1, 6.1]
    }
    df = pd.DataFrame(data).set_index('timestamp')

    # Call the method
    result = data_source.df_to_timeserie(df)

    # Expected result
    expected_result = [
        {
            "airTemperature": -5.4,
            "timestamp": "2025-02-08T17:00:00.000Z",
            "windDirection": 205,
            "windSpeed": 7.1
        },
        {
            "airTemperature": -5.8,
            "timestamp": "2025-02-08T18:00:00.000Z",
            "windDirection": 205,
            "windSpeed": 6.1
        }
    ]

    # Assert the result
    assert result == expected_result

# Test for handling latitude and longitude
def test_df_to_timeserie_with_location(data_source):
    """Test conversion of DataFrame with latitude and longitude to time series observations."""
    # Create a sample DataFrame with location data
    data = {
        'timestamp': pd.to_datetime(['2025-02-08T17:00:00.000', '2025-02-08T18:00:00.000']),
        'airTemperature': [-5.4, -5.8],
        'windDirection': [205, 205],
        'windSpeed': [7.1, 6.1],
        'latitude': [48.8566, 48.8566],
        'longitude': [2.3522, 2.3522]
    }
    df = pd.DataFrame(data).set_index('timestamp')

    # Call the method
    result = data_source.df_to_timeserie(df)

    # Expected result
    expected_result = [
        {
            "airTemperature": -5.4,
            "timestamp": "2025-02-08T17:00:00.000Z",
            "windDirection": 205,
            "windSpeed": 7.1,
            "location": {"lat": 48.8566, "lon": 2.3522}
        },
        {
            "airTemperature": -5.8,
            "timestamp": "2025-02-08T18:00:00.000Z",
            "windDirection": 205,
            "windSpeed": 6.1,
            "location": {"lat": 48.8566, "lon": 2.3522}
        }
    ]

    # Assert the result
    assert result == expected_result

# Test for error handling
@patch.object(DataSource, '_handle_error')
def test_df_to_timeserie_error_handling(mock_handle_error, data_source):
    """Test error handling in df_to_timeserie method."""
    # Create an invalid DataFrame (e.g., non-numeric data)
    data = {
        'timestamp': pd.to_datetime(['2025-02-08T17:00:00.000', '2025-02-08T18:00:00.000']),
        'airTemperature': [-5.4, 'invalid_value'],
        'windDirection': [205, 205],
        'windSpeed': [7.1, 6.1]
    }
    df = pd.DataFrame(data).set_index('timestamp')

    # Call the method
    result = data_source.df_to_timeserie(df)

    # Assert that _handle_error was called and the result is None
    mock_handle_error.assert_called_once()
    assert result is None