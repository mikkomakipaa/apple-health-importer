#!/usr/bin/env python3
"""
Create the ultimate Apple Health dashboard with 6 tabs:
1. Overview (fast glance)
2. Training & Performance  
3. Recovery & Sleep
4. Daily Health Markers
5. Stress & Readiness
6. Data Quality & Ops
"""

import json
from typing import Dict, List, Any

class UltimateDashboardBuilder:
    def __init__(self):
        self.dashboard = {
            "annotations": {"list": []},
            "editable": True,
            "fiscalYearStartMonth": 0,
            "graphTooltip": 1,  # Shared crosshair
            "links": [],
            "liveNow": False,
            "panels": [],
            "refresh": "1m",
            "schemaVersion": 38,
            "style": "dark",
            "tags": ["health", "apple", "ultimate", "comprehensive"],
            "templating": {"list": []},
            "time": {
                "from": "now-7d",
                "to": "now"
            },
            "timepicker": {
                "refresh_intervals": ["5s", "10s", "30s", "1m", "5m", "15m", "30m", "1h", "2h", "1d"]
            },
            "timezone": "browser",
            "title": "Apple Health Ultimate Dashboard",
            "uid": "apple_health_ultimate",
            "version": 1,
            "weekStart": ""
        }
        
        self.current_y = 0
        self.current_id = 1
        
    def add_panel(self, panel: Dict) -> None:
        """Add a panel to the dashboard."""
        panel["id"] = self.current_id
        self.current_id += 1
        
        # Set grid position if not specified
        if "gridPos" not in panel:
            panel["gridPos"] = {
                "h": 8,
                "w": 12,
                "x": 0,
                "y": self.current_y
            }
        
        self.current_y = max(self.current_y, panel["gridPos"]["y"] + panel["gridPos"]["h"])
        self.dashboard["panels"].append(panel)
    
    def add_row(self, title: str, collapsed: bool = False) -> None:
        """Add a row panel (section header)."""
        row_panel = {
            "collapsed": collapsed,
            "gridPos": {
                "h": 1,
                "w": 24,
                "x": 0,
                "y": self.current_y
            },
            "id": self.current_id,
            "panels": [],
            "title": title,
            "type": "row"
        }
        self.current_id += 1
        self.current_y += 1
        self.dashboard["panels"].append(row_panel)
    
    def get_base_datasource(self) -> Dict:
        """Get base data source configuration."""
        return {
            "type": "influxdb",
            "uid": "health_influxdb"
        }
    
    def create_overview_tab(self) -> None:
        """Create Overview tab (Tab 1)."""
        self.add_row("📊 Today's Summary")
        
        # Today summary stats row
        today_stats = [
            {"title": "Steps", "query": 'SELECT last("steps") FROM "movement_metrics" WHERE "type" = \'HKQuantityTypeIdentifierStepCount\' AND time >= now() - 1d', "unit": "short"},
            {"title": "Active kcal", "query": 'SELECT last("active_energy") FROM "energy_metrics" WHERE "type" = \'HKQuantityTypeIdentifierActiveEnergyBurned\' AND time >= now() - 1d', "unit": "kcal"},
            {"title": "Stand Hours", "query": 'SELECT last("stand_time") FROM "energy_metrics" WHERE "type" = \'HKQuantityTypeIdentifierAppleStandTime\' AND time >= now() - 1d', "unit": "h"},
            {"title": "Exercise Min", "query": 'SELECT last("exercise_time") FROM "energy_metrics" WHERE "type" = \'HKQuantityTypeIdentifierAppleExerciseTime\' AND time >= now() - 1d', "unit": "min"},
            {"title": "RHR", "query": 'SELECT last("resting_heart_rate") FROM "heart_metrics" WHERE "type" = \'HKQuantityTypeIdentifierRestingHeartRate\' AND time >= now() - 1d', "unit": "bpm"},
            {"title": "HRV", "query": 'SELECT last("hrv_sdnn") FROM "heart_metrics" WHERE "type" = \'HKQuantityTypeIdentifierHeartRateVariabilitySDNN\' AND time >= now() - 1d', "unit": "ms"},
            {"title": "Sleep Duration", "query": 'SELECT sum("duration")/60 FROM "sleep_metrics" WHERE "type" = \'HKCategoryTypeIdentifierSleepAnalysis\' AND time >= now() - 1d', "unit": "h"},
            {"title": "SpO₂ Avg", "query": 'SELECT mean("oxygen_saturation") FROM "respiratory_metrics" WHERE "type" = \'HKQuantityTypeIdentifierOxygenSaturation\' AND time >= now() - 1d', "unit": "%"}
        ]
        
        for i, stat in enumerate(today_stats):
            x_pos = (i % 4) * 6
            y_pos = self.current_y + (i // 4) * 4
            
            self.add_panel({
                "datasource": self.get_base_datasource(),
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 50},
                                {"color": "red", "value": 80}
                            ]
                        },
                        "unit": stat["unit"]
                    }
                },
                "gridPos": {"h": 4, "w": 6, "x": x_pos, "y": y_pos},
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {
                        "calcs": ["lastNotNull"],
                        "fields": "",
                        "values": False
                    },
                    "showPercentChange": True,
                    "textMode": "auto",
                    "wideLayout": True
                },
                "targets": [{
                    "datasource": self.get_base_datasource(),
                    "query": stat["query"],
                    "rawQuery": True,
                    "refId": "A",
                    "resultFormat": "time_series"
                }],
                "title": stat["title"],
                "type": "stat"
            })
        
        self.current_y += 8
        
        # All-day HR curve with zones
        self.add_row("💓 Heart Rate Overview")
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "palette-classic"},
                    "custom": {
                        "axisCenteredZero": False,
                        "axisColorMode": "text",
                        "axisLabel": "BPM",
                        "axisPlacement": "auto",
                        "drawStyle": "line",
                        "fillOpacity": 10,
                        "gradientMode": "opacity",
                        "lineInterpolation": "smooth",
                        "lineWidth": 2,
                        "pointSize": 5,
                        "showPoints": "never",
                        "spanNulls": True,
                        "stacking": {"group": "A", "mode": "none"},
                        "thresholdsStyle": {"mode": "area"}
                    },
                    "mappings": [],
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "blue", "value": None},  # Zone 1 (Recovery)
                            {"color": "green", "value": 100}, # Zone 2 (Aerobic)
                            {"color": "yellow", "value": 140}, # Zone 3 (Tempo)
                            {"color": "orange", "value": 160}, # Zone 4 (Threshold)
                            {"color": "red", "value": 180}     # Zone 5 (VO2max)
                        ]
                    },
                    "unit": "bpm"
                }
            },
            "gridPos": {"h": 10, "w": 24, "x": 0, "y": self.current_y},
            "options": {
                "legend": {
                    "calcs": ["mean", "max", "min"],
                    "displayMode": "table",
                    "placement": "bottom",
                    "showLegend": True
                },
                "tooltip": {"mode": "multi", "sort": "desc"}
            },
            "targets": [{
                "datasource": self.get_base_datasource(),
                "query": 'SELECT mean("heart_rate") AS "Heart Rate" FROM "heart_metrics" WHERE $timeFilter AND "type" = \'HKQuantityTypeIdentifierHeartRate\' GROUP BY time($__interval) fill(null)',
                "rawQuery": True,
                "refId": "A",
                "resultFormat": "time_series"
            }],
            "title": "All-Day Heart Rate with Zones",
            "type": "timeseries"
        })
        
        self.current_y += 10
        
        # Readiness Score and Weekly Streaks
        self.add_row("🎯 Performance Metrics")
        
        # Readiness Score (calculated from HRV/RHR/Sleep)
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "color": {
                        "mode": "thresholds"
                    },
                    "custom": {
                        "hideFrom": {
                            "legend": False,
                            "tooltip": False,
                            "viz": False
                        }
                    },
                    "mappings": [],
                    "max": 100,
                    "min": 0,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "red", "value": None},
                            {"color": "yellow", "value": 40},
                            {"color": "green", "value": 70}
                        ]
                    },
                    "unit": "percent"
                }
            },
            "gridPos": {"h": 8, "w": 8, "x": 0, "y": self.current_y},
            "options": {
                "minVizHeight": 75,
                "minVizWidth": 75,
                "orientation": "auto",
                "reduceOptions": {
                    "calcs": ["lastNotNull"],
                    "fields": "",
                    "values": False
                },
                "showThresholdLabels": False,
                "showThresholdMarkers": True,
                "text": {}
            },
            "targets": [{
                "datasource": self.get_base_datasource(),
                # Complex readiness formula: (HRV_score * 0.4 + RHR_score * 0.3 + Sleep_score * 0.3)
                "query": '''
                SELECT 
                    ((COALESCE(hrv_score, 50) * 0.4) + (COALESCE(rhr_score, 50) * 0.3) + (COALESCE(sleep_score, 50) * 0.3)) as "Readiness Score"
                FROM (
                    SELECT 
                        last("hrv_sdnn") * 1.2 as hrv_score,
                        (100 - last("resting_heart_rate")) as rhr_score,
                        last("duration")/60 * 12.5 as sleep_score
                    FROM "heart_metrics", "sleep_metrics" 
                    WHERE time >= now() - 1d
                )
                ''',
                "rawQuery": True,
                "refId": "A",
                "resultFormat": "time_series"
            }],
            "title": "Readiness Score",
            "type": "gauge"
        })
        
        # Training Load (ACWR)
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "thresholds"},
                    "mappings": [
                        {"options": {"from": 0.8, "to": 1.3}, "type": "range", "result": {"text": "Optimal"}},
                        {"options": {"from": 1.3, "to": 1.5}, "type": "range", "result": {"text": "Caution"}},
                        {"options": {"from": 1.5, "to": None}, "type": "range", "result": {"text": "High Risk"}}
                    ],
                    "thresholds": {
                        "mode": "absolute", 
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 1.3},
                            {"color": "red", "value": 1.5}
                        ]
                    },
                    "unit": "none"
                }
            },
            "gridPos": {"h": 8, "w": 8, "x": 8, "y": self.current_y},
            "options": {
                "colorMode": "background",
                "graphMode": "area",
                "justifyMode": "center",
                "orientation": "horizontal",
                "reduceOptions": {"calcs": ["lastNotNull"]}
            },
            "targets": [{
                "datasource": self.get_base_datasource(),
                "query": '''
                SELECT 
                    (acute_load / chronic_load) as "ACWR"
                FROM (
                    SELECT 
                        mean("duration") * mean("value") as acute_load
                    FROM "workout_sessions" 
                    WHERE time >= now() - 7d
                ),
                (
                    SELECT 
                        mean("duration") * mean("value") as chronic_load
                    FROM "workout_sessions" 
                    WHERE time >= now() - 28d
                )
                ''',
                "rawQuery": True,
                "refId": "A"
            }],
            "title": "Training Load (ACWR)",
            "type": "stat"
        })
        
        # Weekly Exercise Streak
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "palette-classic"},
                    "custom": {
                        "fillOpacity": 80,
                        "gradientMode": "none",
                        "hideFrom": {"legend": False, "tooltip": False, "viz": False},
                        "lineWidth": 1
                    },
                    "mappings": [],
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [{"color": "green", "value": None}]
                    },
                    "unit": "min"
                }
            },
            "gridPos": {"h": 8, "w": 8, "x": 16, "y": self.current_y},
            "options": {
                "barRadius": 0,
                "barWidth": 0.97,
                "groupWidth": 0.7,
                "legend": {"calcs": [], "displayMode": "list", "placement": "bottom"},
                "orientation": "vertical",
                "showValue": "auto",
                "stacking": "none",
                "tooltip": {"mode": "single", "sort": "none"}
            },
            "targets": [{
                "datasource": self.get_base_datasource(),
                "query": 'SELECT sum("exercise_time") as "Exercise Minutes" FROM "energy_metrics" WHERE "type" = \'HKQuantityTypeIdentifierAppleExerciseTime\' AND $timeFilter GROUP BY time(1d) fill(0)',
                "rawQuery": True,
                "refId": "A"
            }],
            "title": "Weekly Exercise Streak",
            "type": "barchart"
        })
        
        self.current_y += 8

    def create_training_performance_tab(self) -> None:
        """Create Training & Performance tab (Tab 2)."""
        self.add_row("🏃‍♂️ Workout Analysis")
        
        # Workouts table (last 30 days)
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "custom": {
                        "align": "center",
                        "cellOptions": {"type": "auto"},
                        "filterable": True,
                        "inspect": False
                    },
                    "mappings": [],
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [{"color": "green", "value": None}]
                    }
                },
                "overrides": [
                    {
                        "matcher": {"id": "byName", "options": "Duration"},
                        "properties": [{"id": "unit", "value": "s"}]
                    },
                    {
                        "matcher": {"id": "byName", "options": "Distance"},
                        "properties": [{"id": "unit", "value": "m"}]
                    }
                ]
            },
            "gridPos": {"h": 12, "w": 24, "x": 0, "y": self.current_y},
            "options": {
                "cellHeight": "sm",
                "footer": {"countRows": False, "fields": "", "reducer": ["sum"], "show": False},
                "showHeader": True,
                "sortBy": [{"desc": True, "displayName": "time"}]
            },
            "targets": [{
                "datasource": self.get_base_datasource(),
                "query": '''
                SELECT 
                    "activity_type" as "Type",
                    "duration" as "Duration", 
                    "distance" as "Distance",
                    "value" as "Energy",
                    time as "Date"
                FROM "workout_sessions" 
                WHERE $timeFilter 
                ORDER BY time DESC
                LIMIT 50
                ''',
                "rawQuery": True,
                "refId": "A",
                "resultFormat": "table"
            }],
            "title": "Recent Workouts (Last 30 Days)",
            "type": "table"
        })
        
        self.current_y += 12
        
        # Training Load Analysis
        self.add_row("📈 Training Load Analysis")
        
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "palette-classic"},
                    "custom": {
                        "axisCenteredZero": False,
                        "axisColorMode": "text",
                        "axisLabel": "Training Load",
                        "drawStyle": "line",
                        "fillOpacity": 10,
                        "lineInterpolation": "smooth",
                        "lineWidth": 2,
                        "showPoints": "auto"
                    },
                    "unit": "short"
                }
            },
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": self.current_y},
            "options": {
                "legend": {"calcs": ["mean"], "displayMode": "list", "placement": "bottom"},
                "tooltip": {"mode": "multi"}
            },
            "targets": [
                {
                    "datasource": self.get_base_datasource(),
                    "query": '''
                    SELECT 
                        mean("duration" * "value" / 1000) as "Acute Load (7d)"
                    FROM "workout_sessions" 
                    WHERE $timeFilter 
                    GROUP BY time(1d)
                    ''',
                    "rawQuery": True,
                    "refId": "A"
                },
                {
                    "datasource": self.get_base_datasource(),
                    "query": '''
                    SELECT 
                        mean("duration" * "value" / 4000) as "Chronic Load (28d)"
                    FROM "workout_sessions" 
                    WHERE time >= now() - 28d 
                    GROUP BY time(1d)
                    ''',
                    "rawQuery": True,
                    "refId": "B"
                }
            ],
            "title": "Training Load (TSB Style)",
            "type": "timeseries"
        })
        
        # VO2 Max Trend
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "continuous-GrYlRd"},
                    "custom": {
                        "axisLabel": "ml/kg/min",
                        "drawStyle": "line",
                        "fillOpacity": 20,
                        "lineWidth": 3,
                        "showPoints": "auto"
                    },
                    "unit": "short"
                }
            },
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": self.current_y},
            "options": {
                "legend": {"displayMode": "list", "placement": "bottom"},
                "tooltip": {"mode": "single"}
            },
            "targets": [{
                "datasource": self.get_base_datasource(),
                "query": 'SELECT mean("vo2_max") as "VO₂ Max" FROM "fitness_metrics" WHERE "type" = \'HKQuantityTypeIdentifierVO2Max\' AND $timeFilter GROUP BY time(7d) fill(null)',
                "rawQuery": True,
                "refId": "A"
            }],
            "title": "VO₂ Max Trend (12-week rolling)",
            "type": "timeseries"
        })
        
        self.current_y += 8

    def create_recovery_sleep_tab(self) -> None:
        """Create Recovery & Sleep tab (Tab 3)."""
        self.add_row("😴 Sleep Analysis")
        
        # Sleep duration & efficiency
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "palette-classic"},
                    "custom": {
                        "fillOpacity": 80,
                        "gradientMode": "none",
                        "lineWidth": 1,
                        "stacking": {"group": "A", "mode": "normal"}
                    },
                    "unit": "h"
                }
            },
            "gridPos": {"h": 8, "w": 16, "x": 0, "y": self.current_y},
            "options": {
                "barRadius": 0,
                "barWidth": 0.97,
                "groupWidth": 0.7,
                "legend": {"calcs": [], "displayMode": "list", "placement": "bottom"},
                "orientation": "vertical",
                "showValue": "never",
                "stacking": "normal"
            },
            "targets": [{
                "datasource": self.get_base_datasource(),
                "query": '''
                SELECT 
                    sum("duration")/60 as "Total Sleep"
                FROM "sleep_metrics" 
                WHERE "type" = 'HKCategoryTypeIdentifierSleepAnalysis' AND "sleep_state" = 'HKCategoryValueSleepAnalysisAsleep'
                AND $timeFilter 
                GROUP BY time(1d) fill(0)
                ''',
                "rawQuery": True,
                "refId": "A"
            }],
            "title": "Sleep Duration & Efficiency",
            "type": "barchart"
        })
        
        # Sleep Timeline
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "thresholds"},
                    "custom": {
                        "fillOpacity": 70,
                        "lineWidth": 0,
                        "spanNulls": False
                    },
                    "mappings": [
                        {
                            "options": {
                                "0": {"color": "light-blue", "index": 0, "text": "Awake"},
                                "1": {"color": "dark-blue", "index": 1, "text": "Asleep"}
                            },
                            "type": "value"
                        }
                    ],
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [{"color": "light-blue", "value": None}]
                    }
                }
            },
            "gridPos": {"h": 8, "w": 8, "x": 16, "y": self.current_y},
            "options": {
                "alignValue": "center",
                "legend": {"displayMode": "list", "placement": "bottom"},
                "mergeValues": True,
                "rowHeight": 0.9,
                "showValue": "never"
            },
            "targets": [{
                "datasource": self.get_base_datasource(),
                "query": 'SELECT mean("value") as "Sleep State" FROM "sleep_metrics" WHERE "type" = \'HKCategoryTypeIdentifierSleepAnalysis\' AND $timeFilter GROUP BY time(10m), "sleep_state" fill(null)',
                "rawQuery": True,
                "refId": "A"
            }],
            "title": "Sleep Timeline",
            "type": "state-timeline"
        })
        
        self.current_y += 8
        
        # HRV & RHR Recovery Metrics
        self.add_row("💓 Recovery Metrics")
        
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "palette-classic"},
                    "custom": {
                        "axisCenteredZero": False,
                        "axisColorMode": "text",
                        "drawStyle": "line",
                        "fillOpacity": 10,
                        "lineInterpolation": "smooth",
                        "lineWidth": 2,
                        "showPoints": "auto"
                    }
                },
                "overrides": [
                    {
                        "matcher": {"id": "byName", "options": "HRV SDNN"},
                        "properties": [
                            {"id": "unit", "value": "ms"},
                            {"id": "custom.axisPlacement", "value": "left"}
                        ]
                    },
                    {
                        "matcher": {"id": "byName", "options": "Resting HR"},
                        "properties": [
                            {"id": "unit", "value": "bpm"},
                            {"id": "custom.axisPlacement", "value": "right"}
                        ]
                    }
                ]
            },
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": self.current_y},
            "options": {
                "legend": {"calcs": ["mean", "last"], "displayMode": "table", "placement": "bottom"},
                "tooltip": {"mode": "multi"}
            },
            "targets": [
                {
                    "datasource": self.get_base_datasource(),
                    "query": 'SELECT mean("hrv_sdnn") as "HRV SDNN" FROM "heart_metrics" WHERE "type" = \'HKQuantityTypeIdentifierHeartRateVariabilitySDNN\' AND $timeFilter GROUP BY time($__interval) fill(null)',
                    "rawQuery": True,
                    "refId": "A"
                },
                {
                    "datasource": self.get_base_datasource(),
                    "query": 'SELECT mean("resting_heart_rate") as "Resting HR" FROM "heart_metrics" WHERE "type" = \'HKQuantityTypeIdentifierRestingHeartRate\' AND $timeFilter GROUP BY time($__interval) fill(null)',
                    "rawQuery": True,
                    "refId": "B"
                }
            ],
            "title": "Nightly HRV & RHR with Baseline",
            "type": "timeseries"
        })
        
        # Heart Rate Recovery
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "continuous-BlPu"},
                    "custom": {
                        "drawStyle": "points",
                        "lineWidth": 2,
                        "pointSize": 8,
                        "showPoints": "always"
                    },
                    "unit": "bpm"
                }
            },
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": self.current_y},
            "options": {
                "legend": {"calcs": ["mean", "count"], "displayMode": "table", "placement": "bottom"},
                "tooltip": {"mode": "single"}
            },
            "targets": [{
                "datasource": self.get_base_datasource(),
                "query": 'SELECT "value" as "1-Min Recovery" FROM "heart_metrics" WHERE "type" = \'HKQuantityTypeIdentifierHeartRateRecoveryOneMinute\' AND $timeFilter',
                "rawQuery": True,
                "refId": "A"
            }],
            "title": "Heart Rate Recovery (Post-Workout)",
            "type": "timeseries"
        })
        
        self.current_y += 8

    def create_daily_health_markers_tab(self) -> None:
        """Create Daily Health Markers tab (Tab 4)."""
        self.add_row("🏥 Health Vitals")
        
        # Resting HR 28-day trend
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "continuous-RdYlGn", "reverse": True},
                    "custom": {
                        "axisLabel": "BPM",
                        "drawStyle": "line",
                        "fillOpacity": 20,
                        "lineWidth": 3,
                        "showPoints": "auto"
                    },
                    "unit": "bpm"
                }
            },
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": self.current_y},
            "options": {
                "legend": {"displayMode": "list", "placement": "bottom"},
                "tooltip": {"mode": "single"}
            },
            "targets": [{
                "datasource": self.get_base_datasource(),
                "query": 'SELECT mean("resting_heart_rate") as "Resting HR" FROM "heart_metrics" WHERE "type" = \'HKQuantityTypeIdentifierRestingHeartRate\' AND $timeFilter GROUP BY time(1d) fill(null)',
                "rawQuery": True,
                "refId": "A"
            }],
            "title": "Resting HR (28-day trend)",
            "type": "timeseries"
        })
        
        # SpO₂ nightly avg & min
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "palette-classic"},
                    "custom": {
                        "axisLabel": "%",
                        "drawStyle": "line",
                        "fillOpacity": 10,
                        "lineWidth": 2,
                        "showPoints": "auto"
                    },
                    "unit": "percent"
                }
            },
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": self.current_y},
            "options": {
                "legend": {"calcs": ["mean", "min"], "displayMode": "table", "placement": "bottom"},
                "tooltip": {"mode": "multi"}
            },
            "targets": [
                {
                    "datasource": self.get_base_datasource(),
                    "query": 'SELECT mean("oxygen_saturation") as "SpO₂ Average" FROM "respiratory_metrics" WHERE "type" = \'HKQuantityTypeIdentifierOxygenSaturation\' AND $timeFilter GROUP BY time(1d) fill(null)',
                    "rawQuery": True,
                    "refId": "A"
                },
                {
                    "datasource": self.get_base_datasource(),
                    "query": 'SELECT min("oxygen_saturation") as "SpO₂ Minimum" FROM "respiratory_metrics" WHERE "type" = \'HKQuantityTypeIdentifierOxygenSaturation\' AND $timeFilter GROUP BY time(1d) fill(null)',
                    "rawQuery": True,
                    "refId": "B"
                }
            ],
            "title": "SpO₂ Nightly Average & Minimum",
            "type": "timeseries"
        })
        
        self.current_y += 8
        
        # Respiratory Rate with anomaly detection
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "continuous-BlYlRd"},
                    "custom": {
                        "axisLabel": "breaths/min",
                        "drawStyle": "line",
                        "fillOpacity": 15,
                        "lineWidth": 2,
                        "showPoints": "auto",
                        "thresholdsStyle": {"mode": "area"}
                    },
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 12},
                            {"color": "red", "value": 20}
                        ]
                    },
                    "unit": "respirations"
                }
            },
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": self.current_y},
            "options": {
                "legend": {"calcs": ["mean", "stdDev"], "displayMode": "table", "placement": "bottom"},
                "tooltip": {"mode": "single"}
            },
            "targets": [{
                "datasource": self.get_base_datasource(),
                "query": 'SELECT mean("respiratory_rate") as "Respiratory Rate" FROM "respiratory_metrics" WHERE "type" = \'HKQuantityTypeIdentifierRespiratoryRate\' AND $timeFilter GROUP BY time($__interval) fill(null)',
                "rawQuery": True,
                "refId": "A"
            }],
            "title": "Respiratory Rate with Anomaly Detection",
            "type": "timeseries"
        })
        
        self.current_y += 8

    def create_stress_readiness_tab(self) -> None:
        """Create Stress & Readiness tab (Tab 5)."""
        self.add_row("🧠 Stress Analysis")
        
        # Stress proxy: HRV vs HR correlation
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "continuous-RdYlBu"},
                    "custom": {
                        "drawStyle": "points",
                        "pointSize": 6,
                        "showPoints": "always"
                    },
                    "unit": "short"
                }
            },
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": self.current_y},
            "options": {
                "legend": {"displayMode": "list", "placement": "bottom"},
                "tooltip": {"mode": "single"}
            },
            "targets": [{
                "datasource": self.get_base_datasource(),
                "query": '''
                SELECT 
                    ("hrv_sdnn" / "heart_rate" * 100) as "Stress Index"
                FROM "heart_metrics" 
                WHERE $timeFilter AND "hrv_sdnn" IS NOT NULL AND "heart_rate" IS NOT NULL
                ''',
                "rawQuery": True,
                "refId": "A"
            }],
            "title": "Daytime Stress Proxy (HRV/HR Ratio)",
            "type": "timeseries"
        })
        
        # Readiness Score Breakdown
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "palette-classic"},
                    "custom": {
                        "fillOpacity": 80,
                        "gradientMode": "none",
                        "lineWidth": 1,
                        "stacking": {"group": "A", "mode": "normal"}
                    },
                    "max": 100,
                    "min": 0,
                    "unit": "percent"
                }
            },
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": self.current_y},
            "options": {
                "barRadius": 0,
                "barWidth": 0.97,
                "groupWidth": 0.7,
                "legend": {"calcs": [], "displayMode": "list", "placement": "bottom"},
                "orientation": "vertical",
                "showValue": "auto",
                "stacking": "normal"
            },
            "targets": [
                {
                    "datasource": self.get_base_datasource(),
                    "query": 'SELECT last("hrv_sdnn") * 1.2 as "HRV Score" FROM "heart_metrics" WHERE "type" = \'HKQuantityTypeIdentifierHeartRateVariabilitySDNN\' AND $timeFilter GROUP BY time(1d)',
                    "rawQuery": True,
                    "refId": "A"
                },
                {
                    "datasource": self.get_base_datasource(),
                    "query": 'SELECT (100 - last("resting_heart_rate")) as "RHR Score" FROM "heart_metrics" WHERE "type" = \'HKQuantityTypeIdentifierRestingHeartRate\' AND $timeFilter GROUP BY time(1d)',
                    "rawQuery": True,
                    "refId": "B"
                },
                {
                    "datasource": self.get_base_datasource(),
                    "query": 'SELECT (sum("duration")/60 * 12.5) as "Sleep Score" FROM "sleep_metrics" WHERE "type" = \'HKCategoryTypeIdentifierSleepAnalysis\' AND $timeFilter GROUP BY time(1d)',
                    "rawQuery": True,
                    "refId": "C"
                }
            ],
            "title": "Readiness Score Breakdown",
            "type": "barchart"
        })
        
        self.current_y += 8

    def create_data_quality_ops_tab(self) -> None:
        """Create Data Quality & Ops tab (Tab 6)."""
        self.add_row("🔍 Data Quality Monitoring")
        
        # Missing data heatmap
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "color": {
                        "mode": "continuous-RdYlGn",
                        "reverse": True
                    },
                    "custom": {
                        "hideFrom": {"legend": False, "tooltip": False, "viz": False}
                    },
                    "mappings": [],
                    "unit": "percent"
                }
            },
            "gridPos": {"h": 8, "w": 16, "x": 0, "y": self.current_y},
            "options": {
                "calculate": False,
                "calculation": {},
                "cellGap": 2,
                "cellValues": {"unit": "percent"},
                "color": {"exponent": 0.5, "fill": "dark-orange", "mode": "continuous", "reverse": False, "scheme": "RdYlGn", "steps": 64},
                "exemplars": {"color": "rgba(255,0,255,0.7)"},
                "filterValues": {"le": 1e-9},
                "legend": {"show": False},
                "rowsFrame": {"layout": "auto"},
                "tooltip": {"show": True, "yHistogram": False},
                "yAxis": {"axisPlacement": "left", "reverse": False}
            },
            "targets": [{
                "datasource": self.get_base_datasource(),
                "query": '''
                SELECT 
                    (COUNT("heart_rate") * 100.0 / 1440) as "heart_metrics",
                    (COUNT("steps") * 100.0 / 1440) as "movement_metrics",
                    (COUNT("duration") * 100.0 / 24) as "sleep_metrics"
                FROM "heart_metrics", "movement_metrics", "sleep_metrics"
                WHERE $timeFilter 
                GROUP BY time(1h) fill(0)
                ''',
                "rawQuery": True,
                "refId": "A"
            }],
            "title": "Data Completeness Heatmap (by hour)",
            "type": "heatmap"
        })
        
        # Ingestion lag and data freshness
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "thresholds"},
                    "mappings": [],
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 300},  # 5 minutes
                            {"color": "red", "value": 900}      # 15 minutes
                        ]
                    },
                    "unit": "s"
                }
            },
            "gridPos": {"h": 4, "w": 8, "x": 16, "y": self.current_y},
            "options": {
                "colorMode": "background",
                "graphMode": "area",
                "justifyMode": "center",
                "orientation": "horizontal",
                "reduceOptions": {"calcs": ["lastNotNull"]}
            },
            "targets": [{
                "datasource": self.get_base_datasource(),
                "query": 'SELECT (now() - max(time)) as "Data Lag" FROM "heart_metrics"',
                "rawQuery": True,
                "refId": "A"
            }],
            "title": "Data Freshness",
            "type": "stat"
        })
        
        # Outlier Detection
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "palette-classic"},
                    "custom": {
                        "drawStyle": "points",
                        "pointSize": 8,
                        "showPoints": "always"
                    },
                    "unit": "short"
                }
            },
            "gridPos": {"h": 4, "w": 8, "x": 16, "y": self.current_y + 4},
            "options": {
                "legend": {"displayMode": "list", "placement": "bottom"},
                "tooltip": {"mode": "single"}
            },
            "targets": [{
                "datasource": self.get_base_datasource(),
                "query": '''
                SELECT 
                    ABS("heart_rate" - mean("heart_rate")) / stddev("heart_rate") as "HR Z-Score"
                FROM "heart_metrics" 
                WHERE "type" = 'HKQuantityTypeIdentifierHeartRate' AND $timeFilter
                HAVING ABS("heart_rate" - mean("heart_rate")) / stddev("heart_rate") > 3
                ''',
                "rawQuery": True,
                "refId": "A"
            }],
            "title": "Outlier Detection (Z-Score > 3)",
            "type": "timeseries"
        })
        
        self.current_y += 8
        
        # Data source statistics
        self.add_panel({
            "datasource": self.get_base_datasource(),
            "fieldConfig": {
                "defaults": {
                    "custom": {
                        "align": "auto",
                        "cellOptions": {"type": "auto"},
                        "inspect": False
                    },
                    "mappings": [],
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [{"color": "green", "value": None}]
                    }
                }
            },
            "gridPos": {"h": 6, "w": 24, "x": 0, "y": self.current_y},
            "options": {
                "cellHeight": "sm",
                "footer": {"countRows": False, "fields": "", "reducer": ["sum"], "show": False},
                "showHeader": True
            },
            "targets": [{
                "datasource": self.get_base_datasource(),
                "query": '''
                SELECT 
                    'heart_metrics' as "Measurement",
                    COUNT(*) as "Records",
                    min(time) as "First Record", 
                    max(time) as "Last Record"
                FROM "heart_metrics"
                UNION ALL
                SELECT 
                    'movement_metrics' as "Measurement",
                    COUNT(*) as "Records", 
                    min(time) as "First Record",
                    max(time) as "Last Record"
                FROM "movement_metrics"
                ''',
                "rawQuery": True,
                "refId": "A",
                "resultFormat": "table"
            }],
            "title": "Data Source Statistics",
            "type": "table"
        })
        
        self.current_y += 6

    def build_dashboard(self) -> Dict:
        """Build the complete ultimate dashboard."""
        print("🏗️  Building Ultimate Apple Health Dashboard...")
        
        # Build all tabs as collapsed rows
        self.add_row("📊 1. Overview (Today's Summary)", collapsed=True)
        overview_start_y = self.current_y
        self.create_overview_tab()
        
        # Collapse the Overview section
        overview_panels = []
        for panel in self.dashboard["panels"][1:]:  # Skip the row itself
            if panel.get("gridPos", {}).get("y", 0) >= overview_start_y:
                overview_panels.append(panel)
        
        # Remove panels from main dashboard and add to row
        for panel in overview_panels:
            self.dashboard["panels"].remove(panel)
        
        self.dashboard["panels"][0]["panels"] = overview_panels
        self.dashboard["panels"][0]["collapsed"] = True
        
        # Reset position counter
        self.current_y = 1
        
        # Build other tabs
        self.add_row("🏃‍♂️ 2. Training & Performance", collapsed=True)
        self.create_training_performance_tab()
        
        self.add_row("😴 3. Recovery & Sleep", collapsed=True)  
        self.create_recovery_sleep_tab()
        
        self.add_row("🏥 4. Daily Health Markers", collapsed=True)
        self.create_daily_health_markers_tab()
        
        self.add_row("🧠 5. Stress & Readiness", collapsed=True)
        self.create_stress_readiness_tab()
        
        self.add_row("🔍 6. Data Quality & Ops", collapsed=True)
        self.create_data_quality_ops_tab()
        
        print("✅ Ultimate dashboard structure completed!")
        return self.dashboard

def main():
    print("🚀 Creating Ultimate Apple Health Dashboard...")
    
    builder = UltimateDashboardBuilder()
    ultimate_dashboard = builder.build_dashboard()
    
    # Save the dashboard
    output_file = "grafana_dashboard_ultimate.json"
    with open(output_file, 'w') as f:
        json.dump(ultimate_dashboard, f, indent=2)
    
    print(f"✅ Ultimate dashboard saved as: {output_file}")
    print(f"📊 Dashboard contains {len(ultimate_dashboard['panels'])} panels across 6 sections")
    print(f"🎯 Features:")
    print(f"   • Today's summary with readiness scoring")
    print(f"   • Training load analysis (ACWR)")
    print(f"   • Advanced recovery metrics (HRV, RHR)")
    print(f"   • Sleep analysis with efficiency tracking")
    print(f"   • Stress monitoring via HRV/HR correlation")
    print(f"   • Data quality monitoring and outlier detection")
    print(f"   • 6-tab organized structure for focused analysis")

if __name__ == '__main__':
    main()