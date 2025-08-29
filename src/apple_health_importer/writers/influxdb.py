from influxdb import InfluxDBClient
from typing import Dict, List, Optional, Union, Set
import logging
from urllib.parse import urlparse
import time
from datetime import datetime, timedelta
from ..config.manager import ConfigManager


class InfluxDBWriter:
    """InfluxDB writer with configurable measurements and batching support."""
    
    def __init__(self, url: str, username: str, password: str, database: str, config_manager: Optional[ConfigManager] = None):
        # Parse and validate URL
        try:
            parsed = urlparse(url)
            if not parsed.hostname:
                raise ValueError(f"Invalid URL format: {url}")
            
            host = parsed.hostname
            port = parsed.port or 8086  # Default InfluxDB port
            
            if not isinstance(port, int) or port <= 0 or port > 65535:
                raise ValueError(f"Invalid port number: {port}")
                
        except Exception as e:
            logging.error(f"Error parsing InfluxDB URL '{url}': {e}")
            raise ValueError(f"Invalid InfluxDB URL: {e}")
        
        self.client = InfluxDBClient(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database
        )
        
        # Initialize configuration manager
        self.config_manager = config_manager or ConfigManager()
        
        # Cache for duplicate detection
        self.existing_timestamps: Dict[str, Set[str]] = {}
        
    def check_for_duplicates(self, measurement: str, start_time: str, end_time: str) -> Set[str]:
        """Check for existing timestamps in InfluxDB within the given time range."""
        try:
            # First check if measurement exists by trying to get any record
            test_query = f'SHOW MEASUREMENTS WHERE "name" = \'{measurement}\''
            test_result = self.client.query(test_query)
            
            if not test_result:
                # Measurement doesn't exist yet, no duplicates
                return set()
            
            # Query existing data points in the time range
            # Use * to get all fields which avoids the "at least 1 non-time field" error
            query = f"""
            SELECT * FROM "{measurement}" 
            WHERE time >= '{start_time}' AND time <= '{end_time}'
            LIMIT 10000
            """
            
            result = self.client.query(query)
            existing_times = set()
            
            if result:
                for point in result.get_points():
                    existing_times.add(point['time'])
                    
            logging.debug(f"Found {len(existing_times)} existing records in {measurement} between {start_time} and {end_time}")
            return existing_times
            
        except Exception as e:
            logging.warning(f"Could not check for duplicates in {measurement}: {e}")
            return set()
    
    def load_existing_data_cache(self, data_points: List[Dict]) -> None:
        """Load existing data cache for duplicate detection."""
        if not data_points:
            return
            
        # Group by measurement
        measurements_timeranges = {}
        for point in data_points:
            measurement = point.get('measurement', '')
            timestamp = point.get('time', '')
            
            if measurement not in measurements_timeranges:
                measurements_timeranges[measurement] = {'min': timestamp, 'max': timestamp}
            else:
                if timestamp < measurements_timeranges[measurement]['min']:
                    measurements_timeranges[measurement]['min'] = timestamp
                if timestamp > measurements_timeranges[measurement]['max']:
                    measurements_timeranges[measurement]['max'] = timestamp
        
        # Check each measurement for existing data
        for measurement, timerange in measurements_timeranges.items():
            # Add buffer to the time range
            try:
                start_dt = datetime.fromisoformat(timerange['min'].replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(timerange['max'].replace('Z', '+00:00'))
                
                # Add buffer hours
                window_hours = self.config_manager.get_duplicate_check_window()
                start_dt -= timedelta(hours=window_hours)
                end_dt += timedelta(hours=window_hours)
                
                existing_times = self.check_for_duplicates(
                    measurement,
                    start_dt.isoformat(),
                    end_dt.isoformat()
                )
                
                self.existing_timestamps[measurement] = existing_times
                
            except Exception as e:
                logging.warning(f"Error processing time range for {measurement}: {e}")
                self.existing_timestamps[measurement] = set()

    def get_measurement_category(self, data_type: str) -> str:
        """Determine the measurement category for a given data type."""
        category = self.config_manager.find_measurement_category(data_type)
        return category if category else 'other'

    def prepare_point(self, data_point: Dict[str, Union[str, Dict]]) -> Dict[str, Union[str, Dict]]:
        """Prepare data point for InfluxDB storage."""
        data_type = data_point.get('type', '')
        category = self.get_measurement_category(data_type)
        
        # Get measurement configuration
        measurement_config = self.config_manager.get_measurement_config(category)
        if not measurement_config:
            raise ValueError(f"No configuration found for category: {category}")
        
        point = {
            "measurement": measurement_config.measurement_name,
            "time": data_point['time'],
            "tags": {
                "type": data_type
            },
            "fields": {}
        }

        # Add configured tags, filtering out empty/None values
        source_tags = data_point.get('tags', {})
        for tag_name in measurement_config.tags:
            tag_value = source_tags.get(tag_name)
            if tag_value is not None and str(tag_value).strip():  # Skip empty strings and None
                point['tags'][tag_name] = str(tag_value).strip()

        # Handle fields - use dynamic mapping based on data type
        source_fields = data_point.get('fields', {})
        
        # For most cases, map 'value' field to a type-specific name
        if 'value' in source_fields:
            field_name = self._get_field_name_for_type(data_type)
            point['fields'][field_name] = source_fields['value']
        
        # Map other fields directly
        for field_name, value in source_fields.items():
            if field_name != 'value':  # Already handled above
                point['fields'][field_name] = value
        
        # Ensure we have at least one field for InfluxDB
        if not point['fields']:
            point['fields']['value'] = 1  # Default value for category-type records
        
        return point
    
    def _get_field_name_for_type(self, data_type: str) -> str:
        """Get appropriate field name for a data type."""
        # Map common data types to meaningful field names
        type_field_mapping = {
            'HKQuantityTypeIdentifierHeartRate': 'heart_rate',
            'HKQuantityTypeIdentifierRestingHeartRate': 'resting_heart_rate',
            'HKQuantityTypeIdentifierHeartRateVariabilitySDNN': 'hrv_sdnn',
            'HKQuantityTypeIdentifierBodyMass': 'weight',
            'HKQuantityTypeIdentifierHeight': 'height',
            'HKQuantityTypeIdentifierActiveEnergyBurned': 'active_energy',
            'HKQuantityTypeIdentifierBasalEnergyBurned': 'basal_energy',
            'HKQuantityTypeIdentifierStepCount': 'steps',
            'HKQuantityTypeIdentifierDistanceWalkingRunning': 'distance',
            'HKQuantityTypeIdentifierFlightsClimbed': 'flights',
            'HKQuantityTypeIdentifierOxygenSaturation': 'oxygen_saturation',
            'HKQuantityTypeIdentifierRespiratoryRate': 'respiratory_rate',
            'HKQuantityTypeIdentifierVO2Max': 'vo2_max',
            'HKQuantityTypeIdentifierWalkingSpeed': 'walking_speed',
            'HKQuantityTypeIdentifierRunningSpeed': 'running_speed',
            'HKQuantityTypeIdentifierAppleExerciseTime': 'exercise_time',
            'HKQuantityTypeIdentifierAppleStandTime': 'stand_time',
        }
        
        return type_field_mapping.get(data_type, 'value')
    
    def is_duplicate(self, data_point: Dict) -> bool:
        """Check if a data point is a duplicate."""
        measurement = data_point.get('measurement', '')
        timestamp = data_point.get('time', '')
        
        if measurement in self.existing_timestamps:
            return timestamp in self.existing_timestamps[measurement]
        return False

    def write_point(self, data_point: Dict[str, Union[str, Dict]], max_retries: int = 3, skip_duplicates: bool = True) -> bool:
        """Write a single data point to InfluxDB with retry logic and duplicate checking."""
        if skip_duplicates and self.is_duplicate(data_point):
            return True  # Skip duplicate, return success
            
        point = self.prepare_point(data_point)
        
        for attempt in range(max_retries):
            try:
                self.client.write_points([point])
                return True
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logging.warning(f"InfluxDB write attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Error writing to InfluxDB after {max_retries} attempts: {e}")
                    return False
        
        return False
            
    def write_points_batch(self, data_points: List[Dict[str, Union[str, Dict]]], skip_duplicates: bool = True) -> Dict[str, int]:
        """Write multiple data points to InfluxDB using batching.
        Returns statistics about the write operation."""
        if not data_points:
            return {'written': 0, 'duplicates': 0, 'errors': 0}
        
        # Load existing data cache for duplicate detection
        if skip_duplicates:
            logging.info("Loading existing data cache for duplicate detection...")
            self.load_existing_data_cache(data_points)
        
        stats = {'written': 0, 'duplicates': 0, 'errors': 0}
        prepared_points = []
        
        # Filter duplicates and prepare points
        for data_point in data_points:
            if skip_duplicates and self.is_duplicate(data_point):
                stats['duplicates'] += 1
                continue
                
            try:
                point = self.prepare_point(data_point)
                prepared_points.append(point)
            except Exception as e:
                logging.error(f"Error preparing data point: {e}")
                stats['errors'] += 1
        
        # Write in batches
        batch_size = self.config_manager.get_batch_size()
        total_batches = (len(prepared_points) + batch_size - 1) // batch_size
        logging.info(f"Writing {len(prepared_points)} points in {total_batches} batches of {batch_size}")
        
        for i in range(0, len(prepared_points), batch_size):
            batch = prepared_points[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            success = self._write_batch_with_retry(batch, batch_num, total_batches)
            if success:
                stats['written'] += len(batch)
            else:
                stats['errors'] += len(batch)
        
        return stats
    
    def write_points_batch_streaming(self, data_points: List[Dict[str, Union[str, Dict]]], skip_duplicates: bool = True) -> Dict[str, int]:
        """Write data points with minimal memory footprint for streaming."""
        if not data_points:
            return {'written': 0, 'duplicates': 0, 'errors': 0}
        
        stats = {'written': 0, 'duplicates': 0, 'errors': 0}
        
        # For streaming, we check duplicates per small batch to minimize memory usage
        # Group by measurement for efficient duplicate checking
        measurements_data = {}
        for point in data_points:
            measurement = point.get('measurement', 'unknown')
            if measurement not in measurements_data:
                measurements_data[measurement] = []
            measurements_data[measurement].append(point)
        
        # Process each measurement separately
        for measurement, points in measurements_data.items():
            if skip_duplicates:
                # Load minimal duplicate cache for this measurement and time range
                self._load_streaming_duplicate_cache(measurement, points)
            
            prepared_points = []
            for data_point in points:
                if skip_duplicates and self.is_duplicate(data_point):
                    stats['duplicates'] += 1
                    continue
                
                try:
                    point = self.prepare_point(data_point)
                    prepared_points.append(point)
                except Exception as e:
                    logging.error(f"Error preparing data point: {e}")
                    stats['errors'] += 1
            
            # Write prepared points for this measurement
            if prepared_points:
                try:
                    self.client.write_points(prepared_points)
                    stats['written'] += len(prepared_points)
                    logging.debug(f"Wrote {len(prepared_points)} {measurement} points")
                except Exception as e:
                    logging.error(f"Error writing {measurement} batch: {e}")
                    stats['errors'] += len(prepared_points)
        
        return stats
    
    def _load_streaming_duplicate_cache(self, measurement: str, data_points: List[Dict]) -> None:
        """Load duplicate cache for a specific measurement and small time range."""
        if not data_points:
            return
        
        # Find time range for this small batch
        timestamps = [point.get('time', '') for point in data_points if point.get('time')]
        if not timestamps:
            return
        
        min_time = min(timestamps)
        max_time = max(timestamps)
        
        try:
            # Add small buffer (1 hour) to catch edge cases
            start_dt = datetime.fromisoformat(min_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(max_time.replace('Z', '+00:00'))
            
            start_dt -= timedelta(hours=1)
            end_dt += timedelta(hours=1)
            
            existing_times = self.check_for_duplicates(
                measurement,
                start_dt.isoformat(),
                end_dt.isoformat()
            )
            
            # Only store timestamps for this measurement
            self.existing_timestamps[measurement] = existing_times
            
        except Exception as e:
            logging.warning(f"Error loading streaming duplicate cache for {measurement}: {e}")
            self.existing_timestamps[measurement] = set()
    
    def _write_batch_with_retry(self, batch: List[Dict], batch_num: int, total_batches: int) -> bool:
        """Write a single batch with retry logic."""
        max_retries = self.config_manager.get_max_retries()
        retry_delay_base = self.config_manager.get_retry_delay_base()
        
        for attempt in range(max_retries):
            try:
                self.client.write_points(batch)
                logging.info(f"Successfully wrote batch {batch_num}/{total_batches} ({len(batch)} points)")
                return True
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay_base ** attempt
                    logging.warning(f"Batch {batch_num} attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Failed to write batch {batch_num} after {max_retries} attempts: {e}")
                    return False
        
        return False
    
    def write_points(self, data_points: List[Dict[str, Union[str, Dict]]]) -> int:
        """Write multiple data points to InfluxDB (legacy method).
        Returns the number of successfully written points."""
        stats = self.write_points_batch(data_points)
        return stats['written']
        
    def close(self) -> None:
        """Close the InfluxDB client connection."""
        self.client.close() 