# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Apple Health data importer that processes exported Apple Health XML files and stores the data in InfluxDB while creating corresponding Home Assistant sensors. The system handles heart rate, workouts, activity summaries, sleep data, and calories.

## Key Commands

### Running the Application

**Basic Import:**
```bash
python import_health_data.py path/to/export.xml [--config config.yaml]
```

**Large File Optimization:**
```bash
# Automatic streaming mode for files >100MB
python import_health_data.py large_export.xml --streaming

# Incremental import (only new data)  
python import_health_data.py export.xml --incremental

# Preview before import
python import_health_data.py export.xml --preview

# Resume interrupted import
python import_health_data.py export.xml --resume

# Force re-import
python import_health_data.py export.xml --force
```

**Import Management:**
```bash
# View import history
python import_health_data.py --show-history

# Reset tracking
python import_health_data.py --reset-history
```

### Setup
```bash
pip install -r requirements.txt
cp config.yaml.example config.yaml
# Edit config.yaml with your InfluxDB and Home Assistant settings
```

## Architecture

### Core Components

1. **import_health_data.py** - Main entry point that orchestrates the data import process
   - Parses command line arguments
   - Loads configuration from YAML
   - Processes XML records by type (heart rate, workouts, activities, sleep)
   - Maintains import statistics

2. **health_data_parser.py** - Handles parsing of Apple Health XML records
   - `HealthDataParser` class with timezone-aware datetime parsing
   - Separate methods for each data type: `parse_heart_rate()`, `parse_workout()`, `parse_activity()`, `parse_sleep()`, `parse_calories()`
   - Returns standardized data dictionaries with measurement, fields, tags, and time

3. **influxdb_writer.py** - Manages InfluxDB data storage
   - `InfluxDBWriter` class with connection management
   - Unit conversion mappings for Apple Health data
   - Measurement configurations for different data types
   - `write_point()` method for storing individual data points

4. **homeassistant.py** - Creates and updates Home Assistant sensors
   - `HomeAssistantAPI` class for REST API communication
   - `create_sensor()` method for entity creation/updates

### Configuration

The system uses YAML configuration (`config.yaml`) with sections for:
- InfluxDB connection (url, token, org, bucket)
- Home Assistant connection (url, token)  
- Processing settings (timezone, min_time_between)

### Data Flow

1. XML export file is parsed using ElementTree
2. Records are categorized by type and processed by appropriate parser methods
3. Parsed data is written to InfluxDB via the writer component
4. Home Assistant sensors can be created/updated via the API component
5. Import statistics are tracked and logged

### Error Handling

- Comprehensive exception handling in parsers with logging
- Connection error handling for external services
- Data validation to prevent malformed records
- Import statistics include error counts