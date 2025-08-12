#!/usr/bin/env python3
"""
Verify the customized dashboard content and data source references.
"""

import json

def verify_dashboard():
    """Verify the customized dashboard."""
    
    with open('grafana_dashboard_customized.json', 'r') as f:
        dashboard = json.load(f)
    
    print("🔍 Dashboard Verification")
    print("=" * 50)
    
    # Basic info
    print(f"📊 Title: {dashboard.get('title')}")
    print(f"🆔 UID: {dashboard.get('uid')}")
    print(f"📝 Version: {dashboard.get('version')}")
    print(f"🏷️  Tags: {', '.join(dashboard.get('tags', []))}")
    
    # Panel analysis
    panels = dashboard.get('panels', [])
    print(f"\n📱 Total Panels: {len(panels)}")
    
    # Categorize panels
    row_panels = [p for p in panels if p.get('type') == 'row']
    data_panels = [p for p in panels if p.get('type') != 'row']
    
    print(f"   • Row headers: {len(row_panels)}")
    print(f"   • Data panels: {len(data_panels)}")
    
    print(f"\n📋 Panel Categories:")
    for panel in panels:
        panel_title = panel.get('title', 'Untitled')
        panel_type = panel.get('type', 'unknown')
        
        if panel_type == 'row':
            print(f"   📁 {panel_title} (section)")
        else:
            print(f"   📊 {panel_title} ({panel_type})")
    
    # Data source verification
    print(f"\n🔗 Data Source Analysis:")
    
    data_sources = set()
    for panel in panels:
        # Panel-level datasource
        if 'datasource' in panel and 'uid' in panel['datasource']:
            data_sources.add(panel['datasource']['uid'])
        
        # Target-level datasources
        for target in panel.get('targets', []):
            if 'datasource' in target and 'uid' in target['datasource']:
                data_sources.add(target['datasource']['uid'])
    
    print(f"   • Unique data source UIDs found: {len(data_sources)}")
    for ds_uid in sorted(data_sources):
        print(f"     - {ds_uid}")
    
    # Check for body composition references
    print(f"\n🔍 Body Composition Check:")
    body_refs = []
    dashboard_json = json.dumps(dashboard).lower()
    
    body_keywords = ['body', 'weight', 'height', 'composition', 'mass']
    for keyword in body_keywords:
        if keyword in dashboard_json:
            body_refs.append(keyword)
    
    if body_refs:
        print(f"   ⚠️  Found potential body composition references: {', '.join(body_refs)}")
        print("      (These might be in queries or field names - check manually if needed)")
    else:
        print("   ✅ No body composition references found")
    
    # Query analysis
    print(f"\n🔍 Query Analysis:")
    query_measurements = set()
    
    for panel in panels:
        for target in panel.get('targets', []):
            query = target.get('query', '')
            if 'FROM' in query:
                # Extract measurement names from queries
                import re
                matches = re.findall(r'FROM\s+"([^"]+)"', query)
                query_measurements.update(matches)
    
    print(f"   • Measurements used in queries: {len(query_measurements)}")
    for measurement in sorted(query_measurements):
        print(f"     - {measurement}")
    
    print(f"\n✅ Verification complete!")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    print("   1. Ensure your InfluxDB data source in Grafana has UID: 'health_influxdb'")
    print("   2. Verify the data source points to your 'health' database")
    print("   3. Test a few panels after import to confirm data connectivity")
    
    if 'body_composition' in query_measurements:
        print("   4. ⚠️  body_composition measurement still referenced - you may want to remove those queries")

if __name__ == '__main__':
    verify_dashboard()