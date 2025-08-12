#!/usr/bin/env python3
"""
Script to update Grafana dashboard with comprehensive Apple Health metrics.
This script helps migrate from the basic dashboard to the comprehensive version.
"""

import json
import requests
import argparse
import logging
from pathlib import Path
from typing import Dict, Any

def load_dashboard(file_path: str) -> Dict[str, Any]:
    """Load dashboard JSON from file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading dashboard from {file_path}: {e}")
        raise

def update_grafana_dashboard(grafana_url: str, api_key: str, dashboard_data: Dict[str, Any]) -> bool:
    """Update dashboard in Grafana using the API."""
    
    # Prepare the API payload
    payload = {
        "dashboard": dashboard_data,
        "overwrite": True,
        "message": "Updated with comprehensive Apple Health metrics"
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # Update/create dashboard
        response = requests.post(
            f"{grafana_url}/api/dashboards/db",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logging.info(f"Dashboard updated successfully. URL: {result.get('url', 'N/A')}")
            return True
        else:
            logging.error(f"Failed to update dashboard: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"Error updating dashboard: {e}")
        return False

def backup_existing_dashboard(grafana_url: str, api_key: str, dashboard_uid: str, backup_file: str) -> bool:
    """Backup existing dashboard before updating."""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get existing dashboard
        response = requests.get(
            f"{grafana_url}/api/dashboards/uid/{dashboard_uid}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            dashboard_data = response.json()
            
            # Save backup
            with open(backup_file, 'w') as f:
                json.dump(dashboard_data, f, indent=2)
            
            logging.info(f"Backup saved to {backup_file}")
            return True
        elif response.status_code == 404:
            logging.info("No existing dashboard found to backup")
            return True
        else:
            logging.warning(f"Could not backup dashboard: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"Error backing up dashboard: {e}")
        return False

def validate_dashboard_data(dashboard_data: Dict[str, Any]) -> bool:
    """Validate dashboard data structure."""
    
    required_fields = ['title', 'panels', 'uid']
    for field in required_fields:
        if field not in dashboard_data:
            logging.error(f"Missing required field: {field}")
            return False
    
    # Check if we have panels
    if not dashboard_data['panels']:
        logging.error("Dashboard has no panels")
        return False
    
    # Check measurement names in queries
    expected_measurements = [
        'heart_metrics', 'respiratory_metrics', 'body_composition', 
        'energy_metrics', 'movement_metrics', 'running_performance',
        'walking_analysis', 'fitness_metrics', 'sleep_metrics',
        'environmental_metrics', 'workout_sessions'
    ]
    
    dashboard_json = json.dumps(dashboard_data)
    found_measurements = [m for m in expected_measurements if m in dashboard_json]
    
    logging.info(f"Dashboard uses {len(found_measurements)} comprehensive measurement types:")
    for measurement in found_measurements:
        logging.info(f"  - {measurement}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Update Grafana dashboard with comprehensive Apple Health metrics')
    parser.add_argument('--grafana-url', required=True, 
                       help='Grafana URL (e.g., http://localhost:3000)')
    parser.add_argument('--api-key', required=True,
                       help='Grafana API key with editor permissions')
    parser.add_argument('--dashboard-file', default='grafana_dashboard_ultimate.json',
                       help='Path to ultimate dashboard JSON file')
    parser.add_argument('--backup', action='store_true',
                       help='Backup existing dashboard before updating')
    parser.add_argument('--dry-run', action='store_true',
                       help='Validate dashboard without updating Grafana')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load dashboard data
        logging.info(f"Loading dashboard from {args.dashboard_file}")
        dashboard_data = load_dashboard(args.dashboard_file)
        
        # Validate dashboard
        if not validate_dashboard_data(dashboard_data):
            logging.error("Dashboard validation failed")
            return 1
        
        if args.dry_run:
            logging.info("Dry run completed successfully - dashboard is valid")
            return 0
        
        # Backup existing dashboard if requested
        if args.backup:
            dashboard_uid = dashboard_data.get('uid', 'apple_health')
            backup_file = f"grafana_dashboard_backup_{dashboard_uid}.json"
            backup_existing_dashboard(args.grafana_url, args.api_key, dashboard_uid, backup_file)
        
        # Update dashboard
        logging.info("Updating Grafana dashboard...")
        success = update_grafana_dashboard(args.grafana_url, args.api_key, dashboard_data)
        
        if success:
            logging.info("Dashboard update completed successfully!")
            logging.info("\nNew dashboard features:")
            logging.info("  ✓ Comprehensive heart rate analysis (HR, HRV, recovery)")
            logging.info("  ✓ Respiratory health monitoring (O2 sat, breathing rate)")
            logging.info("  ✓ Body composition tracking (weight, height)")
            logging.info("  ✓ Detailed movement analytics (steps, distance, flights)")
            logging.info("  ✓ Sports performance metrics (running, walking, VO2 max)")
            logging.info("  ✓ Enhanced sleep analysis")
            logging.info("  ✓ Environmental health monitoring")
            logging.info("  ✓ Workout distribution and analysis")
            return 0
        else:
            logging.error("Dashboard update failed")
            return 1
            
    except Exception as e:
        logging.error(f"Script failed: {e}")
        return 1

if __name__ == '__main__':
    exit(main())