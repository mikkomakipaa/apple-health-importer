#!/usr/bin/env python3

import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Optional, Set
from pathlib import Path


class ImportTracker:
    """Tracks import history for incremental imports."""
    
    def __init__(self, tracker_file: str = "import_history.json"):
        self.tracker_file = Path(tracker_file)
        self.import_history = self._load_history()
    
    def _load_history(self) -> Dict:
        """Load import history from file."""
        if not self.tracker_file.exists():
            return {
                'last_import': None,
                'imported_files': {},
                'last_timestamps': {
                    'heartrate_bpm': None,
                    'energy_kcal': None,
                    'sleep_duration_min': None
                }
            }
        
        try:
            with open(self.tracker_file, 'r') as f:
                history = json.load(f)
                # Ensure all required keys exist
                if 'last_timestamps' not in history:
                    history['last_timestamps'] = {
                        'heartrate_bpm': None,
                        'energy_kcal': None,
                        'sleep_duration_min': None
                    }
                return history
        except Exception as e:
            logging.warning(f"Could not load import history: {e}. Starting fresh.")
            return {
                'last_import': None,
                'imported_files': {},
                'last_timestamps': {
                    'heartrate_bpm': None,
                    'energy_kcal': None,
                    'sleep_duration_min': None
                }
            }
    
    def _save_history(self) -> None:
        """Save import history to file."""
        try:
            # Create directory if it doesn't exist
            self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.tracker_file, 'w') as f:
                json.dump(self.import_history, f, indent=2, default=str)
                
        except Exception as e:
            logging.error(f"Could not save import history: {e}")
    
    def get_file_hash(self, file_path: str) -> str:
        """Generate a simple hash of the file for change detection."""
        import hashlib
        
        try:
            file_stat = os.stat(file_path)
            # Use file size and modification time as a simple hash
            hash_input = f"{file_stat.st_size}_{file_stat.st_mtime}".encode()
            return hashlib.md5(hash_input).hexdigest()
        except Exception as e:
            logging.warning(f"Could not generate file hash: {e}")
            return ""
    
    def is_file_already_imported(self, file_path: str) -> bool:
        """Check if this exact file version has been imported before."""
        file_hash = self.get_file_hash(file_path)
        abs_path = str(Path(file_path).resolve())
        
        if abs_path in self.import_history['imported_files']:
            stored_hash = self.import_history['imported_files'][abs_path].get('hash', '')
            return stored_hash == file_hash
        
        return False
    
    def get_last_import_time(self, measurement: str) -> Optional[datetime]:
        """Get the last import timestamp for a specific measurement."""
        timestamp_str = self.import_history['last_timestamps'].get(measurement)
        if timestamp_str:
            try:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except Exception as e:
                logging.warning(f"Invalid timestamp format for {measurement}: {timestamp_str}")
        return None
    
    def should_import_record(self, record_time: str, measurement: str) -> bool:
        """Check if a record should be imported based on timestamp."""
        try:
            record_dt = datetime.fromisoformat(record_time.replace('Z', '+00:00'))
            last_import = self.get_last_import_time(measurement)
            
            if last_import is None:
                return True  # No previous import, import everything
            
            # Import if record is newer than last import
            return record_dt > last_import
            
        except Exception as e:
            logging.warning(f"Error checking import timestamp: {e}")
            return True  # Import when in doubt
    
    def filter_data_points_by_time(self, data_points: Dict, incremental: bool = False) -> Dict:
        """Filter data points based on last import timestamps."""
        if not incremental:
            return data_points
        
        filtered_points = {
            'vitals': [],
            'activity': [],
            'sleep': [],
            'errors': data_points.get('errors', [])
        }
        
        skipped_counts = {'vitals': 0, 'activity': 0, 'sleep': 0}
        
        # Filter vitals (heart rate)
        for point in data_points.get('vitals', []):
            if self.should_import_record(point['time'], 'heartrate_bpm'):
                filtered_points['vitals'].append(point)
            else:
                skipped_counts['vitals'] += 1
        
        # Filter activity (energy and workouts)
        for point in data_points.get('activity', []):
            if self.should_import_record(point['time'], 'energy_kcal'):
                filtered_points['activity'].append(point)
            else:
                skipped_counts['activity'] += 1
        
        # Filter sleep
        for point in data_points.get('sleep', []):
            if self.should_import_record(point['time'], 'sleep_duration_min'):
                filtered_points['sleep'].append(point)
            else:
                skipped_counts['sleep'] += 1
        
        # Log filtering results
        total_skipped = sum(skipped_counts.values())
        if total_skipped > 0:
            logging.info(f"Incremental import: skipped {total_skipped} records from previous imports")
            logging.info(f"  Vitals skipped: {skipped_counts['vitals']}")
            logging.info(f"  Activity skipped: {skipped_counts['activity']}")
            logging.info(f"  Sleep skipped: {skipped_counts['sleep']}")
        
        return filtered_points
    
    def update_last_timestamps(self, data_points: Dict) -> None:
        """Update the last import timestamps based on imported data."""
        # Find the latest timestamp for each measurement type
        latest_timestamps = {}
        
        # Check vitals
        if data_points.get('vitals'):
            latest_vitals = max(data_points['vitals'], key=lambda x: x['time'])
            latest_timestamps['heartrate_bpm'] = latest_vitals['time']
        
        # Check activity
        if data_points.get('activity'):
            latest_activity = max(data_points['activity'], key=lambda x: x['time'])
            latest_timestamps['energy_kcal'] = latest_activity['time']
        
        # Check sleep
        if data_points.get('sleep'):
            latest_sleep = max(data_points['sleep'], key=lambda x: x['time'])
            latest_timestamps['sleep_duration_min'] = latest_sleep['time']
        
        # Update history
        for measurement, timestamp in latest_timestamps.items():
            if timestamp:
                self.import_history['last_timestamps'][measurement] = timestamp
                logging.info(f"Updated last import timestamp for {measurement}: {timestamp}")
    
    def record_file_import(self, file_path: str, stats: Dict) -> None:
        """Record successful import of a file."""
        abs_path = str(Path(file_path).resolve())
        file_hash = self.get_file_hash(file_path)
        
        self.import_history['imported_files'][abs_path] = {
            'hash': file_hash,
            'import_time': datetime.now(timezone.utc).isoformat(),
            'stats': stats
        }
        
        self.import_history['last_import'] = datetime.now(timezone.utc).isoformat()
        self._save_history()
    
    def get_import_summary(self) -> Dict:
        """Get a summary of import history."""
        summary = {
            'total_files_imported': len(self.import_history['imported_files']),
            'last_import': self.import_history['last_import'],
            'last_timestamps': self.import_history['last_timestamps'].copy()
        }
        
        # Convert timestamp strings to readable format
        if summary['last_import']:
            try:
                dt = datetime.fromisoformat(summary['last_import'].replace('Z', '+00:00'))
                summary['last_import_readable'] = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            except:
                summary['last_import_readable'] = summary['last_import']
        
        return summary
    
    def reset_history(self) -> None:
        """Reset import history (for testing or fresh start)."""
        self.import_history = {
            'last_import': None,
            'imported_files': {},
            'last_timestamps': {
                'heartrate_bpm': None,
                'energy_kcal': None,
                'sleep_duration_min': None
            }
        }
        self._save_history()
        logging.info("Import history has been reset")
    
    def show_history(self) -> None:
        """Display import history in a readable format."""
        summary = self.get_import_summary()
        
        print("\n=== Import History ===")
        print(f"Total files imported: {summary['total_files_imported']}")
        
        if summary['last_import']:
            print(f"Last import: {summary.get('last_import_readable', summary['last_import'])}")
        else:
            print("No previous imports found")
        
        print("\nLast timestamps by measurement:")
        for measurement, timestamp in summary['last_timestamps'].items():
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    readable = dt.strftime('%Y-%m-%d %H:%M:%S')
                    print(f"  {measurement}: {readable}")
                except:
                    print(f"  {measurement}: {timestamp}")
            else:
                print(f"  {measurement}: Never imported")
        
        if self.import_history['imported_files']:
            print(f"\nImported files:")
            for file_path, info in self.import_history['imported_files'].items():
                import_time = info.get('import_time', 'Unknown')
                try:
                    dt = datetime.fromisoformat(import_time.replace('Z', '+00:00'))
                    readable_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    readable_time = import_time
                    
                stats = info.get('stats', {})
                written = stats.get('written', 'Unknown')
                print(f"  {Path(file_path).name} - {readable_time} ({written} records)")