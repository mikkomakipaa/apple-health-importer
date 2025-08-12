#!/usr/bin/env python3
"""
Create a properly fixed sleep timeline panel that works with InfluxDB limitations.
"""

import json

def fix_sleep_timeline_specifically():
    """Create a corrected sleep timeline panel."""
    
    # Load the fixed dashboard
    with open('grafana_dashboard_fixed.json', 'r') as f:
        dashboard = json.load(f)
    
    # Find and fix the sleep timeline panel
    for panel in dashboard.get('panels', []):
        if panel.get('title') == 'Sleep Timeline':
            print("🔧 Fixing Sleep Timeline panel with InfluxDB-compatible query...")
            
            # Update the query to work with InfluxDB's limitations
            for target in panel.get('targets', []):
                # Simple approach: show sleep duration as a value, use grouping for timeline
                target['query'] = '''SELECT mean("value") AS "Sleep State" FROM "sleep_metrics" WHERE $timeFilter AND "type" = 'HKCategoryTypeIdentifierSleepAnalysis' GROUP BY time(10m), "sleep_state" fill(null)'''
                target['resultFormat'] = 'time_series'
                print("   ✓ Updated to use time-grouped sleep state data")
            
            # Update visualization to work better with this data
            panel['type'] = 'timeseries'  # Change from state-timeline to timeseries
            panel['fieldConfig']['defaults'].update({
                "custom": {
                    "drawStyle": "bars",
                    "fillOpacity": 80,
                    "lineWidth": 0,
                    "pointSize": 5,
                    "showPoints": "never",
                    "spanNulls": False,
                    "stacking": {
                        "group": "A",
                        "mode": "normal"
                    }
                },
                "mappings": [],
                "unit": "short"
            })
            
            # Update overrides to color different sleep states
            panel['fieldConfig']['overrides'] = [
                {
                    "matcher": {
                        "id": "byRegexp",
                        "options": ".*InBed.*"
                    },
                    "properties": [
                        {
                            "id": "color",
                            "value": {
                                "mode": "fixed",
                                "fixedColor": "light-blue"
                            }
                        },
                        {
                            "id": "displayName",
                            "value": "In Bed"
                        }
                    ]
                },
                {
                    "matcher": {
                        "id": "byRegexp", 
                        "options": ".*Asleep.*"
                    },
                    "properties": [
                        {
                            "id": "color",
                            "value": {
                                "mode": "fixed",
                                "fixedColor": "dark-blue"
                            }
                        },
                        {
                            "id": "displayName",
                            "value": "Asleep"
                        }
                    ]
                },
                {
                    "matcher": {
                        "id": "byRegexp",
                        "options": ".*Awake.*"
                    },
                    "properties": [
                        {
                            "id": "color",
                            "value": {
                                "mode": "fixed",
                                "fixedColor": "red"
                            }
                        },
                        {
                            "id": "displayName",
                            "value": "Awake"
                        }
                    ]
                }
            ]
            
            print("   ✓ Updated visualization type and color coding")
            break
    
    # Save the updated dashboard
    with open('grafana_dashboard_fixed.json', 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print("✅ Sleep Timeline panel fixed and saved")

if __name__ == '__main__':
    fix_sleep_timeline_specifically()