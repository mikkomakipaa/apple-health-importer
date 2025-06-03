#!/usr/bin/env python3

import argparse
import logging
import sys
import yaml
import xml.etree.ElementTree as ET
from typing import Dict, List
from datetime import datetime

from health_data_parser import HealthDataParser
from influxdb_writer import InfluxDBWriter
from homeassistant import HomeAssistantAPI

def load_config(config_path: str) -> Dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Error loading config file: {e}")
        sys.exit(1)

def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('import.log'),
            logging.StreamHandler()
        ]
    )

def process_health_data(xml_path: str, config: Dict) -> None:
    """Process Apple Health export data."""
    try:
        # Initialize components
        parser = HealthDataParser(config['processing']['timezone'])
        influx = InfluxDBWriter(
            config['influxdb']['url'],
            config['influxdb']['token'],
            config['influxdb']['org'],
            config['influxdb']['bucket']
        )
        ha = HomeAssistantAPI(
            config['homeassistant']['url'],
            config['homeassistant']['token']
        )
        
        # Parse XML file
        logging.info(f"Parsing XML file: {xml_path}")
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Process records
        latest_data = {}
        data_points = []
        
        # Process heart rate records
        for record in root.findall('Record'):
            # Heart Rate
            hr_data = parser.parse_heart_rate(record)
            if hr_data:
                data_points.append(hr_data)
                latest_data['heart_rate'] = hr_data['fields']
                latest_data['heart_rate']['time'] = hr_data['time']
                
            # Calories
            cal_data = parser.parse_calories(record)
            if cal_data:
                data_points.append(cal_data)
                if 'calories' not in latest_data:
                    latest_data['calories'] = {}
                latest_data['calories'][cal_data['fields']['type']] = cal_data['fields']['value']
                
            # Sleep
            sleep_data = parser.parse_sleep(record)
            if sleep_data:
                data_points.append(sleep_data)
                latest_data['sleep'] = {
                    'state': sleep_data['fields']['value'],
                    'duration_minutes': sleep_data['fields']['duration_minutes'],
                    'start_time': sleep_data['time']
                }
        
        # Process workouts
        for workout in root.findall('Workout'):
            workout_data = parser.parse_workout(workout)
            if workout_data:
                data_points.append(workout_data)
                latest_data['workout'] = workout_data['fields']
                latest_data['workout']['activity_type'] = workout_data['tags']['activity_type']
                latest_data['workout']['start_time'] = workout_data['time']
        
        # Process activity summaries
        for activity in root.findall('ActivitySummary'):
            activity_data = parser.parse_activity(activity)
            if activity_data:
                data_points.append(activity_data)
                latest_data['activity'] = activity_data['fields']
        
        # Write data to InfluxDB
        logging.info("Writing data to InfluxDB...")
        success_count = influx.write_points(data_points)
        logging.info(f"Successfully wrote {success_count} of {len(data_points)} points to InfluxDB")
        
        # Update Home Assistant sensors
        logging.info("Updating Home Assistant sensors...")
        ha.update_health_sensors(latest_data)
        
        # Cleanup
        influx.close()
        
    except Exception as e:
        logging.error(f"Error processing health data: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Import Apple Health data to Home Assistant')
    parser.add_argument('xml_file', help='Path to the Apple Health export XML file')
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    args = parser.parse_args()
    
    setup_logging()
    config = load_config(args.config)
    process_health_data(args.xml_file, config)
    logging.info("Import completed successfully")

if __name__ == '__main__':
    main() 