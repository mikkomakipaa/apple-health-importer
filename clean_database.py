#!/usr/bin/env python3
"""Clean the apple_health database for a fresh import."""

import yaml
from influxdb import InfluxDBClient

def clean_database():
    """Remove all measurements from apple_health database."""
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    influx_config = config['influxdb']
    
    try:
        # Parse URL to get host and port
        url = influx_config['url']
        if '://' in url:
            url = url.split('://', 1)[1]  # Remove protocol
        if ':' in url:
            host, port = url.split(':', 1)
            port = int(port)
        else:
            host = url
            port = 8086
            
        # Create client
        client = InfluxDBClient(
            host=host,
            port=port,
            username=influx_config['username'],
            password=influx_config['password'],
            database=influx_config['database']
        )
        
        print(f"Connected to {influx_config['database']} database")
        
        # Get all measurements
        measurements_result = client.query("SHOW MEASUREMENTS")
        measurements = [point['name'] for point in measurements_result.get_points()]
        
        if not measurements:
            print("✅ Database is already empty")
            return
            
        print(f"📊 Found {len(measurements)} measurements:")
        for measurement in measurements:
            print(f"  - {measurement}")
        
        # Get counts before deletion
        total_records = 0
        for measurement in measurements:
            try:
                count_result = client.query(f'SELECT COUNT(*) FROM "{measurement}"')
                count_points = list(count_result.get_points())
                if count_points:
                    count_values = [v for v in count_points[0].values() if isinstance(v, (int, float))]
                    count = sum(count_values) if count_values else 0
                    total_records += count
                    print(f"  {measurement}: {count:,} records")
            except Exception as e:
                print(f"  {measurement}: Could not count records ({e})")
        
        print(f"\n📈 Total records to be deleted: {total_records:,}")
        
        # Confirm deletion
        confirm = input(f"\n⚠️  This will DELETE ALL DATA in the apple_health database. Type 'yes' to continue: ")
        if confirm.lower() != 'yes':
            print("❌ Operation cancelled")
            return
        
        # Drop all measurements
        deleted_count = 0
        for measurement in measurements:
            try:
                client.query(f'DROP MEASUREMENT "{measurement}"')
                deleted_count += 1
                print(f"🗑️  Deleted {measurement}")
            except Exception as e:
                print(f"❌ Failed to delete {measurement}: {e}")
        
        print(f"\n✅ Successfully deleted {deleted_count}/{len(measurements)} measurements")
        print("🔄 Database is now clean and ready for fresh import")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error cleaning database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    clean_database()