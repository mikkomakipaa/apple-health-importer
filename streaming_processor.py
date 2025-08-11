#!/usr/bin/env python3

import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Iterator, Tuple, Optional
from datetime import datetime
import json
from pathlib import Path
from tqdm import tqdm

from health_data_parser import HealthDataParser
from data_validator import HealthDataValidator
from influxdb_writer import InfluxDBWriter
from import_tracker import ImportTracker


class ProgressCheckpoint:
    """Manages progress checkpoints for resumable imports."""
    
    def __init__(self, checkpoint_file: str = "import_progress.json"):
        self.checkpoint_file = Path(checkpoint_file)
        self.checkpoint_data = self._load_checkpoint()
    
    def _load_checkpoint(self) -> Dict:
        """Load checkpoint data from file."""
        if not self.checkpoint_file.exists():
            return {
                'file_hash': None,
                'processed_records': 0,
                'processed_workouts': 0,
                'processed_activities': 0,
                'last_checkpoint_time': None,
                'stats': {
                    'vitals': 0,
                    'activity': 0,
                    'sleep': 0,
                    'errors': 0,
                    'written': 0,
                    'duplicates': 0,
                    'validation_errors': 0
                }
            }
        
        try:
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Could not load checkpoint: {e}. Starting fresh.")
            return self._get_empty_checkpoint()
    
    def _get_empty_checkpoint(self) -> Dict:
        """Get empty checkpoint structure."""
        return {
            'file_hash': None,
            'processed_records': 0,
            'processed_workouts': 0,
            'processed_activities': 0,
            'last_checkpoint_time': None,
            'stats': {
                'vitals': 0,
                'activity': 0,
                'sleep': 0,
                'errors': 0,
                'written': 0,
                'duplicates': 0,
                'validation_errors': 0
            }
        }
    
    def save_checkpoint(self, file_hash: str, processed_counts: Dict, stats: Dict) -> None:
        """Save current progress to checkpoint file."""
        self.checkpoint_data.update({
            'file_hash': file_hash,
            'processed_records': processed_counts.get('records', 0),
            'processed_workouts': processed_counts.get('workouts', 0),
            'processed_activities': processed_counts.get('activities', 0),
            'last_checkpoint_time': datetime.now().isoformat(),
            'stats': stats
        })
        
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(self.checkpoint_data, f, indent=2)
        except Exception as e:
            logging.error(f"Could not save checkpoint: {e}")
    
    def can_resume(self, file_hash: str) -> bool:
        """Check if we can resume processing this file."""
        return (self.checkpoint_data.get('file_hash') == file_hash and 
                self.checkpoint_data.get('processed_records', 0) > 0)
    
    def get_resume_position(self) -> Dict:
        """Get position to resume from."""
        return {
            'records': self.checkpoint_data.get('processed_records', 0),
            'workouts': self.checkpoint_data.get('processed_workouts', 0),
            'activities': self.checkpoint_data.get('processed_activities', 0)
        }
    
    def get_resume_stats(self) -> Dict:
        """Get accumulated stats from previous processing."""
        return self.checkpoint_data.get('stats', {
            'vitals': 0,
            'activity': 0,
            'sleep': 0,
            'errors': 0,
            'written': 0,
            'duplicates': 0,
            'validation_errors': 0
        })
    
    def clear_checkpoint(self) -> None:
        """Clear checkpoint file."""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
        self.checkpoint_data = self._get_empty_checkpoint()


class StreamingHealthDataProcessor:
    """Processes large Apple Health XML files in streaming fashion."""
    
    def __init__(self, parser: HealthDataParser, validator: HealthDataValidator, 
                 influxdb: InfluxDBWriter, tracker: ImportTracker,
                 process_batch_size: int = 5000, checkpoint_interval: int = 10000):
        self.parser = parser
        self.validator = validator
        self.influxdb = influxdb
        self.tracker = tracker
        self.process_batch_size = process_batch_size  # Records to collect before processing
        self.checkpoint_interval = checkpoint_interval  # Records between checkpoints
        
        self.checkpoint = ProgressCheckpoint()
        
        # Processing statistics
        self.total_stats = {
            'vitals': 0,
            'activity': 0,
            'sleep': 0,
            'errors': 0,
            'written': 0,
            'duplicates': 0,
            'validation_errors': 0
        }
    
    def count_xml_elements(self, file_path: str) -> Dict[str, int]:
        """Count total elements in XML file for progress tracking."""
        logging.info("Counting XML elements for progress tracking...")
        counts = {'records': 0, 'workouts': 0, 'activities': 0}
        
        try:
            # Use iterparse to count without loading everything into memory
            for event, elem in ET.iterparse(file_path, events=('start', 'end')):
                if event == 'start':
                    if elem.tag == 'Record':
                        counts['records'] += 1
                    elif elem.tag == 'Workout':
                        counts['workouts'] += 1
                    elif elem.tag == 'ActivitySummary':
                        counts['activities'] += 1
                # Clear element to free memory
                if event == 'end':
                    elem.clear()
            
            logging.info(f"Found {counts['records']} records, {counts['workouts']} workouts, {counts['activities']} activities")
            return counts
            
        except Exception as e:
            logging.warning(f"Could not count XML elements: {e}. Using approximate progress.")
            return {'records': 1000000, 'workouts': 10000, 'activities': 1000}  # Rough estimates
    
    def stream_xml_elements(self, file_path: str, resume_position: Dict = None) -> Iterator[Tuple[str, ET.Element, int]]:
        """Stream XML elements with position tracking."""
        if resume_position is None:
            resume_position = {'records': 0, 'workouts': 0, 'activities': 0}
        
        current_position = {'records': 0, 'workouts': 0, 'activities': 0}
        
        try:
            for event, elem in ET.iterparse(file_path, events=('start', 'end')):
                if event == 'end':
                    if elem.tag == 'Record':
                        current_position['records'] += 1
                        if current_position['records'] > resume_position['records']:
                            yield ('record', elem, current_position['records'])
                    
                    elif elem.tag == 'Workout':
                        current_position['workouts'] += 1
                        if current_position['workouts'] > resume_position['workouts']:
                            yield ('workout', elem, current_position['workouts'])
                    
                    elif elem.tag == 'ActivitySummary':
                        current_position['activities'] += 1
                        if current_position['activities'] > resume_position['activities']:
                            yield ('activity', elem, current_position['activities'])
                    
                    # Clear element to free memory
                    elem.clear()
                    
        except Exception as e:
            logging.error(f"Error streaming XML: {e}")
            raise
    
    def process_batch(self, batch_data: List[Dict], incremental: bool = False) -> Dict:
        """Process a batch of data points."""
        if not batch_data:
            return {'written': 0, 'duplicates': 0, 'errors': 0}
        
        # Filter for incremental import
        if incremental:
            filtered_data = {'vitals': [], 'activity': [], 'sleep': [], 'errors': []}
            
            for point in batch_data:
                measurement = point.get('measurement', '')
                
                if measurement == 'heartrate_bpm':
                    if self.tracker.should_import_record(point['time'], 'heartrate_bpm'):
                        filtered_data['vitals'].append(point)
                elif measurement == 'energy_kcal':
                    if self.tracker.should_import_record(point['time'], 'energy_kcal'):
                        filtered_data['activity'].append(point)
                elif measurement == 'sleep_duration_min':
                    if self.tracker.should_import_record(point['time'], 'sleep_duration_min'):
                        filtered_data['sleep'].append(point)
            
            all_points = []
            all_points.extend(filtered_data['vitals'])
            all_points.extend(filtered_data['activity'])
            all_points.extend(filtered_data['sleep'])
        else:
            all_points = batch_data
        
        if not all_points:
            return {'written': 0, 'duplicates': 0, 'errors': 0}
        
        # Write batch to InfluxDB with per-batch duplicate detection
        return self.influxdb.write_points_batch_streaming(all_points)
    
    def process_file_streaming(self, file_path: str, incremental: bool = False, 
                             preview: bool = False, force: bool = False) -> Dict:
        """Process large XML file in streaming fashion."""
        file_hash = self.tracker.get_file_hash(file_path)
        
        # Check if we can resume
        resume_position = None
        if not force and self.checkpoint.can_resume(file_hash):
            resume_position = self.checkpoint.get_resume_position()
            self.total_stats = self.checkpoint.get_resume_stats()
            logging.info(f"Resuming import from: Records={resume_position['records']}, "
                        f"Workouts={resume_position['workouts']}, Activities={resume_position['activities']}")
        elif not force and self.tracker.is_file_already_imported(file_path):
            logging.info(f"File {file_path} was already imported. Use --force to import again.")
            return self.total_stats
        
        # Count elements for progress tracking
        element_counts = self.count_xml_elements(file_path)
        total_elements = sum(element_counts.values())
        
        if resume_position:
            processed_elements = sum(resume_position.values())
            remaining_elements = total_elements - processed_elements
        else:
            processed_elements = 0
            remaining_elements = total_elements
        
        logging.info(f"Processing {remaining_elements} remaining elements in streaming mode")
        
        if preview:
            logging.info("PREVIEW MODE - Processing first batch only")
        
        # Initialize progress bar
        progress_bar = tqdm(total=remaining_elements, 
                          initial=processed_elements,
                          desc="Processing elements", 
                          unit="elements")
        
        batch_data = []
        processed_counts = resume_position.copy() if resume_position else {'records': 0, 'workouts': 0, 'activities': 0}
        last_checkpoint = processed_elements
        
        try:
            # Stream and process elements
            for element_type, element, position in self.stream_xml_elements(file_path, resume_position):
                data = None
                
                try:
                    # Parse element
                    if element_type == 'record':
                        record_type = element.get('type', '')
                        
                        if 'HeartRate' in record_type:
                            data = self.parser.parse_heart_rate(element)
                            if data:
                                validation_result = self.validator.validate_data_point(data)
                                if validation_result.is_valid:
                                    batch_data.append(data)
                                    self.total_stats['vitals'] += 1
                                else:
                                    self.total_stats['validation_errors'] += 1
                                    
                                # Log warnings
                                for warning in validation_result.warnings:
                                    if self.validator.config_manager.should_log_warnings():
                                        logging.warning(f"Data quality warning: {warning}")
                        
                        elif any(energy_type in record_type for energy_type in ['EnergyBurned', 'StepCount']):
                            data = self.parser.parse_calories(element)
                            if data:
                                validation_result = self.validator.validate_data_point(data)
                                if validation_result.is_valid:
                                    batch_data.append(data)
                                    self.total_stats['activity'] += 1
                                else:
                                    self.total_stats['validation_errors'] += 1
                        
                        elif 'Sleep' in record_type:
                            data = self.parser.parse_sleep(element)
                            if data:
                                validation_result = self.validator.validate_data_point(data)
                                if validation_result.is_valid:
                                    batch_data.append(data)
                                    self.total_stats['sleep'] += 1
                                else:
                                    self.total_stats['validation_errors'] += 1
                        
                        processed_counts['records'] = position
                    
                    elif element_type == 'workout':
                        data = self.parser.parse_workout(element)
                        if data:
                            validation_result = self.validator.validate_data_point(data)
                            if validation_result.is_valid:
                                batch_data.append(data)
                                self.total_stats['activity'] += 1
                            else:
                                self.total_stats['validation_errors'] += 1
                        
                        processed_counts['workouts'] = position
                    
                    elif element_type == 'activity':
                        data = self.parser.parse_activity(element)
                        if data:
                            batch_data.append(data)
                            self.total_stats['activity'] += 1
                        
                        processed_counts['activities'] = position
                    
                except Exception as e:
                    logging.error(f"Error processing {element_type}: {e}")
                    self.total_stats['errors'] += 1
                
                progress_bar.update(1)
                
                # Process batch when it reaches target size
                if len(batch_data) >= self.process_batch_size:
                    if not preview:
                        batch_stats = self.process_batch(batch_data, incremental)
                        self.total_stats['written'] += batch_stats['written']
                        self.total_stats['duplicates'] += batch_stats['duplicates']
                        self.total_stats['errors'] += batch_stats['errors']
                    
                    batch_data = []  # Clear batch to free memory
                
                # Save checkpoint periodically
                current_processed = sum(processed_counts.values())
                if current_processed - last_checkpoint >= self.checkpoint_interval:
                    if not preview:
                        self.checkpoint.save_checkpoint(file_hash, processed_counts, self.total_stats)
                    last_checkpoint = current_processed
                
                # Preview mode - process only first batch
                if preview and self.total_stats['vitals'] + self.total_stats['activity'] + self.total_stats['sleep'] >= 100:
                    break
            
            # Process remaining batch
            if batch_data and not preview:
                batch_stats = self.process_batch(batch_data, incremental)
                self.total_stats['written'] += batch_stats['written']
                self.total_stats['duplicates'] += batch_stats['duplicates']
                self.total_stats['errors'] += batch_stats['errors']
            
            progress_bar.close()
            
            if not preview:
                # Update import tracking
                if self.total_stats['written'] > 0:
                    # We'll need to recreate data_points structure for tracker
                    data_points = self._create_data_points_for_tracker()
                    self.tracker.update_last_timestamps(data_points)
                    self.tracker.record_file_import(file_path, self.total_stats)
                
                # Clear checkpoint on successful completion
                self.checkpoint.clear_checkpoint()
            
            return self.total_stats
            
        except KeyboardInterrupt:
            logging.info("Import interrupted by user. Progress has been saved.")
            if not preview:
                self.checkpoint.save_checkpoint(file_hash, processed_counts, self.total_stats)
            raise
        except Exception as e:
            logging.error(f"Error during streaming processing: {e}")
            if not preview:
                self.checkpoint.save_checkpoint(file_hash, processed_counts, self.total_stats)
            raise
    
    def _create_data_points_for_tracker(self) -> Dict:
        """Create minimal data points structure for timestamp tracking."""
        # This is a simplified version just for timestamp tracking
        # In a real scenario, we'd need to track the latest timestamps during processing
        return {
            'vitals': [],
            'activity': [],
            'sleep': []
        }