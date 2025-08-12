#!/usr/bin/env python3
"""
Fix the data source UID in the ultimate dashboard to match the actual 
InfluxDB data source UID from Grafana.
"""

import json
import argparse

def get_actual_datasource_uid():
    """
    From the screenshot, we can see the user has a data source named "health".
    We need to find its actual UID to update the dashboard.
    """
    print("📋 Based on your Grafana screenshot, I can see you have:")
    print("   • influxdb (default) - InfluxDB")  
    print("   • health - InfluxDB")
    print("   • portfolio - InfluxDB")
    print()
    print("The dashboard should use the 'health' data source.")
    print()
    
    # Common UID patterns for Grafana data sources
    health_uid_suggestions = [
        "health",
        "influxdb-health", 
        "health-influxdb",
        "P951FEA4DE58B8DFC",  # From original dashboard
        # We'll need the user to provide the actual UID
    ]
    
    return health_uid_suggestions

def update_dashboard_datasource(dashboard_file: str, old_uid: str, new_uid: str) -> str:
    """Update all data source UIDs in the dashboard."""
    
    with open(dashboard_file, 'r') as f:
        dashboard = json.load(f)
    
    print(f"🔄 Updating dashboard data source UID...")
    print(f"   From: {old_uid}")
    print(f"   To: {new_uid}")
    
    updates_count = 0
    
    # Update all panels
    for panel in dashboard.get('panels', []):
        # Update panel-level datasource
        if 'datasource' in panel and panel['datasource'].get('uid') == old_uid:
            panel['datasource']['uid'] = new_uid
            updates_count += 1
        
        # Update target-level datasources
        for target in panel.get('targets', []):
            if 'datasource' in target and target['datasource'].get('uid') == old_uid:
                target['datasource']['uid'] = new_uid
                updates_count += 1
        
        # Update nested panels (for collapsed sections)
        for nested_panel in panel.get('panels', []):
            if 'datasource' in nested_panel and nested_panel['datasource'].get('uid') == old_uid:
                nested_panel['datasource']['uid'] = new_uid
                updates_count += 1
            
            for nested_target in nested_panel.get('targets', []):
                if 'datasource' in nested_target and nested_target['datasource'].get('uid') == old_uid:
                    nested_target['datasource']['uid'] = new_uid
                    updates_count += 1
    
    print(f"   ✅ Updated {updates_count} data source references")
    
    # Update dashboard metadata
    dashboard['version'] = dashboard.get('version', 1) + 1
    dashboard['title'] = dashboard.get('title', '') + ' (Data Source Fixed)'
    
    # Save the updated dashboard
    output_file = dashboard_file.replace('.json', '_fixed_ds.json')
    with open(output_file, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    return output_file

def get_grafana_datasource_info():
    """Instructions to get the actual data source UID."""
    instructions = """
📋 To get your actual 'health' data source UID, follow these steps:

1. **In Grafana**, go to Configuration → Data Sources
2. **Click on your 'health' InfluxDB data source**
3. **Look at the URL** - it will show the UID like:
   http://your-grafana:3000/datasources/edit/YOUR_UID_HERE
   
   OR
   
4. **In the data source settings**, look for "Basic Auth" or "Custom HTTP Headers" section
5. **The UID** is usually displayed somewhere in the interface

Common UID formats:
   • Short: health, influxdb-health
   • UUID: like P951FEA4DE58B8DFC (8-16 characters)
   • Generated: influxdb_uid_12345

🔧 Once you have the UID, run:
   python3 fix_datasource_uid.py --uid YOUR_ACTUAL_UID

Or if you're not sure, try one of these common ones:
"""
    return instructions

def main():
    parser = argparse.ArgumentParser(description='Fix data source UID in dashboard')
    parser.add_argument('--dashboard', default='grafana_dashboard_ultimate.json',
                       help='Dashboard file to fix')
    parser.add_argument('--uid', 
                       help='Your actual health data source UID from Grafana')
    parser.add_argument('--old-uid', default='health_influxdb',
                       help='Old UID to replace (default: health_influxdb)')
    
    args = parser.parse_args()
    
    if not args.uid:
        print("❌ Data Source UID Fix Needed!")
        print("=" * 50)
        print(get_grafana_datasource_info())
        
        # Suggest trying common UIDs
        print("\n💡 Quick fixes to try:")
        common_uids = ["health", "influxdb-health", "P951FEA4DE58B8DFC"]
        
        for uid in common_uids:
            print(f"   python3 fix_datasource_uid.py --uid {uid}")
        
        return 1
    
    try:
        output_file = update_dashboard_datasource(args.dashboard, args.old_uid, args.uid)
        
        print(f"\n✅ Dashboard fixed and saved as: {output_file}")
        print(f"\n📋 Next steps:")
        print(f"   1. Import the fixed dashboard:")
        print(f"      python3 update_grafana_dashboard.py \\")
        print(f"        --dashboard-file {output_file} \\")
        print(f"        --grafana-url 'http://your-grafana:3000' \\")
        print(f"        --api-key 'your-api-key'")
        print(f"")
        print(f"   2. Or manually import {output_file} via Grafana UI")
        print(f"")
        print(f"✅ The dashboard will now use your 'health' data source!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == '__main__':
    exit(main())