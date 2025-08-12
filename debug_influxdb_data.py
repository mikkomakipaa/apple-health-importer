#!/usr/bin/env python3
"""
Debug script to check what data is actually available in InfluxDB
for heart rate recovery and sleep timeline panels.
"""

import yaml
from influxdb import InfluxDBClient
import logging

def load_config():
    """Load InfluxDB configuration."""
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return config['influxdb']
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def check_measurements_and_fields(client):
    """Check all measurements and their fields."""
    print("=== Available Measurements ===")
    
    try:
        measurements = client.get_list_measurements()
        for measurement in measurements:
            measurement_name = measurement['name']
            print(f"\n📊 Measurement: {measurement_name}")
            
            # Get field keys
            try:
                field_result = client.query(f'SHOW FIELD KEYS FROM "{measurement_name}"')
                if field_result:
                    fields = list(field_result.get_points())
                    for field in fields:
                        print(f"  └─ Field: {field['fieldKey']} ({field['fieldType']})")
                
                # Get tag keys
                tag_result = client.query(f'SHOW TAG KEYS FROM "{measurement_name}"')
                if tag_result:
                    tags = list(tag_result.get_points())
                    if tags:
                        print(f"  └─ Tags: {', '.join([tag['tagKey'] for tag in tags])}")
                
                # Get sample data
                sample_result = client.query(f'SELECT * FROM "{measurement_name}" LIMIT 3')
                if sample_result:
                    samples = list(sample_result.get_points())
                    if samples:
                        print(f"  └─ Sample record: {samples[0]}")
                        
            except Exception as e:
                print(f"  └─ Error getting details: {e}")
                
    except Exception as e:
        print(f"Error getting measurements: {e}")

def check_heart_rate_recovery(client):
    """Specifically check for heart rate recovery data."""
    print("\n=== Heart Rate Recovery Analysis ===")
    
    # Check for heart rate recovery data types
    recovery_queries = [
        "SELECT * FROM \"heart_metrics\" WHERE \"type\" = 'HKQuantityTypeIdentifierHeartRateRecoveryOneMinute' LIMIT 5",
        "SELECT * FROM \"heart_metrics\" WHERE \"type\" LIKE '%Recovery%' LIMIT 5",
        "SELECT * FROM \"heart_metrics\" WHERE \"type\" LIKE '%HeartRate%' LIMIT 10",
        "SELECT DISTINCT(\"type\") FROM \"heart_metrics\" WHERE \"type\" LIKE '%Heart%'"
    ]
    
    for query in recovery_queries:
        try:
            print(f"\nQuery: {query}")
            result = client.query(query)
            points = list(result.get_points())
            if points:
                print(f"Found {len(points)} records:")
                for point in points[:3]:  # Show first 3
                    print(f"  └─ {point}")
            else:
                print("  └─ No data found")
        except Exception as e:
            print(f"  └─ Query error: {e}")

def check_sleep_data(client):
    """Specifically check for sleep data structure."""
    print("\n=== Sleep Data Analysis ===")
    
    sleep_queries = [
        "SELECT * FROM \"sleep_metrics\" LIMIT 5",
        "SELECT DISTINCT(\"type\") FROM \"sleep_metrics\"",
        "SELECT * FROM \"sleep_metrics\" WHERE \"type\" = 'HKCategoryTypeIdentifierSleepAnalysis' LIMIT 5",
        "SHOW FIELD KEYS FROM \"sleep_metrics\""
    ]
    
    for query in sleep_queries:
        try:
            print(f"\nQuery: {query}")
            result = client.query(query)
            points = list(result.get_points())
            if points:
                print(f"Found {len(points)} records:")
                for point in points[:3]:  # Show first 3
                    print(f"  └─ {point}")
            else:
                print("  └─ No data found")
        except Exception as e:
            print(f"  └─ Query error: {e}")

def check_data_counts(client):
    """Check record counts for key measurements."""
    print("\n=== Data Counts ===")
    
    measurements = [
        "heart_metrics",
        "sleep_metrics", 
        "energy_metrics",
        "movement_metrics",
        "body_composition",
        "respiratory_metrics"
    ]
    
    for measurement in measurements:
        try:
            result = client.query(f'SELECT COUNT(*) FROM "{measurement}"')
            points = list(result.get_points())
            if points:
                count = points[0]['count_heart_rate'] if 'count_heart_rate' in points[0] else points[0].get('count', 0)
                print(f"📊 {measurement}: {count} records")
            else:
                print(f"📊 {measurement}: No data")
        except Exception as e:
            print(f"📊 {measurement}: Error - {e}")

def main():
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    influx_config = load_config()
    if not influx_config:
        print("❌ Could not load InfluxDB configuration")
        return
    
    print(f"🔗 Connecting to InfluxDB: {influx_config['url']}")
    
    try:
        # Connect to InfluxDB
        from urllib.parse import urlparse
        parsed = urlparse(influx_config['url'])
        
        client = InfluxDBClient(
            host=parsed.hostname,
            port=parsed.port or 8086,
            username=influx_config['username'],
            password=influx_config['password'],
            database=influx_config['database']
        )
        
        # Test connection
        client.ping()
        print("✅ Connected successfully!")
        
        # Run diagnostics
        check_data_counts(client)
        check_measurements_and_fields(client)
        check_heart_rate_recovery(client)
        check_sleep_data(client)
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == '__main__':
    main()