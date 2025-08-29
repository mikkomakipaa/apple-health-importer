#!/usr/bin/env python3

import logging
from datetime import datetime
from typing import Dict, List, Optional, Union
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    corrected_value: Optional[Union[int, float]] = None


class HealthDataValidator:
    """Validates and cleans Apple Health data using configuration-driven rules."""

    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.validation_stats = {
            'total_validated': 0,
            'errors': 0,
            'warnings': 0,
            'corrected': 0
        }

        # Fallback rules for legacy compatibility
        self._fallback_rules = {
            'heart_rate': {
                'min_value': 30,
                'max_value': 250,
                'typical_min': 40,
                'typical_max': 200,
                'units': 'bpm'
            },
            'active_calories': {
                'min_value': 0,
                'max_value': 8000,
                'typical_min': 0,
                'typical_max': 4000,
                'units': 'kcal'
            },
            'resting_calories': {
                'min_value': 500,
                'max_value': 3500,
                'typical_min': 1200,
                'typical_max': 2500,
                'units': 'kcal'
            },
            'workout_duration': {
                'min_value': 60,
                'max_value': 43200,
                'typical_min': 300,
                'typical_max': 7200,
                'units': 'seconds'
            },
            'workout_distance': {
                'min_value': 0,
                'max_value': 200000,
                'typical_min': 100,
                'typical_max': 50000,
                'units': 'meters'
            },
            'sleep_duration': {
                'min_value': 30,
                'max_value': 1440,
                'typical_min': 240,
                'typical_max': 720,
                'units': 'minutes'
            }
        }

    def _get_validation_rules(self, data_type: str, field_name: str = 'value') -> Dict:
        """Get validation rules for a specific data type from config or fallback."""
        if self.config_manager:
            # Find the category this data type belongs to
            category = self.config_manager.find_measurement_category(data_type)
            if category:
                config = self.config_manager.get_measurement_config(category)
                if config and config.validation and config.validation.get('enabled', True):
                    rules = config.validation.get('rules', {})
                    if field_name in rules:
                        return rules[field_name]

        # Fallback to legacy rules
        if data_type in ['HKQuantityTypeIdentifierHeartRate']:
            return self._fallback_rules.get('heart_rate', {})
        elif data_type in ['HKQuantityTypeIdentifierActiveEnergyBurned']:
            return self._fallback_rules.get('active_calories', {})
        elif data_type in ['HKQuantityTypeIdentifierBasalEnergyBurned']:
            return self._fallback_rules.get('resting_calories', {})
        elif data_type in ['HKCategoryTypeIdentifierSleepAnalysis']:
            return self._fallback_rules.get('sleep_duration', {})

        return {}

    def validate_heart_rate(self, value: float, timestamp: str, context: Dict = None) -> ValidationResult:
        """Validate heart rate data."""
        rules = self._get_validation_rules('HKQuantityTypeIdentifierHeartRate')
        errors = []
        warnings = []
        corrected_value = None

        # Only validate if we have rules
        if rules:
            # Basic range validation
            if 'min' in rules and 'max' in rules:
                if value < rules['min'] or value > rules['max']:
                    errors.append(f"Heart rate {value} bpm is outside valid range ({rules['min']}-{rules['max']} bpm)")

            # Typical range warnings
            elif 'typical_min' in rules and 'typical_max' in rules:
                if value < rules['typical_min'] or value > rules['typical_max']:
                    warnings.append(f"Heart rate {value} bpm is outside typical range ({rules['typical_min']}-{rules['typical_max']} bpm)")

        # Context-based validation
        if context and 'motion_context' in context:
            motion = context['motion_context']
            if motion == '0':  # Sedentary
                if value > 120:
                    warnings.append(f"High heart rate ({value} bpm) for sedentary context")
            elif motion == '2':  # Active
                if value < 80:
                    warnings.append(f"Low heart rate ({value} bpm) for active context")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            corrected_value=corrected_value
        )

    def validate_workout(self, data: Dict) -> ValidationResult:
        """Validate workout data."""
        errors = []
        warnings = []

        # Validate duration
        duration = data.get('fields', {}).get('duration', 0)
        if duration:
            duration_result = self._validate_numeric_field(
                duration, 'workout_duration'
            )
            errors.extend(duration_result.errors)
            warnings.extend(duration_result.warnings)

        # Validate distance
        distance = data.get('fields', {}).get('distance', 0)
        if distance:
            distance_result = self._validate_numeric_field(
                distance, 'workout_distance'
            )
            errors.extend(distance_result.errors)
            warnings.extend(distance_result.warnings)

        # Validate energy
        energy = data.get('fields', {}).get('value', 0)
        if energy:
            energy_result = self._validate_numeric_field(
                energy, 'active_calories'
            )
            errors.extend(energy_result.errors)
            warnings.extend(energy_result.warnings)

        # Cross-field validation
        if duration and distance and duration > 0:
            speed_mps = distance / duration  # meters per second
            speed_kmh = speed_mps * 3.6      # km/h

            activity_type = data.get('tags', {}).get('activity_type', '')

            # Basic speed validation
            if speed_kmh > 100:  # Faster than 100 km/h is unrealistic for human activity
                errors.append(f"Unrealistic speed: {speed_kmh:.1f} km/h for {activity_type}")
            elif 'Running' in activity_type and speed_kmh > 30:
                warnings.append(f"Very fast running speed: {speed_kmh:.1f} km/h")
            elif 'Walking' in activity_type and speed_kmh > 12:
                warnings.append(f"Very fast walking speed: {speed_kmh:.1f} km/h")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def validate_sleep(self, data: Dict) -> ValidationResult:
        """Validate sleep data."""
        errors = []
        warnings = []

        duration = data.get('fields', {}).get('value', 0)
        sleep_result = self._validate_numeric_field(duration, 'sleep_duration')
        errors.extend(sleep_result.errors)
        warnings.extend(sleep_result.warnings)

        # Validate sleep timing
        timestamp = data.get('time', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                hour = dt.hour

                # Sleep starting during unusual hours
                if 6 <= hour <= 18:  # 6 AM to 6 PM
                    warnings.append(f"Sleep recorded during daytime hours: {hour:02d}:00")

            except Exception as e:
                errors.append(f"Invalid timestamp format: {timestamp}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def validate_calories(self, data: Dict) -> ValidationResult:
        """Validate calorie data."""
        errors = []
        warnings = []

        value = data.get('fields', {}).get('value', 0)
        energy_type = data.get('tags', {}).get('energy_type', 'active')

        if energy_type == 'resting':
            rules_key = 'resting_calories'
        else:
            rules_key = 'active_calories'

        result = self._validate_numeric_field(value, rules_key)
        errors.extend(result.errors)
        warnings.extend(result.warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def validate_generic_data_point(self, data_point: Dict) -> ValidationResult:
        """Generic validation for any data point using configuration-driven rules."""
        data_type = data_point.get('type', '')
        # measurement = data_point.get('measurement', '')  # unused for now
        fields = data_point.get('fields', {})

        errors = []
        warnings = []

        # Skip validation if no config manager
        if not self.config_manager:
            return ValidationResult(is_valid=True, errors=[], warnings=[])

        # Find the category this data type belongs to
        category = self.config_manager.find_measurement_category(data_type)
        if not category:
            # No validation rules for this type
            return ValidationResult(is_valid=True, errors=[], warnings=[])

        # Check if validation is enabled for this category
        if not self.config_manager.is_validation_enabled(category):
            return ValidationResult(is_valid=True, errors=[], warnings=[])

        # Get validation rules for this category
        validation_rules = self.config_manager.get_validation_rules(category)
        if not validation_rules:
            return ValidationResult(is_valid=True, errors=[], warnings=[])

        # Validate each field that has rules
        for field_name, field_value in fields.items():
            if field_name in validation_rules and isinstance(field_value, (int, float)):
                field_rules = validation_rules[field_name]
                field_result = self._validate_field_with_rules(
                    field_value, field_name, field_rules, data_type
                )
                errors.extend(field_result.errors)
                warnings.extend(field_result.warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _validate_field_with_rules(self, value: Union[int, float], field_name: str, rules: Dict, data_type: str) -> ValidationResult:
        """Validate a field against its rules."""
        errors = []
        warnings = []

        # Basic range validation
        if 'min' in rules and 'max' in rules:
            if value < rules['min'] or value > rules['max']:
                errors.append(f"{field_name.replace('_', ' ').title()} {value} is outside valid range ({rules['min']}-{rules['max']}) for {data_type}")

        # Typical range warnings
        if 'typical_min' in rules and 'typical_max' in rules and len(errors) == 0:
            if value < rules['typical_min'] or value > rules['typical_max']:
                warnings.append(f"{field_name.replace('_', ' ').title()} {value} is outside typical range ({rules['typical_min']}-{rules['typical_max']}) for {data_type}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _validate_numeric_field(self, value: Union[int, float], field_type: str) -> ValidationResult:
        """Legacy numeric field validation for backward compatibility."""
        if field_type not in self._fallback_rules:
            return ValidationResult(is_valid=True, errors=[], warnings=[])

        rules = self._fallback_rules[field_type]
        errors = []
        warnings = []

        if value < rules['min_value'] or value > rules['max_value']:
            errors.append(f"{field_type.replace('_', ' ').title()} {value} {rules['units']} is outside valid range ({rules['min_value']}-{rules['max_value']} {rules['units']})")
        elif value < rules['typical_min'] or value > rules['typical_max']:
            warnings.append(f"{field_type.replace('_', ' ').title()} {value} {rules['units']} is outside typical range ({rules['typical_min']}-{rules['typical_max']} {rules['units']})")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def validate_data_point(self, data_point: Dict) -> ValidationResult:
        """Main validation entry point for any data point."""
        self.validation_stats['total_validated'] += 1

        data_type = data_point.get('type', '')

        try:
            # Use configuration-driven validation first
            if self.config_manager:
                result = self.validate_generic_data_point(data_point)
            else:
                # Fall back to legacy validation for specific types
                if 'HeartRate' in data_type:
                    value = data_point.get('fields', {}).get('value', 0)
                    result = self.validate_heart_rate(
                        value,
                        data_point.get('time', ''),
                        data_point.get('tags', {})
                    )
                elif 'Workout' in data_type:
                    result = self.validate_workout(data_point)
                elif 'Sleep' in data_type:
                    result = self.validate_sleep(data_point)
                elif 'Energy' in data_type:
                    result = self.validate_calories(data_point)
                else:
                    # Unknown type, no validation
                    result = ValidationResult(is_valid=True, errors=[], warnings=[])

            # Update statistics
            if result.errors:
                self.validation_stats['errors'] += 1
            if result.warnings:
                self.validation_stats['warnings'] += 1
            if result.corrected_value is not None:
                self.validation_stats['corrected'] += 1

            return result

        except Exception as e:
            logging.error(f"Validation error for {data_type}: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation failed: {str(e)}"],
                warnings=[]
            )

    def get_validation_summary(self) -> Dict[str, int]:
        """Get validation statistics summary."""
        return self.validation_stats.copy()

    def reset_stats(self) -> None:
        """Reset validation statistics."""
        self.validation_stats = {
            'total_validated': 0,
            'errors': 0,
            'warnings': 0,
            'corrected': 0
        }
