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
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def process_data(data: Dict, influxdb: InfluxDBWriter) -> bool:
    """Process and write data point to InfluxDB."""
    if data:
        return influxdb.write_point(data)
    return False

def main():
    parser = argparse.ArgumentParser(description='Import Apple Health data to InfluxDB')
    parser.add_argument('export_file', help='Path to the Apple Health export file')
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    args = parser.parse_args()

    setup_logging()
    config = load_config(args.config)

    try:
        # Initialize components
        influxdb = InfluxDBWriter(
            url=config['influxdb']['url'],
            username=config['influxdb']['username'],
            password=config['influxdb']['password'],
            database=config['influxdb']['database']
        )
        
        parser = HealthDataParser(config['processing']['timezone'])

        # Parse and process the export file
        tree = ET.parse(args.export_file)
        root = tree.getroot()

        stats = {
            'vitals': 0,
            'activity': 0,
            'sleep': 0,
            'errors': 0
        }

        # Process all records
        for record in root.findall('.//Record'):
            data = None
            record_type = record.get('type', '')

            # Try each parser based on record type
            if 'HeartRate' in record_type:
                data = parser.parse_heart_rate(record)
                if data:
                    stats['vitals'] += 1
            elif any(energy_type in record_type for energy_type in ['EnergyBurned', 'StepCount']):
                data = parser.parse_calories(record)
                if data:
                    stats['activity'] += 1
            elif 'Sleep' in record_type:
                data = parser.parse_sleep(record)
                if data:
                    stats['sleep'] += 1

            if data and not process_data(data, influxdb):
                stats['errors'] += 1

        # Process workouts
        for workout in root.findall('.//Workout'):
            data = parser.parse_workout(workout)
            if data:
                if process_data(data, influxdb):
                    stats['activity'] += 1
                else:
                    stats['errors'] += 1

        # Process activity summaries
        for activity in root.findall('.//ActivitySummary'):
            data = parser.parse_activity(activity)
            if data:
                if process_data(data, influxdb):
                    stats['activity'] += 1
                else:
                    stats['errors'] += 1

        logging.info("Data import completed:")
        logging.info(f"  Vitals records: {stats['vitals']}")
        logging.info(f"  Activity records: {stats['activity']}")
        logging.info(f"  Sleep records: {stats['sleep']}")
        if stats['errors'] > 0:
            logging.warning(f"  Errors encountered: {stats['errors']}")

    except Exception as e:
        logging.error(f"Error processing health data: {e}")
        sys.exit(1)
    finally:
        influxdb.close()

if __name__ == '__main__':
    main() 