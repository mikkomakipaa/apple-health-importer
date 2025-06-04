from influxdb import InfluxDBClient
from typing import Dict, List
import logging

class InfluxDBWriter:
    # Unit conversion mappings
    UNIT_CONVERSIONS = {
        'count/min': 'bpm',
        'count': 'count',
        'kcal': 'kcal',
        'km': 'm',
        'min': 's',
        's': 's'
    }

    # Measurement configurations
    MEASUREMENTS = {
        'vitals': {
            'types': ['HKQuantityTypeIdentifierHeartRate'],
            'fields': {
                'value': 'value',
                'heart_rate': 'heart_rate_bpm'
            }
        },
        'activity': {
            'types': [
                'HKQuantityTypeIdentifierStepCount',
                'HKQuantityTypeIdentifierActiveEnergyBurned',
                'HKWorkoutTypeIdentifier'
            ],
            'fields': {
                'steps': 'count',
                'energy': 'energy_kcal',
                'distance': 'distance_m',
                'duration': 'duration_s'
            }
        },
        'sleep': {
            'types': ['HKCategoryTypeIdentifierSleepAnalysis'],
            'fields': {
                'duration': 'duration_min',
                'quality': 'quality_score'
            }
        }
    }

    def __init__(self, url: str, username: str, password: str, database: str):
        # Parse host and port from URL
        host = url.split('://')[1].split(':')[0]
        port = int(url.split(':')[-1])
        
        self.client = InfluxDBClient(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database
        )
        
    def convert_unit(self, value: float, from_unit: str, to_unit: str = None) -> float:
        """Convert value from one unit to another."""
        if not to_unit:
            to_unit = self.UNIT_CONVERSIONS.get(from_unit, from_unit)
        
        if from_unit == to_unit:
            return value
            
        # Convert km to m
        if from_unit == 'km' and to_unit == 'm':
            return value * 1000
            
        # Convert min to s
        if from_unit == 'min' and to_unit == 's':
            return value * 60
            
        return value

    def get_measurement_category(self, data_type: str) -> str:
        """Determine the measurement category for a given data type."""
        for category, config in self.MEASUREMENTS.items():
            if data_type in config['types']:
                return category
        return 'other'

    def prepare_point(self, data_point: Dict) -> Dict:
        """Prepare data point with proper field names and unit conversions."""
        data_type = data_point.get('type', '')
        category = self.get_measurement_category(data_type)
        measurement = f'apple_health_{category}'

        point = {
            "measurement": measurement,
            "time": data_point['time'],
            "tags": {
                "type": data_type,
                "device": data_point.get('tags', {}).get('device', ''),
                "source": data_point.get('tags', {}).get('source', '')
            },
            "fields": {}
        }

        # Add activity-specific tags
        if category == 'activity' and 'activity_type' in data_point.get('tags', {}):
            point['tags']['activity_type'] = data_point['tags']['activity_type']

        # Add motion context as a tag for heart rate
        if data_type == 'HKQuantityTypeIdentifierHeartRate':
            motion_context = data_point.get('fields', {}).get('motion_context')
            if motion_context is not None:
                point['tags']['motion_context'] = str(motion_context)

        # Convert and add fields
        fields_config = self.MEASUREMENTS[category]['fields']
        for field_name, value in data_point.get('fields', {}).items():
            if field_name in fields_config:
                unit = data_point.get('units', {}).get(field_name, '')
                converted_value = self.convert_unit(value, unit)
                point['fields'][fields_config[field_name]] = converted_value

        return point

    def write_point(self, data_point: Dict) -> bool:
        """Write a single data point to InfluxDB."""
        try:
            point = self.prepare_point(data_point)
            self.client.write_points([point])
            return True
            
        except Exception as e:
            logging.error(f"Error writing to InfluxDB: {e}")
            return False
            
    def write_points(self, data_points: List[Dict]) -> int:
        """Write multiple data points to InfluxDB.
        Returns the number of successfully written points."""
        success_count = 0
        for point in data_points:
            if self.write_point(point):
                success_count += 1
        return success_count
        
    def close(self):
        """Close the InfluxDB client connection."""
        self.client.close() 