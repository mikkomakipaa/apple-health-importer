# Grafana Dashboard Upgrade Guide

## Overview
This document outlines the comprehensive upgrade from the basic Apple Health dashboard to the new comprehensive version that leverages all 56+ data types from our enhanced configuration system.

## Key Improvements

### 📊 **Measurement Coverage**
- **Before**: ~5 basic panels covering heart rate, energy, sleep
- **After**: **13 comprehensive measurement categories** with 25+ detailed panels

### 🔄 **Updated Measurement Names**
The dashboard now uses the new standardized measurement names from our comprehensive configuration:

| Category | Old Measurement | New Measurement | Field Mappings |
|----------|-----------------|-----------------|----------------|
| Heart Health | `apple_health_vitals` | `heart_metrics` | `heart_rate`, `resting_heart_rate`, `hrv_sdnn` |
| Activity | `apple_health_activity` | `energy_metrics`, `movement_metrics` | `active_energy`, `basal_energy`, `steps`, `distance` |
| Sleep | `apple_health_sleep` | `sleep_metrics` | `duration`, `sleep_state` |
| Body | *(new)* | `body_composition` | `weight`, `height` |
| Respiratory | *(new)* | `respiratory_metrics` | `oxygen_saturation`, `respiratory_rate` |
| Sports | *(new)* | `running_performance`, `walking_analysis` | `running_speed`, `walking_speed` |
| Fitness | *(new)* | `fitness_metrics` | `vo2_max`, `exercise_time` |
| Environmental | *(new)* | `environmental_metrics` | `audio_level`, `uv_index` |
| Workouts | *(updated)* | `workout_sessions` | `duration`, `activity_type`, `energy` |

## New Dashboard Sections

### 🫀 **Heart Health & Vital Signs**
- **Enhanced Heart Rate Analysis**: Multi-series chart with regular HR, resting HR, and walking average
- **Heart Rate Summary Table**: Current values and 24-hour averages
- **HRV & Respiratory Health**: Heart Rate Variability (SDNN) and Oxygen Saturation trends
- **Heart Rate Recovery**: 1-minute recovery measurements from workouts

### 🏃‍♂️ **Body Composition & Health Metrics**
- **Body Composition Tracking**: Weight and height trends over time
- **Respiratory Rate Monitoring**: Breathing rate with normal range thresholds

### 💪 **Physical Activity & Movement**
- **Enhanced Daily Energy**: Separate tracking of active vs basal energy expenditure
- **Comprehensive Movement Metrics**: Steps, distance, and flights climbed in one view

### 🏆 **Sports Performance & Fitness**
- **Performance Metrics**: Running speed, walking speed, and VO2 Max trending
- **Workout Distribution**: Pie chart showing time spent in different activity types

### 😴 **Sleep & Recovery**
- **Enhanced Sleep Timeline**: State timeline showing different sleep phases
- **Daily Sleep Duration**: Bar chart with average calculations

### 🌍 **Environmental & Context**
- **Environmental Health Monitoring**: Audio exposure and UV index tracking

## Technical Improvements

### 🎯 **Precise Field Mapping**
- Uses dynamic field names based on data type (e.g., `heart_rate` vs generic `value`)
- Leverages category-specific measurement names for better organization
- Improved data aggregation with proper time intervals

### 📈 **Enhanced Visualizations**
- **Better Color Coding**: Consistent color schemes across related metrics
- **Threshold Indicators**: Health range indicators for key metrics
- **Multi-axis Support**: Different units displayed properly (BPM, kg, m/s, etc.)
- **Improved Legends**: Show mean, max, min, and last values where relevant

### 🔧 **Query Optimization**
- More efficient InfluxDB queries using new measurement structure
- Proper grouping by time intervals with `$__interval` variable
- Reduced query complexity through better data organization

## Migration Instructions

### Option 1: Automated Update (Recommended)
```bash
# Install requirements
pip install requests

# Update dashboard (with backup)
python3 update_grafana_dashboard.py \
  --grafana-url "http://your-grafana:3000" \
  --api-key "your-api-key" \
  --backup

# Dry run first to validate
python3 update_grafana_dashboard.py \
  --grafana-url "http://your-grafana:3000" \
  --api-key "your-api-key" \
  --dry-run
```

### Option 2: Manual Import
1. **Backup Current Dashboard**: Export existing dashboard from Grafana UI
2. **Import New Dashboard**: Use Grafana UI to import `grafana_dashboard_comprehensive.json`
3. **Update Data Source**: Ensure InfluxDB data source UID matches (`P951FEA4DE58B8DFC`)

### Option 3: Gradual Migration
- Keep existing dashboard as `Apple Health Dashboard (Legacy)`
- Import comprehensive version as `Apple Health Comprehensive Dashboard`
- Compare data and migrate panel by panel

## Data Source Requirements

### InfluxDB Configuration
Ensure your InfluxDB contains the new measurement names:
```sql
-- Check available measurements
SHOW MEASUREMENTS

-- Expected measurements:
-- heart_metrics, respiratory_metrics, body_composition
-- energy_metrics, movement_metrics, running_performance
-- walking_analysis, fitness_metrics, sleep_metrics
-- environmental_metrics, workout_sessions
```

### Field Verification
Verify field names in your data:
```sql
-- Check field names for heart metrics
SHOW FIELD KEYS FROM "heart_metrics"

-- Expected fields: heart_rate, resting_heart_rate, hrv_sdnn, etc.
```

## Troubleshooting

### Common Issues

1. **No Data Displayed**
   - Verify measurement names in InfluxDB match dashboard queries
   - Check time range (data might be outside selected period)
   - Confirm data source UID in dashboard matches your InfluxDB connection

2. **Field Not Found Errors**
   - Ensure comprehensive configuration was used for data import
   - Check field mappings in `measurements_config_comprehensive.yaml`
   - Re-run import with `--force` flag if needed

3. **Performance Issues**
   - Adjust time intervals in queries (`$__interval`)
   - Consider using shorter time ranges for initial testing
   - Check InfluxDB performance and indexing

### Verification Steps

1. **Check Import Success**:
   ```bash
   # Verify all measurement categories have data
   python3 -c "
   from influxdb import InfluxDBClient
   client = InfluxDBClient('localhost', 8086, 'user', 'pass', 'database')
   measurements = client.get_list_measurements()
   for m in measurements:
       print(f'Measurement: {m[\"name\"]}')
   "
   ```

2. **Test Dashboard Queries**:
   - Use Grafana Query Inspector to test individual panel queries
   - Verify data returns expected results
   - Check for proper time filtering

## Benefits Summary

✅ **100% Data Type Coverage**: All 56+ Apple Health data types now visualized  
✅ **Professional Health Monitoring**: Enterprise-grade health analytics  
✅ **Comprehensive Insights**: Detailed breakdown by health category  
✅ **Performance Optimized**: Efficient queries with proper data structure  
✅ **Future-Proof**: Extensible configuration for new Apple Health types  
✅ **Medical Context**: Proper health ranges and thresholds  

## Next Steps

After successful migration:
1. **Customize Time Ranges**: Adjust default time ranges for your analysis needs
2. **Add Alerts**: Set up Grafana alerts for health thresholds
3. **Create Playlists**: Set up rotating dashboard views
4. **Export/Share**: Create dashboard snapshots for sharing
5. **Backup Strategy**: Regular exports of dashboard configuration

For additional customization, refer to the comprehensive configuration file `measurements_config_comprehensive.yaml` to understand all available data types and field mappings.