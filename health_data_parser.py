import xml.etree.ElementTree as ET
from datetime import datetime
import pytz
import logging
from typing import Dict, List, Optional, Union

class HealthDataParser:
    # Constants for unit conversions
    KM_TO_METERS = 1000
    MINUTES_TO_SECONDS = 60.0
    
    def __init__(self, timezone: str):
        self.timezone = pytz.timezone(timezone)
        
    def parse_datetime(self, date_str: str) -> datetime:
        """Convert Apple Health datetime string to timezone-aware datetime object."""
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S %z")
        return dt.astimezone(self.timezone)
    
    def parse_heart_rate(self, record: ET.Element) -> Optional[Dict[str, Union[str, Dict]]]:
        """Parse heart rate record."""
        if record.get('type') != 'HKQuantityTypeIdentifierHeartRate':
            return None
        
        # Validate required attributes
        if not all([record.get('value'), record.get('startDate')]):
            logging.warning("Heart rate record missing required attributes")
            return None
            
        try:
            value = float(record.get('value'))
            if value <= 0 or value > 300:  # Basic heart rate validation
                logging.warning(f"Invalid heart rate value: {value}")
                return None
                
            start_date = self.parse_datetime(record.get('startDate'))
            device = record.get('device', '')
            
            # Get motion context if available
            motion_context = None
            for metadata in record.findall('MetadataEntry'):
                if metadata.get('key') == 'HKMetadataKeyHeartRateMotionContext':
                    motion_context = int(metadata.get('value'))
                    
            return {
                'measurement': 'heartrate_bpm',
                'type': 'HKQuantityTypeIdentifierHeartRate',
                'time': start_date.isoformat(),
                'fields': {
                    'value': value
                },
                'tags': {
                    'device': device,
                    'source': record.get('sourceName'),
                    'motion_context': str(motion_context) if motion_context is not None else None
                }
            }
        except (ValueError, TypeError, AttributeError) as e:
            logging.error(f"Error parsing heart rate record: {e}")
            return None
            
    def parse_workout(self, workout: ET.Element) -> Optional[Dict[str, Union[str, Dict]]]:
        """Parse workout record."""
        # Validate required attributes
        if not all([workout.get('workoutActivityType'), workout.get('startDate')]):
            logging.warning("Workout record missing required attributes")
            return None
            
        try:
            activity_type = workout.get('workoutActivityType')
            duration = float(workout.get('duration', 0))  # Already in seconds
            distance = float(workout.get('totalDistance', 0)) * self.KM_TO_METERS  # Convert km to m
            energy = float(workout.get('totalEnergyBurned', 0))  # Already in kcal
            
            # Basic validation
            if duration < 0 or distance < 0 or energy < 0:
                logging.warning(f"Invalid workout values: duration={duration}, distance={distance}, energy={energy}")
                return None
                
            start_date = self.parse_datetime(workout.get('startDate'))
            
            return {
                'measurement': 'energy_kcal',
                'type': 'HKWorkoutTypeIdentifier',
                'time': start_date.isoformat(),
                'fields': {
                    'value': energy,
                    'duration': duration,
                    'distance': distance
                },
                'tags': {
                    'activity_type': activity_type,
                    'source': workout.get('sourceName')
                }
            }
        except (ValueError, TypeError, AttributeError) as e:
            logging.error(f"Error parsing workout record: {e}")
            return None
            
    def parse_activity(self, activity: ET.Element) -> Optional[Dict[str, Union[str, Dict]]]:
        """Parse activity summary record."""
        try:
            date = activity.get('dateComponents')
            if not date:
                return None
                
            # Convert YYYY-MM-DD to datetime at start of day
            activity_date = datetime.strptime(date, "%Y-%m-%d").replace(
                tzinfo=self.timezone
            )
            
            return {
                'measurement': 'energy_kcal',
                'type': 'HKActivitySummary',
                'time': activity_date.isoformat(),
                'fields': {
                    'value': float(activity.get('activeEnergyBurned', 0)),
                    'target': float(activity.get('activeEnergyBurnedGoal', 0)),
                    'move_minutes': float(activity.get('appleMoveTime', 0)),
                    'exercise_minutes': float(activity.get('appleExerciseTime', 0)),
                    'stand_hours': float(activity.get('appleStandHours', 0))
                },
                'tags': {
                    'summary_type': 'daily'
                }
            }
        except (ValueError, TypeError, AttributeError) as e:
            logging.error(f"Error parsing activity record: {e}")
            return None
            
    def parse_calories(self, record: ET.Element) -> Optional[Dict[str, Union[str, Dict]]]:
        """Parse calorie-related records."""
        calorie_types = [
            'HKQuantityTypeIdentifierBasalEnergyBurned',
            'HKQuantityTypeIdentifierActiveEnergyBurned'
        ]
        
        if record.get('type') not in calorie_types:
            return None
        
        # Validate required attributes
        if not all([record.get('value'), record.get('startDate')]):
            logging.warning("Calorie record missing required attributes")
            return None
            
        try:
            value = float(record.get('value', 0))
            if value < 0 or value > 10000:  # Basic calorie validation
                logging.warning(f"Invalid calorie value: {value}")
                return None
                
            start_date = self.parse_datetime(record.get('startDate'))
            record_type = record.get('type')
            
            return {
                'measurement': 'energy_kcal',
                'type': record_type,
                'time': start_date.isoformat(),
                'fields': {
                    'value': value
                },
                'tags': {
                    'energy_type': 'active' if 'Active' in record_type else 'resting',
                    'source': record.get('sourceName')
                }
            }
        except (ValueError, TypeError, AttributeError) as e:
            logging.error(f"Error parsing calorie record: {e}")
            return None
            
    def parse_sleep(self, record: ET.Element) -> Optional[Dict[str, Union[str, Dict]]:
        """Parse sleep analysis record."""
        if record.get('type') != 'HKCategoryTypeIdentifierSleepAnalysis':
            return None
            
        try:
            start_date = self.parse_datetime(record.get('startDate'))
            end_date = self.parse_datetime(record.get('endDate'))
            value = record.get('value')
            duration_minutes = (end_date - start_date).total_seconds() / self.MINUTES_TO_SECONDS
            
            return {
                'measurement': 'sleep_duration_min',
                'type': 'HKCategoryTypeIdentifierSleepAnalysis',
                'time': start_date.isoformat(),
                'fields': {
                    'value': duration_minutes,
                    'quality': 1 if value == 'HKCategoryValueSleepAnalysisAsleep' else 0
                },
                'tags': {
                    'state': value,
                    'source': record.get('sourceName')
                }
            }
        except (ValueError, TypeError, AttributeError) as e:
            logging.error(f"Error parsing sleep record: {e}")
            return None 