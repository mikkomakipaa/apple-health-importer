#!/usr/bin/env python3
"""
Fix field mapping issues in dashboard queries.
"""

import json
import re

def fix_field_mappings():
    """Fix field mapping issues in dashboard queries."""
    
    # Load the dashboard
    with open('grafana_dashboard_ultimate_final.json', 'r') as f:
        dashboard = json.load(f)
    
    print("🔧 Fixing dashboard field mappings...")
    
    fixes_applied = []
    
    # Define correct field mappings
    field_fixes = [
        # SpO2 queries
        {
            'pattern': r'SELECT\s+last\("value"\)\s+FROM\s+"respiratory_metrics"\s+WHERE\s+"type"\s+=\s+\'HKQuantityTypeIdentifierOxygenSaturation\'',
            'replacement': 'SELECT last("oxygen_saturation") FROM "respiratory_metrics" WHERE "type" = \'HKQuantityTypeIdentifierOxygenSaturation\'',
            'description': 'SpO2 query: value → oxygen_saturation field'
        },
        # VO2 Max queries  
        {
            'pattern': r'SELECT\s+last\("value"\)\s+FROM\s+"fitness_metrics"\s+WHERE\s+"type"\s+=\s+\'HKQuantityTypeIdentifierVO2Max\'',
            'replacement': 'SELECT last("vo2_max") FROM "fitness_metrics" WHERE "type" = \'HKQuantityTypeIdentifierVO2Max\'',
            'description': 'VO2 Max query: value → vo2_max field'
        },
        # Respiratory rate queries (if any)
        {
            'pattern': r'SELECT\s+last\("value"\)\s+FROM\s+"respiratory_metrics"\s+WHERE\s+"type"\s+=\s+\'HKQuantityTypeIdentifierRespiratoryRate\'',
            'replacement': 'SELECT last("respiratory_rate") FROM "respiratory_metrics" WHERE "type" = \'HKQuantityTypeIdentifierRespiratoryRate\'',
            'description': 'Respiratory Rate query: value → respiratory_rate field'
        }
    ]
    
    def fix_panel_queries(panels, level=0):
        nonlocal fixes_applied
        
        for panel in panels:
            panel_title = panel.get('title', 'Untitled Panel')
            
            # Fix queries in targets
            for target in panel.get('targets', []):
                if 'query' in target:
                    original_query = target['query']
                    fixed_query = original_query
                    
                    # Apply all field mapping fixes
                    for fix in field_fixes:
                        new_query = re.sub(fix['pattern'], fix['replacement'], fixed_query, flags=re.IGNORECASE)
                        if new_query != fixed_query:
                            fixes_applied.append(f"{panel_title}: {fix['description']}")
                            fixed_query = new_query
                    
                    # Additional time window fixes for these metrics
                    if 'oxygen_saturation' in fixed_query and 'time >= now() - 7d' in fixed_query:
                        fixed_query = fixed_query.replace('time >= now() - 7d', 'time >= now() - 30d')
                        fixes_applied.append(f"{panel_title}: SpO2 time window 7d → 30d")
                    
                    elif 'vo2_max' in fixed_query and 'time >= now() - 30d' in fixed_query:
                        fixed_query = fixed_query.replace('time >= now() - 30d', 'time >= now() - 90d')
                        fixes_applied.append(f"{panel_title}: VO2 Max time window 30d → 90d")
                    
                    # Update the query if it was changed
                    if fixed_query != original_query:
                        target['query'] = fixed_query
            
            # Check nested panels
            if 'panels' in panel:
                fix_panel_queries(panel['panels'], level + 1)
    
    # Apply fixes
    fix_panel_queries(dashboard.get('panels', []))
    
    # Save the fixed dashboard
    with open('grafana_dashboard_ultimate_final.json', 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\n✅ Applied {len(fixes_applied)} field mapping fixes:")
    for i, fix in enumerate(fixes_applied, 1):
        print(f"   {i}. {fix}")
    
    print(f"\n🚀 Updated: grafana_dashboard_ultimate_final.json")
    
    return len(fixes_applied)

if __name__ == '__main__':
    fixes = fix_field_mappings()
    if fixes > 0:
        print(f"\n🎉 Dashboard field mappings fixed! ({fixes} fixes applied)")
    else:
        print(f"\n✅ No field mapping issues found in dashboard")