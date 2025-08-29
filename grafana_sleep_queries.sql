-- Apple Health Sleep Data - Updated Grafana Queries
-- Handles both old format (pre Sept 15, 2024) and new detailed format (post Sept 15, 2024)

-- 1. TOTAL DAILY SLEEP DURATION (All Time Compatible)
-- This query works with both old and new sleep data formats
SELECT 
    SUM(duration)/60 as "Sleep Duration (minutes)"
FROM sleep_metrics 
WHERE 
    (type = 'HKCategoryTypeIdentifierSleepAnalysis' OR 
     sleep_state =~ /HKCategoryValueSleepAnalysisAsleep/)
    AND $timeFilter
GROUP BY time(1d) fill(null)

-- 2. RECENT SLEEP DATA ONLY (Post September 15, 2024)
-- Detailed sleep stage data from Apple Watch
SELECT 
    SUM(duration)/60 as "Sleep Minutes"
FROM sleep_metrics 
WHERE sleep_state =~ /HKCategoryValueSleepAnalysisAsleep/
    AND time >= '2024-09-15T00:00:00Z'
    AND $timeFilter
GROUP BY time(1d) fill(null)

-- 3. SLEEP STAGE BREAKDOWN (New Format Only)
-- Shows Core, REM, Deep sleep separately
SELECT 
    SUM(duration)/60 as "Duration (minutes)"
FROM sleep_metrics 
WHERE sleep_state IN ('HKCategoryValueSleepAnalysisAsleepCore',
                      'HKCategoryValueSleepAnalysisAsleepREM', 
                      'HKCategoryValueSleepAnalysisAsleepDeep')
    AND $timeFilter
GROUP BY sleep_state, time(1d) fill(null)

-- 4. SLEEP EFFICIENCY CALCULATION
-- Percentage of time in bed actually sleeping
SELECT 
    (SUM(case when sleep_state !~ /Awake|InBed/ then duration else 0 end) * 100 / 
     SUM(duration)) as "Sleep Efficiency %"
FROM sleep_metrics 
WHERE (sleep_state =~ /Sleep|Awake|InBed/ OR type = 'HKCategoryTypeIdentifierSleepAnalysis')
    AND $timeFilter
GROUP BY time(1d) fill(null)

-- 5. WEEKLY SLEEP AVERAGE
-- Average sleep duration per week
SELECT 
    MEAN(daily_sleep) as "Weekly Average (hours)"
FROM (
    SELECT 
        SUM(duration)/3600 as daily_sleep
    FROM sleep_metrics 
    WHERE (type = 'HKCategoryTypeIdentifierSleepAnalysis' OR 
           sleep_state =~ /HKCategoryValueSleepAnalysisAsleep/)
        AND $timeFilter
    GROUP BY time(1d)
) 
GROUP BY time(1w) fill(null)

-- 6. SLEEP INTERRUPTIONS (New Format)
-- Count of wake periods during sleep
SELECT 
    COUNT(duration) as "Wake Episodes"
FROM sleep_metrics 
WHERE sleep_state = 'HKCategoryValueSleepAnalysisAwake'
    AND time >= '2024-09-15T00:00:00Z'
    AND $timeFilter
GROUP BY time(1d) fill(0)

-- 7. SLEEP ONSET TIME (Time to Fall Asleep)
-- Time between getting in bed and falling asleep
SELECT 
    FIRST(duration)/60 as "Time to Sleep (minutes)"
FROM sleep_metrics 
WHERE sleep_state = 'HKCategoryValueSleepAnalysisInBed'
    AND $timeFilter
GROUP BY time(1d) fill(null)

-- 8. SLEEP CONSISTENCY SCORE
-- Measures how consistent sleep schedule is (standard deviation)
SELECT 
    (3600 - STDDEV(duration)) / 3600 * 100 as "Consistency Score %"
FROM (
    SELECT 
        FIRST(time) as sleep_start,
        SUM(duration) as duration
    FROM sleep_metrics 
    WHERE (type = 'HKCategoryTypeIdentifierSleepAnalysis' OR 
           sleep_state =~ /HKCategoryValueSleepAnalysisAsleep/)
        AND $timeFilter
    GROUP BY time(1d)
)
GROUP BY time(1w) fill(null)

-- 9. DEEP SLEEP PERCENTAGE (New Format Only)
-- Percentage of total sleep that is deep sleep
SELECT 
    (SUM(case when sleep_state = 'HKCategoryValueSleepAnalysisAsleepDeep' then duration else 0 end) * 100 / 
     SUM(case when sleep_state =~ /HKCategoryValueSleepAnalysisAsleep/ then duration else 0 end)) as "Deep Sleep %"
FROM sleep_metrics 
WHERE sleep_state =~ /HKCategoryValueSleepAnalysisAsleep/
    AND time >= '2024-09-15T00:00:00Z'
    AND $timeFilter
GROUP BY time(1d) fill(null)

-- 10. LAST NIGHT'S SLEEP SUMMARY
-- Complete breakdown of last night's sleep
SELECT 
    sleep_state as "Sleep Stage",
    SUM(duration)/60 as "Duration (minutes)",
    COUNT(*) as "Episodes"
FROM sleep_metrics 
WHERE sleep_state =~ /Sleep|Awake|InBed/
    AND time >= now() - 1d
GROUP BY sleep_state

-- USAGE NOTES:
-- - Use queries 1, 4, 5 for historical analysis (covers all data)
-- - Use queries 2, 3, 6, 9 for detailed recent analysis (Sept 15, 2024+)
-- - Query 8 is good for sleep schedule consistency tracking
-- - Query 10 provides a detailed breakdown of recent sleep