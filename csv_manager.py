import csv
import os
from datetime import datetime

DATA_DIR = '/mnt/efs/sw-update-data'
CSV_HEADERS = ['Component', 'CurrentVersion', 'LastUpdateDate', 'PreviousVersion', 'UpdateStatus']
HISTORY_HEADERS = ['Timestamp', 'Component', 'OldVersion', 'NewVersion', 'Action', 'Branch', 'CommitID']
DEVICES = ['lab1','lab2','lab3','lab4','lab5','lab6','lab7','lab8','lab9','lab10']
DEFAULT_VERSIONS = {'OS':'15.2','BE':'11.3.30','DB':'12.0','FW':'3.6.0'}

def _versions_file(device):
    return os.path.join(DATA_DIR, f'{device}_versions.csv')

def _history_file(device):
    return os.path.join(DATA_DIR, f'{device}_history.csv')

def _ensure_device(device):
    if not os.path.exists(_versions_file(device)):
        save_versions(device, DEFAULT_VERSIONS, is_initial=True)

def load_installed_versions(device='lab1'):
    _ensure_device(device)
    try:
        versions = {}
        with open(_versions_file(device), 'r', newline='') as f:
            for row in csv.DictReader(f):
                versions[row['Component']] = row['CurrentVersion']
        return versions or DEFAULT_VERSIONS.copy()
    except:
        return DEFAULT_VERSIONS.copy()

def load_installed_details(device='lab1'):
    _ensure_device(device)
    try:
        details = {}
        with open(_versions_file(device), 'r', newline='') as f:
            for row in csv.DictReader(f):
                details[row['Component']] = {
                    'version': row['CurrentVersion'],
                    'status': row.get('UpdateStatus','initial'),
                    'date': row.get('LastUpdateDate','N/A')
                }
        return details
    except:
        return {k: {'version': v, 'status': 'initial', 'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')} for k,v in DEFAULT_VERSIONS.items()}

def save_versions(device, versions_dict, is_initial=False, previous_versions=None):
    try:
        with open(_versions_file(device), 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for comp, ver in versions_dict.items():
                writer.writerow({'Component':comp,'CurrentVersion':ver,'LastUpdateDate':now,'PreviousVersion':(previous_versions or {}).get(comp,''),'UpdateStatus':'initial' if is_initial else 'updated'})
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def append_update_history(device, component, old_version, new_version, action, branch='manual', commit_id=''):
    try:
        hf = _history_file(device)
        file_exists = os.path.exists(hf)
        with open(hf, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=HISTORY_HEADERS)
            if not file_exists:
                writer.writeheader()
            writer.writerow({'Timestamp':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'Component':component,'OldVersion':old_version,'NewVersion':new_version,'Action':action,'Branch':branch,'CommitID':commit_id})
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def get_version_history(device='lab1'):
    hf = _history_file(device)
    if not os.path.exists(hf):
        return []
    try:
        with open(hf, 'r', newline='') as f:
            return list(csv.DictReader(f))
    except:
        return []
