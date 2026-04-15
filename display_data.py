"""
Display Data Module
Shows version data and allows updating versions
"""
import csv_manager
from compare_versions import compare_versions
import csv
from datetime import datetime


def display_data_menu():
    """
    Main function for displaying data and updating versions.
    Presents a sub-menu and loops until user returns to main menu.
    """
    while True:
        print("\n" + "="*70)
        print("DISPLAY & UPDATE VERSIONS")
        print("="*70)
        print("\n1. Show all components")
        print("2. Enter desired versions and update")
        print("3. Back to main menu")
        
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == '1':
                show_all_components()
            elif choice == '2':
                enter_desired_versions()
            elif choice == '3':
                print("Returning to main menu...")
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 3.")
        
        except KeyboardInterrupt:
            print("\n\nOperation cancelled. Returning to main menu...")
            break
        except Exception as e:
            print(f"Error: {e}")


def show_all_components():
    """Display all components with their current versions"""
    print("\n" + "-"*70)
    print("ALL COMPONENTS")
    print("-"*70)
    
    details = csv_manager.load_installed_details()
    
    if not details:
        print("No data available.")
        return
    
    print(f"\n{'Component':<15} {'Version':<20} {'Status':<15} {'Last Update':<20}")
    print("-"*70)
    
    for component, info in details.items():
        version = info['version']
        status = info['status']
        date = info['date']
        
        # Format status
        if status == 'updated':
            status_display = '✓ UPDATED'
        elif status == 'initial':
            status_display = '● INITIAL'
        else:
            status_display = status.upper()
        
        print(f"{component:<15} {version:<20} {status_display:<15} {date:<20}")
    
    print("-"*70)
    print(f"Total components: {len(details)}")


def enter_desired_versions():
    """
    Enter desired versions and perform update.
    User can enter manually or load from CSV file.
    """
    print("\n" + "-"*70)
    print("ENTER DESIRED VERSIONS & UPDATE")
    print("-"*70)
    
    # Load current versions
    installed_versions = csv_manager.load_installed_versions()
    
    if not installed_versions:
        print("No components found. Please add components first.")
        return
    
    # Show current versions
    print("\nCurrent versions:")
    print(f"{'Component':<15} {'Version':<20}")
    print("-"*70)
    for component, version in installed_versions.items():
        print(f"{component:<15} {version:<20}")
    print("-"*70)
    
    # Ask how to enter desired versions
    print("\nHow would you like to specify desired versions?")
    print("1. Enter manually")
    print("2. Load from CSV file")
    
    choice = input("\nEnter your choice (1/2): ").strip()
    
    desired_versions = None
    
    if choice == '1':
        # Manual entry
        desired_versions = enter_manually(installed_versions)
    elif choice == '2':
        # From CSV
        desired_versions = load_from_csv()
    else:
        print("Invalid choice.")
        return
    
    if not desired_versions:
        print("No desired versions specified.")
        return
    
    # Compare versions
    actions = compare_versions(installed_versions, desired_versions)
    
    # Display comparison
    display_comparison(installed_versions, desired_versions, actions)
    
    # Confirm update
    proceed = input("\nProceed with updates? (yes/no): ").strip().lower()
    
    if proceed in ['yes', 'y']:
        perform_updates(installed_versions, desired_versions, actions)
        print("\n✓ Updates completed successfully!")
    else:
        print("Update cancelled.")


def enter_manually(installed_versions):
    """Get desired versions through manual input"""
    print("\n" + "-"*70)
    print("ENTER DESIRED VERSIONS MANUALLY")
    print("-"*70)
    print("\nEnter desired version for each component (or press Enter to keep current):")
    
    desired_versions = {}
    
    for component, current_version in installed_versions.items():
        while True:
            version = input(f"  {component} (current: {current_version}): ").strip()
            
            if not version:
                # Keep current version
                desired_versions[component] = current_version
                break
            
            # Validate version format
            if not all(c.isdigit() or c == '.' for c in version):
                print("    Error: Version must contain only digits and dots.")
                continue
            
            if version.startswith('.') or version.endswith('.') or '..' in version:
                print("    Error: Invalid version format.")
                continue
            
            desired_versions[component] = version
            break
    
    return desired_versions


def load_from_csv():
    """Load desired versions from CSV file"""
    print("\n" + "-"*70)
    print("LOAD FROM CSV FILE")
    print("-"*70)
    
    file_path = input("\nEnter CSV file path: ").strip().strip('"')
    
    if not file_path:
        print("No file path provided.")
        return None
    
    return read_versions_from_csv(file_path)


def read_versions_from_csv(file_path):
    """Read versions from CSV file - supports multiple formats"""
    try:
        desired_versions = {}
        
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            content = file.read().strip()
            lines = content.split('\n')
            
            if not lines:
                print("Error: File is empty.")
                return None
            
            first_line = lines[0].strip()
            
            # Check if it has headers (case-insensitive)
            if 'component' in first_line.lower():
                file.seek(0)
                reader = csv.DictReader(file)
                for row in reader:
                    # Try different capitalizations and clean whitespace
                    component = (row.get('Component', '') or 
                                row.get('component', '') or
                                row.get('COMPONENT', '')).strip()
                    
                    # Try different version column names (case-insensitive)
                    version = ''
                    for key in row.keys():
                        if 'version' in key.lower():
                            version = row[key].strip()
                            break
                    
                    # Clean component name (remove leading spaces, etc.)
                    component = component.strip().upper()
                    
                    if component and version:
                        desired_versions[component] = version
            else:
                # Simple format without headers
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Try different delimiters
                    if '\t' in line:
                        parts = line.split('\t')
                    elif ',' in line:
                        parts = line.split(',')
                    else:
                        parts = line.split()
                    
                    # Clean and filter empty parts
                    parts = [p.strip() for p in parts if p.strip()]
                    
                    if len(parts) >= 2:
                        # Ensure component is uppercase
                        component = parts[0].strip().upper()
                        version = parts[1].strip()
                        desired_versions[component] = version
        
        if not desired_versions:
            print("Error: No valid version data found in file.")
            print("Expected format:")
            print("  - CSV with headers: Component,Version")
            print("  - Simple format: Component<tab>Version or Component,Version")
            return None
        
        print("\nDesired versions loaded from file:")
        for component, version in desired_versions.items():
            print(f"  {component}: {version}")
        
        return desired_versions
        
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None


def display_comparison(installed, desired, actions):
    """Display comparison table"""
    print("\n" + "="*70)
    print("VERSION COMPARISON")
    print("="*70)
    print(f"{'Component':<15} {'Installed':<20} {'Desired':<20} {'Action':<15}")
    print("-"*70)
    
    for component in installed.keys():
        inst_ver = installed.get(component, 'N/A')
        des_ver = desired.get(component, 'N/A')
        action = actions.get(component, 'missing')
        
        if action == 'upgrade':
            action_display = '↑ UPGRADE'
        elif action == 'downgrade':
            action_display = '↓ DOWNGRADE'
        elif action == 'not required':
            action_display = '✓ UP TO DATE'
        else:
            action_display = action.upper()
        
        print(f"{component:<15} {inst_ver:<20} {des_ver:<20} {action_display:<15}")
    
    print("="*70)


def perform_updates(installed, desired, actions):
    """Execute the updates and display clear results"""
    previous_versions = installed.copy()
    
    print("\nExecuting updates...")
    print("-"*70)
    
    for key, action in actions.items():
        if action == 'upgrade':
            old_ver = installed[key]
            installed[key] = desired[key]
            csv_manager.append_update_history(key, old_ver, desired[key], 'upgrade')
        
        elif action == 'downgrade':
            old_ver = installed[key]
            installed[key] = desired[key]
            csv_manager.append_update_history(key, old_ver, desired[key], 'downgrade')
        
        elif action == 'not required':
            csv_manager.append_update_history(key, installed[key], installed[key], 'not required')
    
    csv_manager.save_versions(installed, is_initial=False, previous_versions=previous_versions)
    
    # Display clear update results table
    print("\n" + "="*80)
    print("UPDATE RESULTS")
    print("="*80)
    print(f"{'Component':<12} {'Before':<18} {'After':<18} {'Status':<15} {'Action':<15}")
    print("-"*80)
    
    for key, action in actions.items():
        before_ver = previous_versions.get(key, 'N/A')
        after_ver = installed.get(key, 'N/A')
        
        if action == 'upgrade':
            status = '✓ SUCCESS'
            action_display = 'UPGRADED'
        elif action == 'downgrade':
            status = '⚠ WARNING'
            action_display = 'DOWNGRADED'
        elif action == 'not required':
            status = '✓ UP TO DATE'
            action_display = 'NO CHANGE'
        else:
            status = action.upper()
            action_display = action.upper()
        
        print(f"{key:<12} {before_ver:<18} {after_ver:<18} {status:<15} {action_display:<15}")
    
    print("="*80)


# Allow running this module directly for testing
if __name__ == "__main__":
    print("Display Data Module - Test Mode")
    display_data_menu()

