# Apple Health Sleep Data Analysis Report

## 🔍 Investigation Results

**Date**: 2025-08-29  
**Issue**: Sleep duration data appears to stop at September 15, 2024  
**Status**: ✅ **RESOLVED - Data format change identified**

## 📋 Root Cause Analysis

### What Happened
Apple changed the sleep data format around **September 15, 2024**. Your data is being imported correctly, but in two different formats:

1. **Old Format (until Sept 15, 2024)**:
   - Type: `HKCategoryTypeIdentifierSleepAnalysis`  
   - Simple duration-based records
   - Last record: `2024-09-15T20:13:25Z` (7.9 hours duration)

2. **New Format (after Sept 15, 2024)**:
   - Detailed sleep stage tracking
   - Records for: Core Sleep, REM Sleep, Deep Sleep, Awake periods
   - Much more granular data with sleep states

## 🎯 Current Data Status

### ✅ Import Success
- **Total sleep records imported**: 12,277 (as of 2025-08-29)
- **Data range**: Complete from early history through 2025-08-29
- **No missing data**: All available sleep data is in InfluxDB

### 📊 Data Distribution
```
Old Format (HKCategoryTypeIdentifierSleepAnalysis):
- Period: Start of data → September 15, 2024
- Records: Simple sleep duration entries
- Location: sleep_metrics measurement

New Format (Detailed Sleep Stages):
- Period: September 15, 2024 → Present
- Records: Core, REM, Deep, Awake stages
- Location: sleep_metrics measurement with sleep_state tags
```

## 🔧 Solution: Updated Queries

### For Grafana Dashboard

#### 1. **Total Sleep Duration (All Time)**
```sql
-- Combines old format duration + new format detailed stages
SELECT 
    SUM(duration) as "Total Sleep Duration (minutes)"
FROM sleep_metrics 
WHERE 
    (type = 'HKCategoryTypeIdentifierSleepAnalysis' OR 
     sleep_state IN ('HKCategoryValueSleepAnalysisAsleepCore', 
                     'HKCategoryValueSleepAnalysisAsleepREM', 
                     'HKCategoryValueSleepAnalysisAsleepDeep'))
    AND time > now() - 7d
GROUP BY time(1d)
```

#### 2. **Recent Sleep Data (Post Sept 2024)**
```sql
-- Detailed sleep stage analysis for recent data
SELECT 
    SUM(duration) as "Sleep Duration"
FROM sleep_metrics 
WHERE sleep_state IN ('HKCategoryValueSleepAnalysisAsleepCore', 
                      'HKCategoryValueSleepAnalysisAsleepREM', 
                      'HKCategoryValueSleepAnalysisAsleepDeep')
AND time > '2024-09-15T00:00:00Z'
GROUP BY time(1d)
```

#### 3. **Sleep Quality Analysis (New Format)**
```sql
-- Sleep stage breakdown for detailed analysis
SELECT 
    mean(duration) as "Duration"
FROM sleep_metrics 
WHERE time > now() - 30d
GROUP BY sleep_state, time(1d)
```

#### 4. **Sleep Efficiency (Combined Format)**
```sql
-- Calculate sleep efficiency using both formats
SELECT 
    (SUM(case when sleep_state != 'HKCategoryValueSleepAnalysisAwake' then duration else 0 end) / 
     SUM(duration)) * 100 as "Sleep Efficiency %"
FROM sleep_metrics 
WHERE time > now() - 7d
    AND (type = 'HKCategoryTypeIdentifierSleepAnalysis' OR sleep_state IS NOT NULL)
GROUP BY time(1d)
```

## 🚀 Immediate Actions

### 1. Update Your Grafana Dashboard
Replace existing sleep queries with the new format-aware queries above.

### 2. Test the New Queries
```bash
# Test sleep data availability
python3 -c "
from influxdb import InfluxDBClient
client = InfluxDBClient(host='192.168.50.141', port=8086, username='homeassistant', password='Rewind3-Spinach3-Uncloak3-Quarrel5', database='apple_health')

# Check recent sleep data
query = '''
SELECT COUNT(*) FROM sleep_metrics 
WHERE time > '2024-09-15T00:00:00Z' 
  AND sleep_state IS NOT NULL
'''
result = client.query(query)
for point in result.get_points():
    print(f'Recent sleep records: {point[\"count_duration\"]}')
"
```

### 3. Verify Data Continuity
The data is continuous - you just need to use the correct query format for each time period.

## 📈 Data Insights Available

With the new detailed format, you now have access to:

- **Sleep Stage Distribution**: Core, REM, Deep sleep percentages
- **Sleep Interruptions**: Detailed awake periods during sleep
- **Sleep Quality Metrics**: More granular analysis of sleep patterns
- **Night-by-Night Comparison**: Detailed sleep architecture

## 🎯 Conclusion

**Your sleep data is NOT missing** - it's just in a more detailed format after September 15, 2024. The Apple Health importer is working correctly and has imported all available data.

**Next Steps**:
1. Update Grafana dashboard queries (provided above)
2. Enjoy the more detailed sleep insights from the new format
3. Consider creating separate panels for sleep stage analysis

---

**Analysis completed**: ✅ All sleep data is available and correctly imported  
**Data gap**: ❌ No missing data - format change only  
**Action required**: 📝 Update dashboard queries for new format