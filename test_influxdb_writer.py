#!/usr/bin/env python3

import unittest
# from unittest.mock import Mock  # unused import, patch
from influxdb_writer import InfluxDBWriter
from config_manager import MeasurementConfig


class TestInfluxDBWriter(unittest.TestCase):
    """Unit tests for InfluxDBWriter class."""

    @patch('influxdb_writer.InfluxDBClient')
    def setUp(self, mock_client):
        """Set up test fixtures."""
        self.writer = InfluxDBWriter(
            url="http://localhost:8086",
            username="test_user",
            password="test_pass",
            database="test_db"
        )
        self.mock_client = mock_client.return_value

    def test_url_parsing_valid(self):
        """Test valid URL parsing."""
        with patch('influxdb_writer.InfluxDBClient') as mock_client:
            writer = InfluxDBWriter(
                url="http://influxdb.example.com:8087",
                username="user",
                password="pass",
                database="db"
            )
            mock_client.assert_called_once_with(
                host="influxdb.example.com",
                port=8087,
                username="user",
                password="pass",
                database="db"
            )

    def test_url_parsing_default_port(self):
        """Test URL parsing with default port."""
        with patch('influxdb_writer.InfluxDBClient') as mock_client:
            writer = InfluxDBWriter(
                url="http://localhost",
                username="user",
                password="pass",
                database="db"
            )
            mock_client.assert_called_once_with(
                host="localhost",
                port=8086,  # Default port
                username="user",
                password="pass",
                database="db"
            )

    def test_url_parsing_invalid(self):
        """Test invalid URL handling."""
        with self.assertRaises(ValueError):
            InfluxDBWriter(
                url="invalid-url",
                username="user",
                password="pass",
                database="db"
            )

    def test_get_measurement_category(self):
        """Test measurement category determination."""
        self.assertEqual(
            self.writer.get_measurement_category('HKQuantityTypeIdentifierHeartRate'),
            'vitals'
        )
        self.assertEqual(
            self.writer.get_measurement_category('HKWorkoutTypeIdentifier'),
            'activity'
        )
        self.assertEqual(
            self.writer.get_measurement_category('HKCategoryTypeIdentifierSleepAnalysis'),
            'sleep'
        )
        self.assertEqual(
            self.writer.get_measurement_category('UnknownType'),
            'other'
        )

    def test_prepare_point_heart_rate(self):
        """Test preparing heart rate data point."""
        data_point = {
            'type': 'HKQuantityTypeIdentifierHeartRate',
            'time': '2024-01-15T10:30:00+00:00',
            'fields': {'value': 72.0},
            'tags': {
                'device': 'Apple Watch',
                'source': 'Health',
                'motion_context': '1'
            }
        }

        result = self.writer.prepare_point(data_point)

        self.assertEqual(result['measurement'], 'heartrate_bpm')
        self.assertEqual(result['fields']['heart_rate'], 72.0)
        self.assertEqual(result['tags']['motion_context'], '1')
        self.assertEqual(result['tags']['device'], 'Apple Watch')

    def test_prepare_point_workout(self):
        """Test preparing workout data point."""
        data_point = {
            'type': 'HKWorkoutTypeIdentifier',
            'time': '2024-01-15T10:00:00+00:00',
            'fields': {'value': 300.0, 'duration': 1800.0, 'distance': 5000.0},
            'tags': {
                'activity_type': 'HKWorkoutActivityTypeRunning',
                'source': 'Apple Watch'
            }
        }

        result = self.writer.prepare_point(data_point)

        self.assertEqual(result['measurement'], 'energy_kcal')
        self.assertEqual(result['fields']['value'], 300.0)
        self.assertEqual(result['fields']['duration'], 1800.0)
        self.assertEqual(result['tags']['activity_type'], 'HKWorkoutActivityTypeRunning')

    def test_write_point_success(self):
        """Test successful data point writing."""
        self.mock_client.write_points.return_value = True

        data_point = {
            'type': 'HKQuantityTypeIdentifierHeartRate',
            'time': '2024-01-15T10:30:00+00:00',
            'fields': {'value': 72.0},
            'tags': {'source': 'Health'}
        }

        result = self.writer.write_point(data_point)

        self.assertTrue(result)
        self.mock_client.write_points.assert_called_once()

    def test_write_point_failure(self):
        """Test data point writing failure."""
        self.mock_client.write_points.side_effect = Exception("Connection error")

        data_point = {
            'type': 'HKQuantityTypeIdentifierHeartRate',
            'time': '2024-01-15T10:30:00+00:00',
            'fields': {'value': 72.0},
            'tags': {}
        }

        result = self.writer.write_point(data_point)

        self.assertFalse(result)

    def test_measurement_config_dataclass(self):
        """Test MeasurementConfig dataclass."""
        config = MeasurementConfig(
            description='Test measurement',
            types=['type1', 'type2'],
            measurement_name='test_measurement',
            fields={'field1': 'mapped1'},
            tags=['tag1', 'tag2'],
            validation={'min_value': 0, 'max_value': 100}
        )

        self.assertEqual(config.types, ['type1', 'type2'])
        self.assertEqual(config.measurement_name, 'test_measurement')
        self.assertEqual(config.fields, {'field1': 'mapped1'})


if __name__ == '__main__':
    unittest.main()
