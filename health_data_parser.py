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
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S %z")
            return dt.astimezone(self.timezone)
        except ValueError as e:
            # Try alternative ISO format
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.astimezone(self.timezone)
            except ValueError:
                logging.error(f"Unable to parse datetime: {date_str}")
                raise ValueError(f"Cannot parse datetime format: {date_str}")
    
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
            if value <= 0 or value > 400:  # More lenient validation for sleep HR
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
            
    def parse_generic_quantity(self, record: ET.Element) -> Optional[Dict[str, Union[str, Dict]]]:
        """Parse any quantity-type record based on dynamic configuration."""
        record_type = record.get('type', '')
        
        # Validate required attributes
        if not all([record.get('value'), record.get('startDate')]):
            logging.warning(f"{record_type} record missing required attributes")
            return None
            
        try:
            value = float(record.get('value', 0))
            start_date = self.parse_datetime(record.get('startDate'))
            
            # Create base data structure
            data = {
                'measurement': 'generic_quantity',  # Will be overridden by config
                'type': record_type,
                'time': start_date.isoformat(),
                'fields': {
                    'value': value
                },
                'tags': {
                    'source': record.get('sourceName', ''),
                    'unit': record.get('unit', ''),
                    'device': record.get('device', '')
                }
            }
            
            # Add record-type specific tags
            if 'Energy' in record_type:
                data['tags']['energy_type'] = 'active' if 'Active' in record_type else 'resting'
            elif 'Distance' in record_type:
                data['tags']['distance_type'] = record_type.replace('HKQuantityTypeIdentifierDistance', '').lower()
            elif 'HeartRate' in record_type:
                data['tags']['heart_rate_type'] = record_type.replace('HKQuantityTypeIdentifierHeartRate', '').lower() or 'standard'
            elif 'Walking' in record_type or 'Running' in record_type:
                data['tags']['movement_type'] = 'walking' if 'Walking' in record_type else 'running'
            elif 'Apple' in record_type:
                data['tags']['apple_metric'] = record_type.replace('HKQuantityTypeIdentifierApple', '').lower()
            
            return data
            
        except (ValueError, TypeError, AttributeError) as e:
            logging.error(f"Error parsing {record_type} record: {e}")
            return None
    
    def parse_category(self, record: ET.Element) -> Optional[Dict[str, Union[str, Dict]]]:
        """Parse category-type records (sleep, audio events, etc.)."""
        record_type = record.get('type', '')
        
        # Validate required attributes
        if not all([record.get('startDate'), record.get('endDate')]):
            logging.warning(f"{record_type} record missing required date attributes")
            return None
            
        try:
            start_date = self.parse_datetime(record.get('startDate'))
            end_date = self.parse_datetime(record.get('endDate'))
            duration_seconds = (end_date - start_date).total_seconds()  # Keep in seconds for consistency
            
            # Get category value
            category_value = record.get('value', 'Unknown')
            
            data = {
                'measurement': 'generic_category',  # Will be overridden by config
                'type': record_type,
                'time': start_date.isoformat(),
                'fields': {
                    'duration': duration_seconds,  # Store in seconds consistently
                    'value': 1  # Category presence indicator
                },
                'tags': {
                    'source': record.get('sourceName', ''),
                    'device': record.get('device', ''),
                    'category_value': category_value
                }
            }
            
            # Add type-specific tags
            if 'Sleep' in record_type:
                data['tags']['sleep_state'] = category_value
                data['fields']['quality'] = 1 if 'Asleep' in category_value else 0
            elif 'Audio' in record_type:
                data['tags']['exposure_event'] = category_value
            elif 'Stand' in record_type:
                data['tags']['stand_hour'] = category_value
                
            return data
            
        except (ValueError, TypeError, AttributeError) as e:
            logging.error(f"Error parsing {record_type} category record: {e}")
            return None
    
    def parse_calories(self, record: ET.Element) -> Optional[Dict[str, Union[str, Dict]]]:
        """Parse calorie-related records - legacy method for backward compatibility."""
        calorie_types = [
            'HKQuantityTypeIdentifierBasalEnergyBurned',
            'HKQuantityTypeIdentifierActiveEnergyBurned'
        ]
        
        if record.get('type') not in calorie_types:
            return None
            
        return self.parse_generic_quantity(record)
            
    def parse_sleep(self, record: ET.Element) -> Optional[Dict[str, Union[str, Dict]]]:
        """Parse sleep analysis record - legacy method for backward compatibility."""
        sleep_types = [
            'HKCategoryTypeIdentifierSleepAnalysis',
            'HKQuantityTypeIdentifierAppleSleepingWristTemperature',
            'HKQuantityTypeIdentifierAppleSleepingBreathingDisturbances',
            'HKDataTypeSleepDurationGoal'
        ]
        
        if record.get('type') not in sleep_types:
            return None
            
        # Use appropriate parser based on type
        if record.get('type') == 'HKCategoryTypeIdentifierSleepAnalysis':
            return self.parse_category(record)
        else:
            return self.parse_generic_quantity(record) 