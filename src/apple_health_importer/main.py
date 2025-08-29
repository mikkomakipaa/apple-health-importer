#!/usr/bin/env python3

import argparse
import logging
import sys
import yaml
import xml.etree.ElementTree as ET
from typing import Dict, List
from datetime import datetime
from tqdm import tqdm
from pathlib import Path

# Handle both relative and absolute imports
try:
    from .parsers.health_data import HealthDataParser
    from .writers.influxdb import InfluxDBWriter
    from .writers.homeassistant import HomeAssistantAPI
    from .validation.validator import HealthDataValidator
    from .tracking.tracker import ImportTracker
    from .config.manager import ConfigManager
    from .parsers.streaming import StreamingHealthDataProcessor
except ImportError:
    # For direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    
    from parsers.health_data import HealthDataParser
    from writers.influxdb import InfluxDBWriter
    from writers.homeassistant import HomeAssistantAPI
    from validation.validator import HealthDataValidator
    from tracking.tracker import ImportTracker
    from config.manager import ConfigManager
    from parsers.streaming import StreamingHealthDataProcessor

def load_config(config_path: str) -> Dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Validate required configuration sections
        required_sections = ['influxdb', 'processing']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required config section: {section}")
        
        # Validate InfluxDB config
        influx_required = ['url', 'username', 'password', 'database']
        for key in influx_required:
            if key not in config['influxdb']:
                raise ValueError(f"Missing required InfluxDB config: {key}")
        
        # Validate processing config
        if 'timezone' not in config['processing']:
            raise ValueError("Missing required processing config: timezone")
            
        return config
        
    except Exception as e:
        logging.error(f"Error loading config file: {e}")
        sys.exit(1)

def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def collect_data_points(root: ET.Element, parser: HealthDataParser, validator: HealthDataValidator) -> Dict[str, List[Dict]]:
    """Collect all data points from XML without writing to database."""
    data_points = {
        'vitals': [],
        'activity': [], 
        'sleep': [],
        'errors': []
    }
    
    logging.info("Parsing XML file and collecting data points...")
    
    # Count total records for progress bar
    all_records = root.findall('.//Record') + root.findall('.//Workout') + root.findall('.//ActivitySummary')
    
    with tqdm(total=len(all_records), desc="Parsing records", unit="records") as pbar:
        # Process regular records
        for record in root.findall('.//Record'):
            data = None
            record_type = record.get('type', '')

            try:
                if 'HeartRate' in record_type:
                    data = parser.parse_heart_rate(record)
                    if data:
                        # Validate the data point
                        validation_result = validator.validate_data_point(data)
                        if validation_result.is_valid:
                            data_points['vitals'].append(data)
                        else:
                            data_points['errors'].append({
                                'type': record_type, 
                                'error': 'validation_failed',
                                'details': validation_result.errors
                            })
                            
                        # Log warnings
                        for warning in validation_result.warnings:
                            logging.warning(f"Data quality warning for {record_type}: {warning}")
                            
                elif any(energy_type in record_type for energy_type in ['EnergyBurned', 'StepCount']):
                    data = parser.parse_calories(record)
                    if data:
                        # Validate the data point
                        validation_result = validator.validate_data_point(data)
                        if validation_result.is_valid:
                            data_points['activity'].append(data)
                        else:
                            data_points['errors'].append({
                                'type': record_type,
                                'error': 'validation_failed', 
                                'details': validation_result.errors
                            })
                            
                        # Log warnings
                        for warning in validation_result.warnings:
                            logging.warning(f"Data quality warning for {record_type}: {warning}")
                            
                elif 'Sleep' in record_type:
                    data = parser.parse_sleep(record)
                    if data:
                        # Validate the data point
                        validation_result = validator.validate_data_point(data)
                        if validation_result.is_valid:
                            data_points['sleep'].append(data)
                        else:
                            data_points['errors'].append({
                                'type': record_type,
                                'error': 'validation_failed',
                                'details': validation_result.errors
                            })
                            
                        # Log warnings
                        for warning in validation_result.warnings:
                            logging.warning(f"Data quality warning for {record_type}: {warning}")
                        
                if not data and record_type:  # Record type matched but parsing failed
                    data_points['errors'].append({'type': record_type, 'error': 'parsing_failed'})
                    
            except Exception as e:
                data_points['errors'].append({'type': record_type, 'error': str(e)})
                
            pbar.update(1)

        # Process workouts
        for workout in root.findall('.//Workout'):
            try:
                data = parser.parse_workout(workout)
                if data:
                    # Validate the workout data
                    validation_result = validator.validate_data_point(data)
                    if validation_result.is_valid:
                        data_points['activity'].append(data)
                    else:
                        data_points['errors'].append({
                            'type': 'Workout',
                            'error': 'validation_failed',
                            'details': validation_result.errors
                        })
                        
                    # Log warnings
                    for warning in validation_result.warnings:
                        logging.warning(f"Data quality warning for Workout: {warning}")
                else:
                    data_points['errors'].append({'type': 'Workout', 'error': 'parsing_failed'})
            except Exception as e:
                data_points['errors'].append({'type': 'Workout', 'error': str(e)})
            pbar.update(1)

        # Process activity summaries (no special validation needed)
        for activity in root.findall('.//ActivitySummary'):
            try:
                data = parser.parse_activity(activity)
                if data:
                    data_points['activity'].append(data)
                else:
                    data_points['errors'].append({'type': 'ActivitySummary', 'error': 'parsing_failed'})
            except Exception as e:
                data_points['errors'].append({'type': 'ActivitySummary', 'error': str(e)})
            pbar.update(1)
    
    return data_points

def main():
    parser = argparse.ArgumentParser(description='Import Apple Health data to InfluxDB')
    parser.add_argument('export_file', help='Path to the Apple Health export file')
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    parser.add_argument('--incremental', action='store_true', 
                       help='Only import data newer than last import')
    parser.add_argument('--force', action='store_true',
                       help='Force import even if file was already imported')
    parser.add_argument('--preview', action='store_true',
                       help='Preview what will be imported without writing to database')
    parser.add_argument('--show-history', action='store_true',
                       help='Show import history and exit')
    parser.add_argument('--reset-history', action='store_true',
                       help='Reset import history and exit')
    parser.add_argument('--streaming', action='store_true',
                       help='Use streaming mode for large files (>100MB)')
    parser.add_argument('--resume', action='store_true',
                       help='Resume interrupted import from checkpoint')
    args = parser.parse_args()

    setup_logging()
    
    # Initialize import tracker
    tracker = ImportTracker()
    
    # Handle history commands
    if args.show_history:
        tracker.show_history()
        return
    
    if args.reset_history:
        tracker.reset_history()
        return
    
    config = load_config(args.config)

    try:
        # Initialize configuration manager - use comprehensive config by default
        measurements_config_path = "measurements_config_comprehensive.yaml"
        if Path("measurements_config.yaml").exists() and not Path(measurements_config_path).exists():
            # Fall back to basic config if comprehensive doesn't exist
            measurements_config_path = "measurements_config.yaml"
            logging.info("Using basic measurements configuration")
        else:
            logging.info("Using comprehensive measurements configuration for all 56+ data types")
            
        config_manager = ConfigManager(measurements_config_path)
        if not config_manager.validate_config():
            logging.error("Configuration validation failed")
            sys.exit(1)
        
        # Initialize components
        influxdb = InfluxDBWriter(
            url=config['influxdb']['url'],
            username=config['influxdb']['username'],
            password=config['influxdb']['password'],
            database=config['influxdb']['database'],
            config_manager=config_manager
        )
        
        health_parser = HealthDataParser(config['processing']['timezone'])
        validator = HealthDataValidator(config_manager)

        # Determine if we should use streaming mode
        file_size_mb = Path(args.export_file).stat().st_size / (1024 * 1024)
        use_streaming = args.streaming or file_size_mb > 100  # Auto-enable for files >100MB
        
        if use_streaming:
            logging.info(f"Using streaming mode for large file ({file_size_mb:.1f} MB)")
            
            # Initialize streaming processor
            streaming_processor = StreamingHealthDataProcessor(
                parser=health_parser,
                validator=validator,
                influxdb=influxdb,
                tracker=tracker,
                config_manager=config_manager,
                process_batch_size=config_manager.get_batch_size(),
                checkpoint_interval=10000
            )
            
            # Process file in streaming mode
            processing_stats = streaming_processor.process_file_streaming(
                file_path=args.export_file,
                incremental=args.incremental,
                preview=args.preview,
                force=args.force
            )
            
            # Get validation statistics
            validation_stats = validator.get_validation_summary()
            
            logging.info("Streaming import completed:")
            logging.info(f"  Processing statistics by category:")
            
            # Show statistics for all configured categories
            total_processed = 0
            for category, config in config_manager.get_all_measurement_configs().items():
                count = processing_stats.get(category, 0)
                total_processed += count
                logging.info(f"    - {category.title()} processed: {count} (→ {config.measurement_name})")
            
            logging.info(f"    - Unknown types: {processing_stats.get('unknown_types', 0)}")
            logging.info(f"    - Parse errors: {processing_stats['errors']}")
            logging.info(f"  Validation statistics:")
            logging.info(f"    - Total validated: {validation_stats['total_validated']}")
            logging.info(f"    - Validation errors: {processing_stats['validation_errors']}")
            logging.info(f"    - Validation warnings: {validation_stats['warnings']}")
            logging.info(f"  Write statistics:")
            logging.info(f"    - Successfully written: {processing_stats['written']}")
            logging.info(f"    - Duplicates skipped: {processing_stats['duplicates']}")
            logging.info(f"    - Write errors: {processing_stats.get('write_errors', 0)}")
            logging.info(f"  Summary:")
            logging.info(f"    - Total records processed: {total_processed}")
            logging.info(f"    - Coverage: {len(config_manager.get_all_measurement_configs())} measurement categories configured")
            
            return
        
        # Original non-streaming mode for smaller files
        logging.info(f"Using standard mode for file ({file_size_mb:.1f} MB)")
        
        # Check if file was already imported
        if not args.force and tracker.is_file_already_imported(args.export_file):
            logging.info(f"File {args.export_file} was already imported. Use --force to import again.")
            return

        # Parse the export file
        logging.info(f"Loading XML file: {args.export_file}")
        tree = ET.parse(args.export_file)
        root = tree.getroot()
        
        # Collect all data points first
        data_points = collect_data_points(root, health_parser, validator)
        
        # Filter for incremental import if requested
        if args.incremental:
            logging.info("Applying incremental import filter...")
            data_points = tracker.filter_data_points_by_time(data_points, incremental=True)
        
        # Report parsing results
        total_parsed = sum(len(points) for category, points in data_points.items() if category != 'errors')
        logging.info(f"Parsing completed:")
        logging.info(f"  Vitals records: {len(data_points['vitals'])}")
        logging.info(f"  Activity records: {len(data_points['activity'])}")
        logging.info(f"  Sleep records: {len(data_points['sleep'])}")
        logging.info(f"  Parse errors: {len(data_points['errors'])}")
        
        if not total_parsed:
            if args.incremental:
                logging.info("No new data points found for incremental import")
            else:
                logging.error("No valid data points found to import")
            return
        
        # Handle preview mode
        if args.preview:
            logging.info("PREVIEW MODE - No data will be written to database")
            logging.info("Data that would be imported:")
            logging.info(f"  Vitals records: {len(data_points['vitals'])}")
            logging.info(f"  Activity records: {len(data_points['activity'])}")
            logging.info(f"  Sleep records: {len(data_points['sleep'])}")
            
            # Show sample data for each category
            for category, points in data_points.items():
                if category != 'errors' and points:
                    sample = points[0]
                    logging.info(f"  {category.title()} sample: {sample.get('type', 'Unknown')} at {sample.get('time', 'Unknown time')}")
            return
        
        # Write data points to InfluxDB using batch processing
        logging.info("Starting bulk import to InfluxDB...")
        all_points = []
        all_points.extend(data_points['vitals'])
        all_points.extend(data_points['activity'])
        all_points.extend(data_points['sleep'])
        
        write_stats = influxdb.write_points_batch(all_points)
        
        # Update import tracking if successful
        if write_stats['written'] > 0:
            tracker.update_last_timestamps(data_points)
            tracker.record_file_import(args.export_file, write_stats)
        
        # Get validation statistics
        validation_stats = validator.get_validation_summary()
        
        logging.info("Data import completed:")
        logging.info(f"  Total parsed: {total_parsed}")
        logging.info(f"  Validation statistics:")
        logging.info(f"    - Total validated: {validation_stats['total_validated']}")
        logging.info(f"    - Validation errors: {validation_stats['errors']}")
        logging.info(f"    - Validation warnings: {validation_stats['warnings']}")
        logging.info(f"  Write statistics:")
        logging.info(f"    - Successfully written: {write_stats['written']}")
        logging.info(f"    - Duplicates skipped: {write_stats['duplicates']}")
        logging.info(f"    - Write errors: {write_stats['errors']}")
        
        if write_stats['errors'] > 0:
            logging.warning(f"Some records failed to write. Check InfluxDB connection and permissions.")
        
        if validation_stats['errors'] > 0:
            logging.warning(f"Some records failed validation and were not imported.")
            
        if validation_stats['warnings'] > 0:
            logging.info(f"Data quality warnings were logged for {validation_stats['warnings']} records.")

    except Exception as e:
        logging.error(f"Error processing health data: {e}")
        sys.exit(1)
    finally:
        influxdb.close()

if __name__ == '__main__':
    main() 