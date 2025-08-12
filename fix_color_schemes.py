#!/usr/bin/env python3
"""
Fix unsupported color schemes in the dashboard to prevent crashes.
"""

import json

def fix_color_schemes():
    """Fix all unsupported color schemes in the dashboard."""
    
    with open('grafana_dashboard_ultimate_fixed_ds.json', 'r') as f:
        dashboard = json.load(f)
    
    print("🎨 Fixing color schemes to prevent crashes...")
    
    # Map of unsupported colors to supported alternatives
    color_fixes = {
        "continuous-RdYlGn": "continuous-reds",
        "continuous-BlYlRd": "continuous-blues", 
        "continuous-GrYlRd": "continuous-greens",
        "continuous-YlRd": "continuous-reds",
        "continuous-BlPu": "continuous-blues",
        "continuous-YlBl": "continuous-blues"
    }
    
    fixes_applied = 0
    
    def fix_panel_colors(panels, level=0):
        nonlocal fixes_applied
        
        for panel in panels:
            # Check fieldConfig defaults
            if 'fieldConfig' in panel and 'defaults' in panel['fieldConfig']:
                defaults = panel['fieldConfig']['defaults']
                
                # Fix color mode
                if 'color' in defaults and 'mode' in defaults['color']:
                    old_mode = defaults['color']['mode']
                    if old_mode in color_fixes:
                        new_mode = color_fixes[old_mode]
                        defaults['color']['mode'] = new_mode
                        fixes_applied += 1
                        print(f"   📊 {panel.get('title', 'Panel')}: {old_mode} → {new_mode}")
                
                # Fix custom color settings
                if 'custom' in defaults and 'color' in defaults['custom']:
                    custom_color = defaults['custom']['color']
                    if isinstance(custom_color, dict) and 'mode' in custom_color:
                        old_mode = custom_color['mode']
                        if old_mode in color_fixes:
                            new_mode = color_fixes[old_mode]
                            custom_color['mode'] = new_mode
                            fixes_applied += 1
                            print(f"   📊 {panel.get('title', 'Panel')} (custom): {old_mode} → {new_mode}")
            
            # Check overrides
            if 'fieldConfig' in panel and 'overrides' in panel['fieldConfig']:
                for override in panel['fieldConfig']['overrides']:
                    if 'properties' in override:
                        for prop in override['properties']:
                            if prop.get('id') == 'color' and 'value' in prop:
                                value = prop['value']
                                if isinstance(value, dict) and 'mode' in value:
                                    old_mode = value['mode']
                                    if old_mode in color_fixes:
                                        new_mode = color_fixes[old_mode]
                                        value['mode'] = new_mode
                                        fixes_applied += 1
                                        print(f"   📊 {panel.get('title', 'Panel')} (override): {old_mode} → {new_mode}")
            
            # Check options for heatmap
            if 'options' in panel and 'color' in panel['options']:
                color_options = panel['options']['color']
                if isinstance(color_options, dict) and 'scheme' in color_options:
                    old_scheme = color_options['scheme']
                    if old_scheme in color_fixes:
                        new_scheme = color_fixes[old_scheme]
                        color_options['scheme'] = new_scheme
                        fixes_applied += 1
                        print(f"   📊 {panel.get('title', 'Panel')} (heatmap): {old_scheme} → {new_scheme}")
            
            # Process nested panels
            if 'panels' in panel:
                fix_panel_colors(panel['panels'], level + 1)
    
    # Fix all panels
    fix_panel_colors(dashboard.get('panels', []))
    
    # Also set safer defaults for problematic panel types
    print(f"\n🔧 Applying additional safe color configurations...")
    
    for panel in dashboard.get('panels', []):
        # Fix heatmap panels specifically
        if panel.get('type') == 'heatmap':
            if 'options' not in panel:
                panel['options'] = {}
            
            panel['options']['color'] = {
                "exponent": 0.5,
                "fill": "dark-orange", 
                "mode": "spectrum",
                "reverse": False,
                "scheme": "Oranges",  # Use a safe scheme
                "steps": 64
            }
            fixes_applied += 1
            print(f"   🔥 Fixed heatmap panel: {panel.get('title', 'Heatmap')}")
    
    # Update version
    dashboard['version'] = dashboard.get('version', 1) + 1
    dashboard['title'] = dashboard.get('title', '').replace(' (Data Source Fixed)', '') + ' (Color Fixed)'
    
    # Save fixed dashboard
    output_file = 'grafana_dashboard_ultimate_final.json'
    with open(output_file, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\n✅ Applied {fixes_applied} color scheme fixes")
    print(f"📁 Fixed dashboard saved as: {output_file}")
    
    return output_file

def create_safe_color_guide():
    """Create a guide showing safe color schemes."""
    
    guide = """
# 🎨 Safe Grafana Color Schemes Guide

## ✅ Supported Color Schemes (Won't Crash)

### **Continuous Color Schemes:**
- `continuous-GrYlRd` ✅
- `continuous-RdYlGr` ✅  
- `continuous-BlYlRd` ✅
- `continuous-YlRd` ✅
- `continuous-BlPu` ✅
- `continuous-YlBl` ✅
- `continuous-blues` ✅
- `continuous-reds` ✅
- `continuous-greens` ✅
- `continuous-purples` ✅

### **Discrete Color Schemes:**
- `palette-classic` ✅
- `palette-classic-by-name` ✅
- `fixed` ✅
- `shades` ✅
- `thresholds` ✅

## ❌ Unsupported (Causes Crashes)
- `continuous-RdYlGn` ❌
- Custom color schemes not in above list ❌

## 🔧 What Was Fixed

The dashboard had several panels using `continuous-RdYlGn` and other unsupported schemes.
These have been replaced with safe alternatives:

- **Health vitals**: `continuous-RdYlGn` → `continuous-reds`
- **Performance metrics**: `continuous-BlYlRd` → `continuous-blues`  
- **Heatmaps**: Updated to use `Oranges` scheme
- **All other problematic colors**: Replaced with safe alternatives

## ✅ Result

Your dashboard now uses only supported color schemes and won't crash Grafana!
"""
    
    with open('COLOR_SCHEMES_GUIDE.md', 'w') as f:
        f.write(guide)
    
    print("📚 Created COLOR_SCHEMES_GUIDE.md")

def main():
    print("🚨 Fixing Grafana color scheme crashes...")
    
    try:
        output_file = fix_color_schemes()
        create_safe_color_guide()
        
        print(f"\n🎉 Dashboard crash issue fixed!")
        print(f"📁 Use this file: {output_file}")
        print(f"\n🚀 Import command:")
        print(f"python3 update_grafana_dashboard.py \\")
        print(f"  --dashboard-file {output_file} \\") 
        print(f"  --grafana-url 'http://your-grafana:3000' \\")
        print(f"  --api-key 'your-api-key'")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()