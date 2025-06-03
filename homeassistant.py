import requests
from typing import Dict, Optional
import logging

class HomeAssistantAPI:
    def __init__(self, url: str, token: str):
        self.url = url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
    def create_sensor(self, entity_id: str, state: str, attributes: Optional[Dict] = None) -> bool:
        """Create or update a sensor in Home Assistant."""
        try:
            data = {
                "state": state,
                "attributes": attributes or {}
            }
            
            response = requests.post(
                f"{self.url}/api/states/{entity_id}",
                headers=self.headers,
                json=data
            )
            
            if response.status_code in (200, 201):
                return True
            else:
                logging.error(f"Error creating sensor {entity_id}: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error communicating with Home Assistant: {e}")
            return False
            
    def update_health_sensors(self, latest_data: Dict) -> None:
        """Update all health-related sensors with latest data."""
        # Heart Rate
        if 'heart_rate' in latest_data:
            self.create_sensor(
                'sensor.health_heart_rate',
                str(latest_data['heart_rate']['value']),
                {
                    'unit_of_measurement': 'bpm',
                    'motion_context': latest_data['heart_rate'].get('motion_context'),
                    'device_class': 'measurement',
                    'state_class': 'measurement'
                }
            )
            
        # Calories
        if 'calories' in latest_data:
            if 'active' in latest_data['calories']:
                self.create_sensor(
                    'sensor.health_active_calories',
                    str(latest_data['calories']['active']),
                    {
                        'unit_of_measurement': 'kcal',
                        'device_class': 'energy',
                        'state_class': 'total'
                    }
                )
            if 'resting' in latest_data['calories']:
                self.create_sensor(
                    'sensor.health_resting_calories',
                    str(latest_data['calories']['resting']),
                    {
                        'unit_of_measurement': 'kcal',
                        'device_class': 'energy',
                        'state_class': 'total'
                    }
                )
                
        # Sleep
        if 'sleep' in latest_data:
            self.create_sensor(
                'sensor.health_sleep_state',
                latest_data['sleep']['state'],
                {
                    'duration_minutes': latest_data['sleep'].get('duration_minutes', 0),
                    'start_time': latest_data['sleep'].get('start_time'),
                    'end_time': latest_data['sleep'].get('end_time')
                }
            )
            
        # Activity
        if 'activity' in latest_data:
            activity = latest_data['activity']
            self.create_sensor(
                'sensor.health_activity',
                str(activity.get('active_energy_burned', 0)),
                {
                    'unit_of_measurement': 'kcal',
                    'move_time': activity.get('apple_move_time', 0),
                    'exercise_time': activity.get('apple_exercise_time', 0),
                    'stand_hours': activity.get('apple_stand_hours', 0),
                    'device_class': 'energy',
                    'state_class': 'total'
                }
            )
            
        # Latest Workout
        if 'workout' in latest_data:
            workout = latest_data['workout']
            self.create_sensor(
                'sensor.health_last_workout',
                workout.get('activity_type', 'unknown'),
                {
                    'duration_minutes': workout.get('duration_minutes', 0),
                    'energy_burned': workout.get('energy_burned', 0),
                    'distance': workout.get('distance', 0),
                    'start_time': workout.get('start_time'),
                    'end_time': workout.get('end_time')
                }
            ) 