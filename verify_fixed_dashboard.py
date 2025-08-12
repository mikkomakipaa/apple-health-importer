#!/usr/bin/env python3
"""
Verify the fixed dashboard uses the correct data source UID.
"""

import json

def verify_dashboard():
    """Verify the fixed dashboard."""
    
    with open('grafana_dashboard_ultimate_fixed_ds.json', 'r') as f:
        dashboard = json.load(f)
    
    print("🔍 Fixed Dashboard Verification")
    print("=" * 40)
    
    # Basic info
    print(f"📊 Title: {dashboard.get('title')}")
    print(f"🆔 UID: {dashboard.get('uid')}")
    print(f"📝 Version: {dashboard.get('version')}")
    
    # Check all data source UIDs
    datasource_uids = set()
    total_references = 0
    
    def check_panel_datasources(panels, level=0):
        nonlocal total_references
        indent = "  " * level
        
        for panel in panels:
            # Panel-level datasource
            if 'datasource' in panel and 'uid' in panel['datasource']:
                uid = panel['datasource']['uid']
                datasource_uids.add(uid)
                total_references += 1
            
            # Target-level datasources  
            for target in panel.get('targets', []):
                if 'datasource' in target and 'uid' in target['datasource']:
                    uid = target['datasource']['uid']
                    datasource_uids.add(uid)
                    total_references += 1
            
            # Nested panels (for collapsed sections)
            nested_panels = panel.get('panels', [])
            if nested_panels:
                check_panel_datasources(nested_panels, level + 1)
    
    check_panel_datasources(dashboard.get('panels', []))
    
    print(f"\n🔗 Data Source Analysis:")
    print(f"   • Total references: {total_references}")
    print(f"   • Unique UIDs found: {len(datasource_uids)}")
    
    for uid in sorted(datasource_uids):
        if uid == 'health':
            print(f"   ✅ {uid} (CORRECT - matches your Grafana data source)")
        else:
            print(f"   ⚠️  {uid} (check if this is correct)")
    
    # Section analysis
    sections = [p for p in dashboard.get('panels', []) if p.get('type') == 'row']
    data_panels = [p for p in dashboard.get('panels', []) if p.get('type') != 'row']
    
    print(f"\n📋 Dashboard Structure:")
    print(f"   • Sections: {len(sections)}")
    print(f"   • Data panels: {len(data_panels)}")
    print(f"   • Total panels: {len(dashboard.get('panels', []))}")
    
    print(f"\n✅ Verification Summary:")
    if datasource_uids == {'health'}:
        print("   🎉 Perfect! All data sources point to 'health'")
        print("   🚀 Dashboard is ready to import!")
    elif 'health' in datasource_uids and len(datasource_uids) == 1:
        print("   ✅ Good! All data sources use the same UID")
        print("   📝 Make sure this UID matches your Grafana data source")
    else:
        print("   ⚠️  Warning: Multiple data source UIDs found")
        print("   📝 Please verify these match your Grafana setup")
    
    return len(datasource_uids) == 1 and 'health' in datasource_uids

if __name__ == '__main__':
    success = verify_dashboard()
    print(f"\n{'✅ Verification passed!' if success else '⚠️ Please check data source UIDs'}")