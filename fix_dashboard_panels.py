#!/usr/bin/env python3
"""
Fix specific panels in the Grafana dashboard based on actual InfluxDB data structure.
"""

import json
import argparse

def fix_heart_rate_recovery_panel(dashboard):
    """Fix the Heart Rate Recovery panel query."""
    for panel in dashboard.get('panels', []):
        if panel.get('title') == 'Heart Rate Recovery':
            print("🔧 Fixing Heart Rate Recovery panel...")
            # Update the query to use 'value' field instead of 'heart_rate'
            for target in panel.get('targets', []):
                if 'HKQuantityTypeIdentifierHeartRateRecoveryOneMinute' in target.get('query', ''):
                    target['query'] = 'SELECT "value" AS "1-Min Recovery (BPM)" FROM "heart_metrics" WHERE $timeFilter AND "type" = \'HKQuantityTypeIdentifierHeartRateRecoveryOneMinute\''
                    print("   ✓ Updated query to use 'value' field")
            
            # Update field config for proper units
            if 'fieldConfig' in panel and 'defaults' in panel['fieldConfig']:
                panel['fieldConfig']['defaults']['unit'] = 'bpm'
            
            return True
    return False

def fix_sleep_timeline_panel(dashboard):
    """Fix the Sleep Timeline panel query."""
    for panel in dashboard.get('panels', []):
        if panel.get('title') == 'Sleep Timeline':
            print("🔧 Fixing Sleep Timeline panel...")
            
            # Update the query to use sleep_state tag for visualization
            for target in panel.get('targets', []):
                target['query'] = '''
SELECT 
  CASE 
    WHEN "sleep_state" = 'HKCategoryValueSleepAnalysisInBed' THEN 0
    WHEN "sleep_state" = 'HKCategoryValueSleepAnalysisAsleep' THEN 1
    WHEN "sleep_state" = 'HKCategoryValueSleepAnalysisAwake' THEN 0
    ELSE 0
  END AS "Sleep State"
FROM "sleep_metrics" 
WHERE $timeFilter AND "type" = 'HKCategoryTypeIdentifierSleepAnalysis'
'''.strip()
                print("   ✓ Updated query to use sleep_state tag")
            
            # Update the mappings for proper sleep state visualization
            if 'fieldConfig' in panel and 'defaults' in panel['fieldConfig']:
                panel['fieldConfig']['defaults']['mappings'] = [
                    {
                        "options": {
                            "0": {
                                "color": "light-blue",
                                "index": 0,
                                "text": "Awake/In Bed"
                            },
                            "1": {
                                "color": "dark-blue", 
                                "index": 1,
                                "text": "Asleep"
                            }
                        },
                        "type": "value"
                    }
                ]
                print("   ✓ Updated state mappings")
            
            return True
    return False

def fix_hrv_panel(dashboard):
    """Fix HRV panel to use correct field name."""
    for panel in dashboard.get('panels', []):
        if panel.get('title') == 'HRV & Respiratory Health':
            print("🔧 Fixing HRV & Respiratory Health panel...")
            
            for target in panel.get('targets', []):
                query = target.get('query', '')
                if 'hrv_sdnn' in query and 'HKQuantityTypeIdentifierHeartRateVariabilitySDNN' in query:
                    # Update to use 'value' field for HRV
                    target['query'] = 'SELECT mean("value") AS "HRV SDNN" FROM "heart_metrics" WHERE $timeFilter AND "type" = \'HKQuantityTypeIdentifierHeartRateVariabilitySDNN\' GROUP BY time($__interval) fill(null)'
                    print("   ✓ Updated HRV query to use 'value' field")
                elif 'oxygen_saturation' in query:
                    # Update to use 'value' field for oxygen saturation  
                    target['query'] = 'SELECT mean("value") AS "Oxygen Saturation" FROM "respiratory_metrics" WHERE $timeFilter AND "type" = \'HKQuantityTypeIdentifierOxygenSaturation\' GROUP BY time($__interval) fill(null)'
                    print("   ✓ Updated O2 saturation query to use 'value' field")
            
            return True
    return False

def fix_body_composition_panel(dashboard):
    """Fix body composition panel to use correct field names."""
    for panel in dashboard.get('panels', []):
        if panel.get('title') == 'Body Composition':
            print("🔧 Fixing Body Composition panel...")
            
            for target in panel.get('targets', []):
                query = target.get('query', '')
                if 'HKQuantityTypeIdentifierBodyMass' in query:
                    target['query'] = 'SELECT mean("weight") AS "Weight" FROM "body_composition" WHERE $timeFilter AND "type" = \'HKQuantityTypeIdentifierBodyMass\' GROUP BY time($__interval) fill(null)'
                    print("   ✓ Updated weight query")
                elif 'HKQuantityTypeIdentifierHeight' in query:
                    target['query'] = 'SELECT mean("height") AS "Height" FROM "body_composition" WHERE $timeFilter AND "type" = \'HKQuantityTypeIdentifierHeight\' GROUP BY time($__interval) fill(null)'
                    print("   ✓ Updated height query")
            
            return True
    return False

def fix_respiratory_rate_panel(dashboard):
    """Fix respiratory rate panel."""
    for panel in dashboard.get('panels', []):
        if panel.get('title') == 'Respiratory Rate':
            print("🔧 Fixing Respiratory Rate panel...")
            
            for target in panel.get('targets', []):
                if 'respiratory_rate' in target.get('query', ''):
                    target['query'] = 'SELECT mean("respiratory_rate") AS "Respiratory Rate" FROM "respiratory_metrics" WHERE $timeFilter AND "type" = \'HKQuantityTypeIdentifierRespiratoryRate\' GROUP BY time($__interval) fill(null)'
                    print("   ✓ Updated respiratory rate query to use correct field")
            
            return True
    return False

def fix_energy_panels(dashboard):
    """Fix energy expenditure panels."""
    for panel in dashboard.get('panels', []):
        if panel.get('title') == 'Daily Energy Expenditure':
            print("🔧 Fixing Daily Energy Expenditure panel...")
            
            for target in panel.get('targets', []):
                query = target.get('query', '')
                if 'active_energy' in query:
                    target['query'] = 'SELECT sum("active_energy") AS "Active Energy" FROM "energy_metrics" WHERE $timeFilter AND "type" = \'HKQuantityTypeIdentifierActiveEnergyBurned\' GROUP BY time(1d) fill(0)'
                    print("   ✓ Updated active energy query")
                elif 'basal_energy' in query:
                    target['query'] = 'SELECT sum("basal_energy") AS "Basal Energy" FROM "energy_metrics" WHERE $timeFilter AND "type" = \'HKQuantityTypeIdentifierBasalEnergyBurned\' GROUP BY time(1d) fill(0)'
                    print("   ✓ Updated basal energy query")
            
            return True
    return False

def fix_movement_panels(dashboard):
    """Fix movement metrics panels."""
    for panel in dashboard.get('panels', []):
        if panel.get('title') == 'Daily Movement Metrics':
            print("🔧 Fixing Daily Movement Metrics panel...")
            
            for target in panel.get('targets', []):
                query = target.get('query', '')
                if 'steps' in query:
                    target['query'] = 'SELECT sum("steps") AS "Steps" FROM "movement_metrics" WHERE $timeFilter AND "type" = \'HKQuantityTypeIdentifierStepCount\' GROUP BY time(1d) fill(0)'
                    print("   ✓ Updated steps query")
                elif 'distance' in query and 'Walking' in query:
                    target['query'] = 'SELECT sum("distance") AS "Distance" FROM "movement_metrics" WHERE $timeFilter AND "type" = \'HKQuantityTypeIdentifierDistanceWalkingRunning\' GROUP BY time(1d) fill(0)'
                    print("   ✓ Updated distance query")
                elif 'flights' in query:
                    target['query'] = 'SELECT sum("flights") AS "Flights Climbed" FROM "movement_metrics" WHERE $timeFilter AND "type" = \'HKQuantityTypeIdentifierFlightsClimbed\' GROUP BY time(1d) fill(0)'
                    print("   ✓ Updated flights query")
            
            return True
    return False

def fix_sleep_duration_panel(dashboard):
    """Fix sleep duration panel."""
    for panel in dashboard.get('panels', []):
        if panel.get('title') == 'Daily Sleep Duration':
            print("🔧 Fixing Daily Sleep Duration panel...")
            
            for target in panel.get('targets', []):
                # Use duration field directly (already in minutes)
                target['query'] = 'SELECT sum("duration")/60 AS "Sleep Duration" FROM "sleep_metrics" WHERE $timeFilter AND "type" = \'HKCategoryTypeIdentifierSleepAnalysis\' GROUP BY time(1d) fill(0)'
                print("   ✓ Updated sleep duration query")
            
            return True
    return False

def main():
    parser = argparse.ArgumentParser(description='Fix Grafana dashboard panel queries')
    parser.add_argument('--input', default='grafana_dashboard_comprehensive.json',
                       help='Input dashboard file')
    parser.add_argument('--output', default='grafana_dashboard_fixed.json',
                       help='Output dashboard file')
    
    args = parser.parse_args()
    
    print(f"📂 Loading dashboard from {args.input}")
    
    # Load dashboard
    with open(args.input, 'r') as f:
        dashboard = json.load(f)
    
    print("🔧 Applying fixes based on actual InfluxDB data structure...")
    
    # Apply fixes
    fixes_applied = []
    
    if fix_heart_rate_recovery_panel(dashboard):
        fixes_applied.append("Heart Rate Recovery")
    
    if fix_sleep_timeline_panel(dashboard):
        fixes_applied.append("Sleep Timeline")
    
    if fix_hrv_panel(dashboard):
        fixes_applied.append("HRV & Respiratory Health")
    
    if fix_body_composition_panel(dashboard):
        fixes_applied.append("Body Composition")
    
    if fix_respiratory_rate_panel(dashboard):
        fixes_applied.append("Respiratory Rate")
    
    if fix_energy_panels(dashboard):
        fixes_applied.append("Energy Expenditure")
    
    if fix_movement_panels(dashboard):
        fixes_applied.append("Movement Metrics")
    
    if fix_sleep_duration_panel(dashboard):
        fixes_applied.append("Sleep Duration")
    
    # Update dashboard version
    dashboard['version'] = dashboard.get('version', 1) + 1
    dashboard['title'] = 'Apple Health Comprehensive Dashboard (Fixed)'
    dashboard['uid'] = 'apple_health_comprehensive_fixed'
    
    # Save fixed dashboard
    with open(args.output, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\n✅ Fixed dashboard saved to {args.output}")
    print(f"🔧 Applied fixes to {len(fixes_applied)} panel groups:")
    for fix in fixes_applied:
        print(f"   ✓ {fix}")
    
    print(f"\n📋 Summary of key fixes:")
    print(f"   • Heart Rate Recovery: Now uses 'value' field")
    print(f"   • Sleep Timeline: Uses sleep_state tag for visualization") 
    print(f"   • HRV/O2 Saturation: Uses 'value' field for both metrics")
    print(f"   • Body Composition: Uses 'weight'/'height' fields")
    print(f"   • All panels: Updated to match actual InfluxDB structure")

if __name__ == '__main__':
    main()