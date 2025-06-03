# Apple Health Data Importer for Home Assistant

This tool imports Apple Health data into Home Assistant via InfluxDB. It processes exported Apple Health data and creates corresponding sensors in Home Assistant while storing the historical data in InfluxDB for visualization with Grafana.

## Supported Data Types

- Heart Rate (including motion context)
- Workouts (duration, type, calories burned)
- Activities (daily summaries)
- Sleep data
- Calories (active and resting)

## Prerequisites

1. Python 3.8 or higher
2. Access to InfluxDB instance
3. Home Assistant instance
4. Apple Health data export (XML format)

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `config.yaml.example` to `config.yaml`
4. Edit `config.yaml` with your settings:
   - InfluxDB connection details
   - Home Assistant URL and access token
   - Your local timezone

## Usage

1. Export your Apple Health data from your iPhone:
   - Open Health app
   - Tap your profile picture
   - Select "Export All Health Data"
   - Save the exported zip file
2. Extract the zip file
3. Run the importer:
   ```bash
   python import_health_data.py path/to/export.xml
   ```

## Data Structure

### InfluxDB Measurements

- `apple_health_heartrate`: Heart rate measurements
- `apple_health_workouts`: Workout sessions
- `apple_health_activity`: Daily activity summaries
- `apple_health_sleep`: Sleep analysis
- `apple_health_calories`: Calorie data

### Home Assistant Entities

The script creates the following sensor entities:

- `sensor.health_heart_rate`: Latest heart rate
- `sensor.health_active_calories`: Daily active calories
- `sensor.health_resting_calories`: Daily resting calories
- `sensor.health_sleep_analysis`: Latest sleep state
- Various workout-related sensors

## Grafana Integration

The data stored in InfluxDB can be visualized using Grafana. Example dashboards will be provided in the `dashboards` directory.

## Error Handling

The script includes error handling for:
- Invalid XML data
- Connection issues
- Data validation
- Duplicate entries

Errors are logged to `import.log` 