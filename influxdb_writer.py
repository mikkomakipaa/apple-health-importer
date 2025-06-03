from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from typing import Dict, List
import logging

class InfluxDBWriter:
    def __init__(self, url: str, token: str, org: str, bucket: str):
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.bucket = bucket
        self.org = org
        
    def write_point(self, data_point: Dict) -> bool:
        """Write a single data point to InfluxDB."""
        try:
            point = Point(data_point['measurement'])
            
            # Add time
            point.time(data_point['time'])
            
            # Add fields
            for field_name, field_value in data_point['fields'].items():
                if field_value is not None:
                    point.field(field_name, field_value)
                    
            # Add tags
            if 'tags' in data_point:
                for tag_name, tag_value in data_point['tags'].items():
                    if tag_value is not None:
                        point.tag(tag_name, tag_value)
                        
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
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