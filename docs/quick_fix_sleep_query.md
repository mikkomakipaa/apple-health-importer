# 🔧 Quick Fix: Sleep Duration Query Error

## Problem
```
InfluxDB returned error: error parsing query: found DURATION, expected identifier, string, number, bool at line 2, char 5
```

## ✅ Solution
The issue is with field name quoting. Use **double quotes** around field names:

### ❌ Wrong Query
```sql
SELECT SUM(duration)/60 as "Sleep Duration (minutes)"
FROM sleep_metrics 
```

### ✅ Correct Query
```sql
SELECT SUM("duration")/60 as "Sleep Duration (minutes)"
FROM sleep_metrics 
WHERE $timeFilter
GROUP BY time(1d) fill(null)
```

## 🚀 Working Grafana Queries

### 1. Daily Sleep Duration (All Data)
```sql
SELECT 
    SUM("duration")/60 as "Sleep Minutes"
FROM sleep_metrics 
WHERE (type = 'HKCategoryTypeIdentifierSleepAnalysis' OR 
       sleep_state =~ /HKCategoryValueSleepAnalysisAsleep/)
    AND $timeFilter
GROUP BY time(1d) fill(null)
```

### 2. Recent Detailed Sleep Data (Post Sept 15, 2024)
```sql
SELECT 
    SUM("duration")/60 as "Sleep Minutes"
FROM sleep_metrics 
WHERE sleep_state =~ /HKCategoryValueSleepAnalysisAsleep/
    AND time >= '2024-09-15T00:00:00Z'
    AND $timeFilter
GROUP BY time(1d) fill(null)
```

### 3. Sleep Stage Breakdown
```sql
SELECT 
    SUM("duration")/60 as "Duration (minutes)"
FROM sleep_metrics 
WHERE sleep_state IN ('HKCategoryValueSleepAnalysisAsleepCore',
                      'HKCategoryValueSleepAnalysisAsleepREM', 
                      'HKCategoryValueSleepAnalysisAsleepDeep')
    AND $timeFilter
GROUP BY sleep_state, time(1d) fill(null)
```

## 🎯 Key Points
1. **Always quote field names**: `"duration"` not `duration`
2. **Use proper regex syntax**: `/pattern/` for pattern matching
3. **Include time filters**: Always use `$timeFilter` in Grafana
4. **Handle nulls**: Use `fill(null)` for missing data points

## 📊 Available Fields
- `"duration"` (float) - Sleep duration in seconds
- `"value"` (float/integer) - Sleep value (usually 1.0 for analysis records)  
- `"quality"` (integer) - Sleep quality score
- `sleep_state` (tag) - Sleep stage (Core, REM, Deep, Awake, InBed)
- `type` (tag) - Record type

## 🔍 Troubleshooting
If queries still fail, try:
1. Use simple test query: `SELECT * FROM sleep_metrics LIMIT 5`
2. Check field names: `SHOW FIELD KEYS FROM sleep_metrics`
3. Check available tags: `SHOW TAG VALUES FROM sleep_metrics WITH KEY = "sleep_state"`