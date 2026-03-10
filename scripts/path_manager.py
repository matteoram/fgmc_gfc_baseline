"""
This script handles path management for the project.

It defines project paths based on the user's home directory, 
allowing for different configurations for different users.
"""

from pathlib import Path
import os

def get_project_paths():
    """
    Returns a dictionary of project paths based on the user's home directory.
    """
    home_dir = Path.home()
    project_paths = {}

    # Check for the current user's home directory
    if home_dir == Path('/Users/matteoramina'):
        project_paths['base'] = Path('/Users/matteoramina/Documents/work/consulting/fcdo/fgmc_gfc_baseline/')
    else:
        # Default to the current working directory if user is not recognized
        project_paths['base'] = Path(os.getcwd())

    # Define other project paths relative to the base directory
    project_paths['scripts'] = project_paths['base'] / 'scripts'
    project_paths['sources'] = project_paths['base'] / 'sources'
    project_paths['analysis'] = project_paths['base'] / 'analysis'
    project_paths['admin'] = project_paths['base'] / 'admin'
    project_paths['meetings'] = project_paths['base'] / 'meetings'

    return project_paths

if __name__ == '__main__':
    # Example of how to use the function
    paths = get_project_paths()
    for name, path in paths.items():
        print(f'{name}: {path}')
