#!/usr/bin/env python3
"""
Customize the Grafana dashboard:
1. Remove body composition panels
2. Update data source UID to match "health" database
"""

import json
import argparse

def remove_body_composition_panels(dashboard):
    """Remove body composition related panels."""
    print("🗑️  Removing body composition panels...")
    
    panels_to_remove = [
        "Body Composition",
        "Body Composition & Health Metrics"  # Row title
    ]
    
    original_count = len(dashboard.get('panels', []))
    
    # Filter out body composition panels
    dashboard['panels'] = [
        panel for panel in dashboard.get('panels', [])
        if panel.get('title') not in panels_to_remove
    ]
    
    removed_count = original_count - len(dashboard['panels'])
    print(f"   ✓ Removed {removed_count} body composition panels")
    
    # Adjust grid positions for remaining panels
    _adjust_grid_positions(dashboard)
    
    return removed_count > 0

def update_data_source_uid(dashboard, new_uid="health_influxdb"):
    """Update all data source UIDs to match the health database."""
    print(f"🔄 Updating data source UID to: {new_uid}")
    
    updated_count = 0
    
    # Update panels
    for panel in dashboard.get('panels', []):
        # Update panel-level datasource
        if 'datasource' in panel and 'uid' in panel['datasource']:
            panel['datasource']['uid'] = new_uid
            updated_count += 1
        
        # Update target-level datasources
        for target in panel.get('targets', []):
            if 'datasource' in target and 'uid' in target['datasource']:
                target['datasource']['uid'] = new_uid
                updated_count += 1
    
    print(f"   ✓ Updated {updated_count} data source references")
    return updated_count > 0

def _adjust_grid_positions(dashboard):
    """Adjust grid positions after removing panels."""
    print("📐 Adjusting panel positions...")
    
    # Sort panels by their current y position
    panels = dashboard.get('panels', [])
    panels.sort(key=lambda p: (p.get('gridPos', {}).get('y', 0), p.get('gridPos', {}).get('x', 0)))
    
    current_y = 0
    
    for panel in panels:
        grid_pos = panel.get('gridPos', {})
        
        # If this is a row panel (collapsed section)
        if panel.get('type') == 'row':
            grid_pos['y'] = current_y
            current_y += grid_pos.get('h', 1)
        else:
            # Regular panel
            panel_height = grid_pos.get('h', 8)
            grid_pos['y'] = current_y
            
            # Check if this completes a row (assuming 24 unit width)
            panel_x = grid_pos.get('x', 0)
            panel_width = grid_pos.get('w', 12)
            
            if panel_x + panel_width >= 24:  # End of row
                current_y += panel_height
    
    print("   ✓ Panel positions adjusted")

def update_dashboard_metadata(dashboard):
    """Update dashboard metadata."""
    dashboard['title'] = 'Apple Health Dashboard (Customized)'
    dashboard['uid'] = 'apple_health_customized'
    dashboard['version'] = dashboard.get('version', 1) + 1
    
    # Update tags
    if 'tags' not in dashboard:
        dashboard['tags'] = []
    
    dashboard['tags'] = [tag for tag in dashboard['tags'] if tag != 'body-composition']
    if 'customized' not in dashboard['tags']:
        dashboard['tags'].append('customized')
    
    print("📝 Updated dashboard metadata")

def create_summary(removed_panels, updated_datasources):
    """Create a summary of changes made."""
    summary = f"""
# Dashboard Customization Summary

## Changes Applied ✅

### 🗑️ Removed Panels
- Body Composition tracking panel
- Body Composition & Health Metrics row section
- Total panels removed: {removed_panels}

### 🔄 Data Source Updates  
- Updated all data source UIDs to use "health" database
- Total references updated: {updated_datasources}
- New data source UID: `health_influxdb`

## Remaining Panel Categories 📊

1. **Heart Health & Vital Signs**
   - Heart Rate Analysis
   - Heart Rate Summary  
   - HRV & Respiratory Health
   - Heart Rate Recovery

2. **Physical Activity & Movement**
   - Daily Energy Expenditure
   - Daily Movement Metrics

3. **Sports Performance & Fitness**
   - Performance Metrics (Speed, VO2 Max)
   - Workout Distribution

4. **Sleep & Recovery**
   - Sleep Timeline
   - Daily Sleep Duration

5. **Environmental & Context**
   - Environmental Health Monitoring

## Data Source Configuration 🔧

Make sure your Grafana InfluxDB data source:
- Name: "health" (or similar)
- UID: `health_influxdb` 
- Database: `health` (your database name)
- URL: Points to your InfluxDB instance

## Next Steps 🚀

1. Import the customized dashboard: `grafana_dashboard_customized.json`
2. Verify data source connection in Grafana
3. Check that all remaining panels display data correctly

The dashboard now focuses on core health metrics without body composition tracking.
"""
    
    with open('CUSTOMIZATION_SUMMARY.md', 'w') as f:
        f.write(summary)
    
    print("📚 Customization summary created: CUSTOMIZATION_SUMMARY.md")

def main():
    parser = argparse.ArgumentParser(description='Customize Grafana dashboard')
    parser.add_argument('--input', default='grafana_dashboard_final.json',
                       help='Input dashboard file')
    parser.add_argument('--output', default='grafana_dashboard_customized.json',
                       help='Output dashboard file')
    parser.add_argument('--datasource-uid', default='health_influxdb',
                       help='New data source UID for health database')
    
    args = parser.parse_args()
    
    print(f"📂 Loading dashboard from {args.input}")
    
    # Load dashboard
    try:
        with open(args.input, 'r') as f:
            dashboard = json.load(f)
    except Exception as e:
        print(f"❌ Error loading dashboard: {e}")
        return 1
    
    print("🔧 Applying customizations...")
    
    # Apply customizations
    removed_panels = 0
    if remove_body_composition_panels(dashboard):
        removed_panels = 1
    
    updated_datasources = 0  
    if update_data_source_uid(dashboard, args.datasource_uid):
        updated_datasources = 1
    
    update_dashboard_metadata(dashboard)
    
    # Save customized dashboard
    try:
        with open(args.output, 'w') as f:
            json.dump(dashboard, f, indent=2)
        print(f"✅ Customized dashboard saved to {args.output}")
    except Exception as e:
        print(f"❌ Error saving dashboard: {e}")
        return 1
    
    # Create summary
    create_summary(removed_panels, updated_datasources)
    
    print(f"\n🎉 Dashboard customization completed!")
    print(f"📁 Files created:")
    print(f"   • {args.output} (ready to import)")
    print(f"   • CUSTOMIZATION_SUMMARY.md (summary of changes)")
    
    print(f"\n✅ Key changes:")
    print(f"   • Removed body composition panels")  
    print(f"   • Updated data source UID to: {args.datasource_uid}")
    print(f"   • Adjusted panel positions automatically")
    print(f"   • Dashboard ready for 'health' database")
    
    return 0

if __name__ == '__main__':
    exit(main())