#!/usr/bin/env python3

import unittest
import xml.etree.ElementTree as ET
from datetime import datetime
from health_data_parser import HealthDataParser


class TestHealthDataParser(unittest.TestCase):
    """Unit tests for HealthDataParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = HealthDataParser('UTC')
    
    def test_parse_datetime(self):
        """Test datetime parsing functionality."""
        date_str = "2024-01-15 10:30:00 +0000"
        result = self.parser.parse_datetime(date_str)
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 15)
    
    def test_parse_heart_rate_valid(self):
        """Test parsing valid heart rate record."""
        xml_str = '''<Record type="HKQuantityTypeIdentifierHeartRate" 
                           value="72" 
                           startDate="2024-01-15 10:30:00 +0000"
                           sourceName="Apple Watch"
                           device="Apple Watch"/>'''
        record = ET.fromstring(xml_str)
        
        result = self.parser.parse_heart_rate(record)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['fields']['value'], 72.0)
        self.assertEqual(result['type'], 'HKQuantityTypeIdentifierHeartRate')
        self.assertEqual(result['measurement'], 'heartrate_bpm')
    
    def test_parse_heart_rate_invalid_type(self):
        """Test parsing non-heart rate record."""
        xml_str = '''<Record type="HKQuantityTypeIdentifierStepCount" 
                           value="100"/>'''
        record = ET.fromstring(xml_str)
        
        result = self.parser.parse_heart_rate(record)
        self.assertIsNone(result)
    
    def test_parse_heart_rate_missing_required(self):
        """Test parsing heart rate record missing required fields."""
        xml_str = '''<Record type="HKQuantityTypeIdentifierHeartRate"/>'''
        record = ET.fromstring(xml_str)
        
        result = self.parser.parse_heart_rate(record)
        self.assertIsNone(result)
    
    def test_parse_heart_rate_invalid_value(self):
        """Test parsing heart rate record with invalid value."""
        xml_str = '''<Record type="HKQuantityTypeIdentifierHeartRate" 
                           value="400" 
                           startDate="2024-01-15 10:30:00 +0000"/>'''
        record = ET.fromstring(xml_str)
        
        result = self.parser.parse_heart_rate(record)
        self.assertIsNone(result)
    
    def test_parse_workout_valid(self):
        """Test parsing valid workout record."""
        xml_str = '''<Workout workoutActivityType="HKWorkoutActivityTypeRunning"
                           duration="1800"
                           totalDistance="5"
                           totalEnergyBurned="300"
                           startDate="2024-01-15 10:00:00 +0000"
                           sourceName="Apple Watch"/>'''
        workout = ET.fromstring(xml_str)
        
        result = self.parser.parse_workout(workout)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['fields']['value'], 300.0)
        self.assertEqual(result['fields']['duration'], 1800.0)
        self.assertEqual(result['fields']['distance'], 5000.0)  # Converted to meters
        self.assertEqual(result['tags']['activity_type'], 'HKWorkoutActivityTypeRunning')
    
    def test_parse_workout_missing_required(self):
        """Test parsing workout missing required fields."""
        xml_str = '''<Workout duration="1800"/>'''
        workout = ET.fromstring(xml_str)
        
        result = self.parser.parse_workout(workout)
        self.assertIsNone(result)
    
    def test_parse_workout_negative_values(self):
        """Test parsing workout with negative values."""
        xml_str = '''<Workout workoutActivityType="HKWorkoutActivityTypeRunning"
                           duration="-100"
                           startDate="2024-01-15 10:00:00 +0000"/>'''
        workout = ET.fromstring(xml_str)
        
        result = self.parser.parse_workout(workout)
        self.assertIsNone(result)
    
    def test_parse_calories_active(self):
        """Test parsing active calorie record."""
        xml_str = '''<Record type="HKQuantityTypeIdentifierActiveEnergyBurned" 
                           value="250" 
                           startDate="2024-01-15 10:30:00 +0000"
                           sourceName="Apple Watch"/>'''
        record = ET.fromstring(xml_str)
        
        result = self.parser.parse_calories(record)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['fields']['value'], 250.0)
        self.assertEqual(result['tags']['energy_type'], 'active')
    
    def test_parse_calories_resting(self):
        """Test parsing resting calorie record."""
        xml_str = '''<Record type="HKQuantityTypeIdentifierBasalEnergyBurned" 
                           value="80" 
                           startDate="2024-01-15 10:30:00 +0000"/>'''
        record = ET.fromstring(xml_str)
        
        result = self.parser.parse_calories(record)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['fields']['value'], 80.0)
        self.assertEqual(result['tags']['energy_type'], 'resting')
    
    def test_parse_calories_invalid_value(self):
        """Test parsing calories with invalid value."""
        xml_str = '''<Record type="HKQuantityTypeIdentifierActiveEnergyBurned" 
                           value="15000" 
                           startDate="2024-01-15 10:30:00 +0000"/>'''
        record = ET.fromstring(xml_str)
        
        result = self.parser.parse_calories(record)
        self.assertIsNone(result)
    
    def test_constants(self):
        """Test class constants."""
        self.assertEqual(HealthDataParser.KM_TO_METERS, 1000)
        self.assertEqual(HealthDataParser.MINUTES_TO_SECONDS, 60.0)


if __name__ == '__main__':
    unittest.main()