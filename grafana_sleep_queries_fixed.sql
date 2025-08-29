-- Apple Health Sleep Data - CORRECTED Grafana Queries
-- Fixed InfluxDB syntax errors for field name conflicts

-- 1. TOTAL DAILY SLEEP DURATION (All Time Compatible)
-- Fixed: Use quotes around 'duration' field and proper aggregation
SELECT 
    SUM("duration")/60 as "Sleep Duration (minutes)"
FROM sleep_metrics 
WHERE 
    (type = 'HKCategoryTypeIdentifierSleepAnalysis' OR 
     sleep_state =~ /HKCategoryValueSleepAnalysisAsleep/)
    AND $timeFilter
GROUP BY time(1d) fill(null)

-- 2. RECENT SLEEP DATA ONLY (Post September 15, 2024)
-- Detailed sleep stage data from Apple Watch
SELECT 
    SUM("duration")/60 as "Sleep Minutes"
FROM sleep_metrics 
WHERE sleep_state =~ /HKCategoryValueSleepAnalysisAsleep/
    AND time >= '2024-09-15T00:00:00Z'
    AND $timeFilter
GROUP BY time(1d) fill(null)

-- 3. SLEEP STAGE BREAKDOWN (New Format Only)
-- Shows Core, REM, Deep sleep separately
SELECT 
    SUM("duration")/60 as "Duration (minutes)"
FROM sleep_metrics 
WHERE sleep_state IN ('HKCategoryValueSleepAnalysisAsleepCore',
                      'HKCategoryValueSleepAnalysisAsleepREM', 
                      'HKCategoryValueSleepAnalysisAsleepDeep')
    AND $timeFilter
GROUP BY sleep_state, time(1d) fill(null)

-- 4. SIMPLE DAILY SLEEP TOTAL (Most Compatible)
-- Basic query that should work with any InfluxDB version
SELECT 
    SUM("value") as "Sleep Duration (seconds)"
FROM sleep_metrics 
WHERE type = 'HKCategoryTypeIdentifierSleepAnalysis'
    AND $timeFilter
GROUP BY time(1d) fill(null)

-- 5. SLEEP EFFICIENCY CALCULATION (Fixed)
-- Uses proper field references and CASE statements
SELECT 
    (SUM(CASE WHEN sleep_state !~ /Awake|InBed/ THEN "duration" ELSE 0 END) * 100.0 / 
     SUM("duration")) as "Sleep Efficiency %"
FROM sleep_metrics 
WHERE sleep_state IS NOT NULL
    AND $timeFilter
GROUP BY time(1d) fill(null)

-- 6. WEEKLY SLEEP AVERAGE (Corrected Syntax)
-- Proper subquery structure for InfluxDB
SELECT 
    MEAN("daily_sleep") as "Weekly Average (hours)"
FROM (
    SELECT 
        SUM("duration")/3600 as "daily_sleep"
    FROM sleep_metrics 
    WHERE (type = 'HKCategoryTypeIdentifierSleepAnalysis' OR 
           sleep_state =~ /HKCategoryValueSleepAnalysisAsleep/)
        AND $timeFilter
    GROUP BY time(1d)
) 
GROUP BY time(1w) fill(null)

-- 7. SLEEP INTERRUPTIONS COUNT (Fixed)
-- Count wake episodes during sleep periods  
SELECT 
    COUNT("duration") as "Wake Episodes"
FROM sleep_metrics 
WHERE sleep_state = 'HKCategoryValueSleepAnalysisAwake'
    AND time >= '2024-09-15T00:00:00Z'
    AND $timeFilter
GROUP BY time(1d) fill(0)

-- 8. LAST NIGHT SLEEP BREAKDOWN (Working Query)
-- Simple breakdown without complex aggregations
SELECT 
    sleep_state,
    SUM("duration")/60 as "Duration_Minutes",
    COUNT(*) as "Episodes"
FROM sleep_metrics 
WHERE sleep_state != ''
    AND time >= now() - 1d
GROUP BY sleep_state

-- 9. ALTERNATIVE: Using VALUE field instead of DURATION
-- If duration field causes issues, try using value field
SELECT 
    SUM("value")/60 as "Sleep Duration (minutes)"
FROM sleep_metrics 
WHERE type = 'HKCategoryTypeIdentifierSleepAnalysis'
    AND $timeFilter
GROUP BY time(1d) fill(null)

-- 10. DEBUG QUERY: Check what fields are actually available
-- Use this to troubleshoot field names
SHOW FIELD KEYS FROM sleep_metrics

-- TROUBLESHOOTING NOTES:
-- 1. If 'duration' field doesn't work, try 'value' field
-- 2. Always quote field names that might be reserved words
-- 3. Use proper CASE syntax for conditional aggregations
-- 4. Avoid complex nested queries in older InfluxDB versions
-- 5. Test simple queries first, then add complexity

-- SIMPLE TEST QUERIES (Use these to verify data access):

-- Test 1: Basic field access
SELECT "duration", "value" FROM sleep_metrics LIMIT 5

-- Test 2: Check available sleep states
SHOW TAG VALUES FROM sleep_metrics WITH KEY = "sleep_state"

-- Test 3: Simple daily aggregation
SELECT SUM("duration") FROM sleep_metrics WHERE time >= now() - 7d GROUP BY time(1d)