import xml.etree.ElementTree as ET
from datetime import datetime
import pytz
from typing import Dict, List, Optional

class HealthDataParser:
    def __init__(self, timezone: str):
        self.timezone = pytz.timezone(timezone)
        
    def parse_datetime(self, date_str: str) -> datetime:
        """Convert Apple Health datetime string to timezone-aware datetime object."""
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S %z")
        return dt.astimezone(self.timezone)
    
    def parse_heart_rate(self, record: ET.Element) -> Optional[Dict]:
        """Parse heart rate record."""
        if record.get('type') != 'HKQuantityTypeIdentifierHeartRate':
            return None
            
        try:
            value = float(record.get('value'))
            start_date = self.parse_datetime(record.get('startDate'))
            device = record.get('device', '')
            
            # Get motion context if available
            motion_context = None
            for metadata in record.findall('MetadataEntry'):
                if metadata.get('key') == 'HKMetadataKeyHeartRateMotionContext':
                    motion_context = int(metadata.get('value'))
                    
            return {
                'measurement': 'apple_health_vitals',
                'type': 'HKQuantityTypeIdentifierHeartRate',
                'time': start_date.isoformat(),
                'fields': {
                    'heart_rate': value
                },
                'tags': {
                    'device': device,
                    'source': record.get('sourceName'),
                    'motion_context': str(motion_context) if motion_context is not None else None
                }
            }
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Error parsing heart rate record: {e}")
            return None
            
    def parse_workout(self, workout: ET.Element) -> Optional[Dict]:
        """Parse workout record."""
        try:
            activity_type = workout.get('workoutActivityType')
            duration = float(workout.get('duration', 0))  # Already in seconds
            distance = float(workout.get('totalDistance', 0)) * 1000  # Convert km to m
            energy = float(workout.get('totalEnergyBurned', 0))  # Already in kcal
            start_date = self.parse_datetime(workout.get('startDate'))
            
            return {
                'measurement': 'apple_health_activity',
                'type': 'HKWorkoutTypeIdentifier',
                'time': start_date.isoformat(),
                'fields': {
                    'duration': duration,
                    'distance': distance,
                    'energy': energy
                },
                'tags': {
                    'activity_type': activity_type,
                    'source': workout.get('sourceName')
                }
            }
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Error parsing workout record: {e}")
            return None
            
    def parse_activity(self, activity: ET.Element) -> Optional[Dict]:
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
                'measurement': 'apple_health_activity',
                'type': 'HKActivitySummary',
                'time': activity_date.isoformat(),
                'fields': {
                    'energy': float(activity.get('activeEnergyBurned', 0)),
                    'energy_goal': float(activity.get('activeEnergyBurnedGoal', 0)),
                    'move_time': float(activity.get('appleMoveTime', 0)),
                    'exercise_time': float(activity.get('appleExerciseTime', 0)),
                    'stand_hours': float(activity.get('appleStandHours', 0))
                },
                'tags': {
                    'summary_type': 'daily'
                }
            }
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Error parsing activity record: {e}")
            return None
            
    def parse_calories(self, record: ET.Element) -> Optional[Dict]:
        """Parse calorie-related records."""
        calorie_types = [
            'HKQuantityTypeIdentifierBasalEnergyBurned',
            'HKQuantityTypeIdentifierActiveEnergyBurned'
        ]
        
        if record.get('type') not in calorie_types:
            return None
            
        try:
            value = float(record.get('value', 0))
            start_date = self.parse_datetime(record.get('startDate'))
            record_type = record.get('type')
            
            return {
                'measurement': 'apple_health_activity',
                'type': record_type,
                'time': start_date.isoformat(),
                'fields': {
                    'energy': value
                },
                'tags': {
                    'energy_type': 'active' if 'Active' in record_type else 'resting',
                    'source': record.get('sourceName')
                }
            }
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Error parsing calorie record: {e}")
            return None
            
    def parse_sleep(self, record: ET.Element) -> Optional[Dict]:
        """Parse sleep analysis record."""
        if record.get('type') != 'HKCategoryTypeIdentifierSleepAnalysis':
            return None
            
        try:
            start_date = self.parse_datetime(record.get('startDate'))
            end_date = self.parse_datetime(record.get('endDate'))
            value = record.get('value')
            duration_minutes = (end_date - start_date).total_seconds() / 60.0
            
            return {
                'measurement': 'apple_health_sleep',
                'type': 'HKCategoryTypeIdentifierSleepAnalysis',
                'time': start_date.isoformat(),
                'fields': {
                    'duration': duration_minutes,
                    'quality': 1 if value == 'HKCategoryValueSleepAnalysisAsleep' else 0
                },
                'tags': {
                    'state': value,
                    'source': record.get('sourceName')
                }
            }
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Error parsing sleep record: {e}")
            return None 