# this is the baseline installed versions for the system
init_installed = {'OS': '10.2', 'BE': '10.0.19042', 'DB': '12.1', 'FW': '3.5.1'}


def compare_version_strings(version1, version2):
    """
    Compare two version strings digit by digit from left to right.
    Returns: 1 if version1 > version2, -1 if version1 < version2, 0 if equal
    """
    # Split versions by '.' and convert to integers
    parts1 = [int(x) for x in version1.split('.')]
    parts2 = [int(x) for x in version2.split('.')]
    
    # Compare each part from left to right
    max_length = max(len(parts1), len(parts2))
    
    for i in range(max_length):
        # Use 0 if part doesn't exist (e.g., comparing 1.0 with 1.0.1)
        part1 = parts1[i] if i < len(parts1) else 0
        part2 = parts2[i] if i < len(parts2) else 0
        
        if part1 > part2:
            return 1  # version1 is greater
        elif part1 < part2:
            return -1  # version1 is smaller
    
    return 0  # versions are equal


# compare_version function compares two version numbers and returns:
# loop for each key in the installed dictionary and compare with the desired versions
# upgrade if installed < desired 
# not required if installed == desired
# downgrade if installed > desired

def compare_versions(installed, desired):
    actions = {}
    
    for key in installed:
        if key in desired:
            installed_ver = installed[key]
            desired_ver = desired[key]
            
            comparison = compare_version_strings(installed_ver, desired_ver)
            
            if comparison < 0:
                actions[key] = 'upgrade'
            elif comparison == 0:
                actions[key] = 'not required'
            else:
                actions[key] = 'downgrade'
        else:
            actions[key] = 'missing'
    
    return actions



test_desired = {'OS': '10.3', 'BE': '10.0.19042', 'DB': '12.2', 'FW': '3.5.0'}
actions = compare_versions(init_installed, test_desired)
