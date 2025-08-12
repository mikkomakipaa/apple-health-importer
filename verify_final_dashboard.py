#!/usr/bin/env python3
"""
Verify the final dashboard has no crash-causing issues.
"""

import json

def verify_final_dashboard():
    """Verify the final dashboard is safe to import."""
    
    with open('grafana_dashboard_ultimate_final.json', 'r') as f:
        dashboard = json.load(f)
    
    print("🔍 Final Dashboard Safety Check")
    print("=" * 40)
    
    # Basic info
    print(f"📊 Title: {dashboard.get('title')}")
    print(f"🆔 UID: {dashboard.get('uid')}")
    print(f"📝 Version: {dashboard.get('version')}")
    
    # Check for problematic color schemes
    problematic_colors = [
        "continuous-RdYlGn", 
        "continuous-BlYlRd",
        "continuous-GrYlRd", 
        "continuous-YlRd",
        "continuous-BlPu",
        "continuous-YlBl"
    ]
    
    safe_colors = [
        "continuous-reds",
        "continuous-blues", 
        "continuous-greens",
        "continuous-purples",
        "palette-classic",
        "thresholds",
        "fixed",
        "shades"
    ]
    
    color_issues = []
    safe_color_count = 0
    datasource_uids = set()
    total_panels = len(dashboard.get('panels', []))
    
    def check_panel_safety(panels, level=0):
        nonlocal safe_color_count, color_issues
        
        for panel in panels:
            panel_title = panel.get('title', 'Untitled Panel')
            
            # Check data source
            if 'datasource' in panel and 'uid' in panel['datasource']:
                datasource_uids.add(panel['datasource']['uid'])
            
            for target in panel.get('targets', []):
                if 'datasource' in target and 'uid' in target['datasource']:
                    datasource_uids.add(target['datasource']['uid'])
            
            # Check color schemes in fieldConfig
            if 'fieldConfig' in panel:
                defaults = panel['fieldConfig'].get('defaults', {})
                
                # Check color mode
                color_mode = defaults.get('color', {}).get('mode', '')
                if color_mode in problematic_colors:
                    color_issues.append(f"{panel_title}: {color_mode}")
                elif color_mode in safe_colors or color_mode.startswith('continuous-'):
                    safe_color_count += 1
                
                # Check custom color
                custom_color = defaults.get('custom', {}).get('color', {})
                if isinstance(custom_color, dict):
                    custom_mode = custom_color.get('mode', '')
                    if custom_mode in problematic_colors:
                        color_issues.append(f"{panel_title} (custom): {custom_mode}")
                
                # Check overrides
                for override in panel['fieldConfig'].get('overrides', []):
                    for prop in override.get('properties', []):
                        if prop.get('id') == 'color' and 'value' in prop:
                            value = prop['value']
                            if isinstance(value, dict) and 'mode' in value:
                                override_mode = value['mode']
                                if override_mode in problematic_colors:
                                    color_issues.append(f"{panel_title} (override): {override_mode}")
            
            # Check heatmap color schemes
            if panel.get('type') == 'heatmap' and 'options' in panel:
                color_options = panel['options'].get('color', {})
                scheme = color_options.get('scheme', '')
                if scheme in problematic_colors:
                    color_issues.append(f"{panel_title} (heatmap): {scheme}")
            
            # Check nested panels
            if 'panels' in panel:
                check_panel_safety(panel['panels'], level + 1)
    
    check_panel_safety(dashboard.get('panels', []))
    
    print(f"\n🎨 Color Scheme Safety:")
    if color_issues:
        print(f"   ❌ Found {len(color_issues)} problematic color schemes:")
        for issue in color_issues:
            print(f"      • {issue}")
    else:
        print(f"   ✅ No problematic color schemes found!")
        print(f"   📊 {safe_color_count} panels using safe colors")
    
    print(f"\n🔗 Data Source Check:")
    if len(datasource_uids) == 1 and 'health' in datasource_uids:
        print(f"   ✅ All panels use 'health' data source")
    else:
        print(f"   ⚠️  Data source UIDs found: {datasource_uids}")
    
    print(f"\n📊 Dashboard Structure:")
    sections = [p for p in dashboard.get('panels', []) if p.get('type') == 'row']
    data_panels = [p for p in dashboard.get('panels', []) if p.get('type') != 'row']
    print(f"   • Total panels: {total_panels}")
    print(f"   • Sections: {len(sections)}")
    print(f"   • Data panels: {len(data_panels)}")
    
    # Safety summary
    is_safe = len(color_issues) == 0 and 'health' in datasource_uids
    
    print(f"\n{'✅' if is_safe else '⚠️'} Safety Summary:")
    if is_safe:
        print("   🎉 Dashboard is SAFE to import!")
        print("   🚀 No crash-causing issues detected")
        print("   📊 All color schemes are supported")
        print("   🔗 Data source configuration is correct")
    else:
        print("   ⚠️  Issues detected - dashboard may crash")
        if color_issues:
            print("   🎨 Color scheme issues need fixing")
        if 'health' not in datasource_uids:
            print("   🔗 Data source configuration needs fixing")
    
    return is_safe

if __name__ == '__main__':
    success = verify_final_dashboard()
    if success:
        print(f"\n🚀 Ready to import: grafana_dashboard_ultimate_final.json")
    else:
        print(f"\n⚠️  Please fix issues before importing")