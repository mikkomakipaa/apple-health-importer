#!/usr/bin/env python3

import yaml
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass


@dataclass
class MeasurementConfig:
    """Configuration for a measurement type."""
    description: str
    types: List[str]
    measurement_name: str
    fields: Dict[str, str]
    tags: List[str]
    validation: Dict[str, Any]


@dataclass
class GlobalConfig:
    """Global configuration settings."""
    batch_size: int
    duplicate_check_window_hours: int
    default_timezone: str
    validation: Dict[str, Any]
    performance: Dict[str, Any]


class ConfigManager:
    """Manages external configuration for measurements and settings."""
    
    def __init__(self, measurements_config_path: str = "measurements_config.yaml"):
        self.config_path = Path(measurements_config_path)
        self.measurements_config = None
        self.global_config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            logging.warning(f"Measurements config file {self.config_path} not found, using defaults")
            self._create_default_config()
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            self._parse_config(config_data)
            logging.info(f"Loaded measurements configuration from {self.config_path}")
            
        except Exception as e:
            logging.error(f"Error loading measurements config: {e}")
            logging.info("Using default configuration")
            self._create_default_config()
    
    def _parse_config(self, config_data: Dict) -> None:
        """Parse loaded configuration data."""
        # Parse measurements
        self.measurements_config = {}
        measurements = config_data.get('measurements', {})
        
        for category, config in measurements.items():
            self.measurements_config[category] = MeasurementConfig(
                description=config.get('description', ''),
                types=config.get('types', []),
                measurement_name=config.get('measurement_name', ''),
                fields=config.get('fields', {}),
                tags=config.get('tags', []),
                validation=config.get('validation', {})
            )
        
        # Parse global settings
        global_data = config_data.get('global', {})
        self.global_config = GlobalConfig(
            batch_size=global_data.get('batch_size', 1000),
            duplicate_check_window_hours=global_data.get('duplicate_check_window_hours', 24),
            default_timezone=global_data.get('default_timezone', 'UTC'),
            validation=global_data.get('validation', {}),
            performance=global_data.get('performance', {})
        )
    
    def _create_default_config(self) -> None:
        """Create default configuration when file is not found."""
        # Default measurements configuration
        self.measurements_config = {
            'vitals': MeasurementConfig(
                description="Heart rate and vital signs data",
                types=['HKQuantityTypeIdentifierHeartRate'],
                measurement_name='heartrate_bpm',
                fields={'heart_rate': 'value'},
                tags=['device', 'source', 'motion_context'],
                validation={'enabled': True, 'rules': {}}
            ),
            'activity': MeasurementConfig(
                description="Physical activity, workouts, and energy data",
                types=[
                    'HKQuantityTypeIdentifierStepCount',
                    'HKQuantityTypeIdentifierActiveEnergyBurned',
                    'HKQuantityTypeIdentifierBasalEnergyBurned',
                    'HKWorkoutTypeIdentifier',
                    'HKActivitySummary'
                ],
                measurement_name='energy_kcal',
                fields={
                    'steps': 'count',
                    'energy': 'value',
                    'energy_goal': 'target',
                    'distance': 'distance',
                    'duration': 'duration',
                    'move_time': 'move_minutes',
                    'exercise_time': 'exercise_minutes',
                    'stand_hours': 'stand_hours'
                },
                tags=['activity_type', 'energy_type', 'summary_type', 'device', 'source'],
                validation={'enabled': True, 'rules': {}}
            ),
            'sleep': MeasurementConfig(
                description="Sleep analysis and duration data",
                types=['HKCategoryTypeIdentifierSleepAnalysis'],
                measurement_name='sleep_duration_min',
                fields={'duration': 'value', 'quality': 'quality'},
                tags=['state', 'device', 'source'],
                validation={'enabled': True, 'rules': {}}
            )
        }
        
        # Default global configuration
        self.global_config = GlobalConfig(
            batch_size=1000,
            duplicate_check_window_hours=24,
            default_timezone='UTC',
            validation={'strict_mode': False, 'log_warnings': True},
            performance={'max_retries': 3, 'retry_delay_base': 2}
        )
    
    def get_measurement_config(self, category: str) -> Optional[MeasurementConfig]:
        """Get configuration for a specific measurement category."""
        return self.measurements_config.get(category)
    
    def get_all_measurement_configs(self) -> Dict[str, MeasurementConfig]:
        """Get all measurement configurations."""
        return self.measurements_config.copy()
    
    def get_global_config(self) -> GlobalConfig:
        """Get global configuration."""
        return self.global_config
    
    def find_measurement_category(self, data_type: str) -> Optional[str]:
        """Find which measurement category a data type belongs to."""
        for category, config in self.measurements_config.items():
            if data_type in config.types:
                return category
        return None
    
    def is_validation_enabled(self, category: str) -> bool:
        """Check if validation is enabled for a measurement category."""
        config = self.get_measurement_config(category)
        if config and config.validation:
            return config.validation.get('enabled', True)
        return True
    
    def get_validation_rules(self, category: str) -> Dict[str, Any]:
        """Get validation rules for a measurement category."""
        config = self.get_measurement_config(category)
        if config and config.validation:
            return config.validation.get('rules', {})
        return {}
    
    def get_batch_size(self) -> int:
        """Get configured batch size."""
        return self.global_config.batch_size
    
    def get_duplicate_check_window(self) -> int:
        """Get duplicate check window in hours."""
        return self.global_config.duplicate_check_window_hours
    
    def get_max_retries(self) -> int:
        """Get maximum retry attempts."""
        return self.global_config.performance.get('max_retries', 3)
    
    def get_retry_delay_base(self) -> int:
        """Get retry delay base for exponential backoff."""
        return self.global_config.performance.get('retry_delay_base', 2)
    
    def is_strict_validation(self) -> bool:
        """Check if strict validation mode is enabled."""
        return self.global_config.validation.get('strict_mode', False)
    
    def should_log_warnings(self) -> bool:
        """Check if validation warnings should be logged."""
        return self.global_config.validation.get('log_warnings', True)
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self._load_config()
        logging.info("Configuration reloaded")
    
    def save_default_config(self, path: Optional[str] = None) -> None:
        """Save current configuration to a file."""
        if path is None:
            path = "measurements_config_default.yaml"
        
        config_data = {
            'measurements': {},
            'global': {
                'batch_size': self.global_config.batch_size,
                'duplicate_check_window_hours': self.global_config.duplicate_check_window_hours,
                'default_timezone': self.global_config.default_timezone,
                'validation': self.global_config.validation,
                'performance': self.global_config.performance
            }
        }
        
        for category, config in self.measurements_config.items():
            config_data['measurements'][category] = {
                'description': config.description,
                'types': config.types,
                'measurement_name': config.measurement_name,
                'fields': config.fields,
                'tags': config.tags,
                'validation': config.validation
            }
        
        try:
            with open(path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            logging.info(f"Configuration saved to {path}")
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")
    
    def validate_config(self) -> bool:
        """Validate the loaded configuration."""
        valid = True
        
        # Check measurements
        for category, config in self.measurements_config.items():
            if not config.measurement_name:
                logging.error(f"Measurement category '{category}' missing measurement_name")
                valid = False
            
            if not config.types:
                logging.error(f"Measurement category '{category}' has no types defined")
                valid = False
            
            if not config.fields:
                logging.warning(f"Measurement category '{category}' has no fields defined")
        
        # Check global config
        if self.global_config.batch_size <= 0:
            logging.error("Global batch_size must be positive")
            valid = False
        
        if self.global_config.duplicate_check_window_hours < 0:
            logging.error("Global duplicate_check_window_hours must be non-negative")
            valid = False
        
        return valid