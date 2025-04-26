#!/usr/bin/env python3

import json
import os
import sys
import argparse
from pathlib import Path
from termcolor import colored

# Constants
PROJECTS_FILE = os.path.join(os.environ['APPDATA'], 'Cursor', 'User', 'globalStorage', 
                            'alefragnani.project-manager', 'projects.json')
DEFAULT_TAG = "app"

def get_project_info(is_folder=False):
    """Get project information from current working directory."""
    try:
        cwd = Path.cwd()
        cwd_name = cwd.name
        
        project_info = {
            "rootFolderName": f"{cwd_name}folder" if is_folder else cwd_name,
            "rootFolderPath": str(cwd),
            "ParentRootFolderName": cwd.parent.name,
            "cwdfolderName": cwd_name
        }
        print(colored(f"✓ Project information collected successfully", "green"))
        return project_info
    except Exception as e:
        print(colored(f"Error collecting project information: {str(e)}", "red"))
        sys.exit(1)

def create_project_entry(project_info, custom_tag=None):
    """Create project entry in JSON format."""
    try:
        # Default tags that are always present
        tags = [
            project_info["ParentRootFolderName"],
            DEFAULT_TAG
        ]
        
        # Add custom tag if provided, without modifying default structure
        if custom_tag:
            tags.append(custom_tag)
            
        entry = {
            "name": project_info["rootFolderName"],
            "rootPath": project_info["rootFolderPath"],
            "paths": [],
            "tags": tags,
            "enabled": True
        }
        print(colored("✓ Project entry created successfully", "green"))
        return entry
    except Exception as e:
        print(colored(f"Error creating project entry: {str(e)}", "red"))
        sys.exit(1)

def update_projects_file(new_entry):
    """Update the projects.json file with the new entry."""
    try:
        # Check if file exists
        if not os.path.exists(PROJECTS_FILE):
            print(colored(f"Error: Projects file not found at {PROJECTS_FILE}", "red"))
            sys.exit(1)

        # Read existing content
        with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            try:
                projects = json.loads(content)
            except json.JSONDecodeError:
                print(colored("Error: Invalid JSON in projects file", "red"))
                sys.exit(1)

        # Add new entry
        if not isinstance(projects, list):
            print(colored("Error: Projects file does not contain a valid array", "red"))
            sys.exit(1)

        projects.append(new_entry)

        # Write updated content
        with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(projects, f, indent=4)

        print(colored("✓ Projects file updated successfully", "green"))
        
        # Validate the updated file
        with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
            json.load(f)
        print(colored("✓ JSON validation successful", "green"))

    except Exception as e:
        print(colored(f"Error updating projects file: {str(e)}", "red"))
        sys.exit(1)

def main():
    """Main function to run the project updater."""
    parser = argparse.ArgumentParser(description='Update Cursor Project Manager with current directory')
    parser.add_argument('--folder', action='store_true', help='Add "folder" suffix to the root folder name')
    parser.add_argument('--tag', type=str, help='Add a custom tag to the project')
    args = parser.parse_args()

    print(colored("\n=== Cursor Project Updater ===\n", "cyan"))
    
    try:
        project_info = get_project_info(args.folder)
        new_entry = create_project_entry(project_info, args.tag)
        update_projects_file(new_entry)
        print(colored("\n✓ Project successfully added to Cursor Project Manager!", "green"))
    except Exception as e:
        print(colored(f"\nError: {str(e)}", "red"))
        sys.exit(1)

if __name__ == "__main__":
    main() 