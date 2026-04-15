"""
CSV Manager Module for Version Tracking
Handles reading and writing version data to CSV file
"""

import csv
import os
from datetime import datetime


CSV_FILE = 'versions.csv'
CSV_HEADERS = ['Component', 'CurrentVersion', 'LastUpdateDate', 'PreviousVersion', 'UpdateStatus']

# Default versions to use if CSV doesn't exist
DEFAULT_VERSIONS = {
    'OS': '10.2',
    'BE': '10.0.19042',
    'DB': '12.1',
    'FW': '3.5.1'
}


def load_installed_versions():
    """
    Load installed versions from CSV file.
    Returns a dictionary of component: version pairs.
    If CSV doesn't exist, creates it with default versions.
    """
    if not os.path.exists(CSV_FILE):
        print(f"Warning: {CSV_FILE} not found. Creating with default versions.")
        save_versions(DEFAULT_VERSIONS, is_initial=True)
        return DEFAULT_VERSIONS.copy()
    
    try:
        versions = {}
        with open(CSV_FILE, 'r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                component = row['Component']
                current_version = row['CurrentVersion']
                versions[component] = current_version
        
        if not versions:
            print(f"Warning: {CSV_FILE} is empty. Using default versions.")
            return DEFAULT_VERSIONS.copy()
        
        return versions
    
    except Exception as e:
        print(f"Error reading {CSV_FILE}: {e}")
        print("Using default versions as fallback.")
        return DEFAULT_VERSIONS.copy()


def load_installed_details():
    """
    Load complete installed version details from CSV file.
    Returns a dictionary of component: {version, status, date} pairs.
    If CSV doesn't exist, creates it with default versions.
    """
    if not os.path.exists(CSV_FILE):
        print(f"Warning: {CSV_FILE} not found. Creating with default versions.")
        save_versions(DEFAULT_VERSIONS, is_initial=True)
        # Return default structure
        default_details = {}
        for comp, ver in DEFAULT_VERSIONS.items():
            default_details[comp] = {
                'version': ver,
                'status': 'initial',
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        return default_details
    
    try:
        details = {}
        with open(CSV_FILE, 'r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                component = row['Component']
                details[component] = {
                    'version': row['CurrentVersion'],
                    'status': row.get('UpdateStatus', 'unknown'),
                    'date': row.get('LastUpdateDate', 'N/A')
                }
        
        if not details:
            print(f"Warning: {CSV_FILE} is empty. Using default versions.")
            default_details = {}
            for comp, ver in DEFAULT_VERSIONS.items():
                default_details[comp] = {
                    'version': ver,
                    'status': 'initial',
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            return default_details
        
        return details
    
    except Exception as e:
        print(f"Error reading {CSV_FILE}: {e}")
        print("Using default versions as fallback.")
        default_details = {}
        for comp, ver in DEFAULT_VERSIONS.items():
            default_details[comp] = {
                'version': ver,
                'status': 'initial',
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        return default_details


def save_versions(versions_dict, is_initial=False, previous_versions=None):
    """
    Save updated versions to CSV file.
    
    Args:
        versions_dict: Dictionary of component: version pairs
        is_initial: Boolean indicating if this is initial setup
        previous_versions: Dictionary of previous versions (for update tracking)
    """
    try:
        # Determine if file exists to decide on mode
        file_exists = os.path.exists(CSV_FILE)
        
        with open(CSV_FILE, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
            writer.writeheader()
            
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for component, current_version in versions_dict.items():
                previous_version = ''
                update_status = 'initial' if is_initial else 'updated'
                
                if previous_versions and component in previous_versions:
                    previous_version = previous_versions[component]
                
                writer.writerow({
                    'Component': component,
                    'CurrentVersion': current_version,
                    'LastUpdateDate': current_date,
                    'PreviousVersion': previous_version,
                    'UpdateStatus': update_status
                })
        
        print(f"Versions saved to {CSV_FILE}")
        return True
    
    except Exception as e:
        print(f"Error saving to {CSV_FILE}: {e}")
        return False


def append_update_history(component, old_version, new_version, action):
    """
    Append an update record to the history CSV file.
    
    Args:
        component: Component name (OS, BE, DB, FW)
        old_version: Previous version
        new_version: New version
        action: Action taken (upgrade, downgrade, not required)
    """
    history_file = 'version_history.csv'
    history_headers = ['Timestamp', 'Component', 'OldVersion', 'NewVersion', 'Action']
    
    try:
        file_exists = os.path.exists(history_file)
        
        with open(history_file, 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=history_headers)
            
            if not file_exists:
                writer.writeheader()
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            writer.writerow({
                'Timestamp': timestamp,
                'Component': component,
                'OldVersion': old_version,
                'NewVersion': new_version,
                'Action': action
            })
        
        return True
    
    except Exception as e:
        print(f"Error appending to history: {e}")
        return False


def get_version_history():
    """
    Read and return all version history records.
    Returns a list of dictionaries.
    """
    history_file = 'version_history.csv'
    
    if not os.path.exists(history_file):
        return []
    
    try:
        history = []
        with open(history_file, 'r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                history.append(row)
        return history
    
    except Exception as e:
        print(f"Error reading history: {e}")
        return []
