#!/usr/bin/env python3

import json
import os
import sys
import argparse
import glob
import re
import logging
from datetime import datetime
from pathlib import Path
from termcolor import colored
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants
PROJECTS_FILE = os.path.join(os.environ['APPDATA'], 'Cursor', 'User', 'globalStorage', 
                            'alefragnani.project-manager', 'projects.json')
DEFAULT_TAG = "app"  # Kept as a constant for reference but will not be used by default
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MAX_FILES_TO_ANALYZE = 10
MAX_CONTENT_LENGTH = 10000  # Characters per file to analyze
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Setup logging
def setup_logging():
    """Configure logging to write to both console and a log file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"pyproject_log_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger('pyproject')
    logger.setLevel(logging.INFO)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, log_file

# Logger instance
logger = None
log_file_path = None

# -------------------- Project Information Module --------------------

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
        logger.info(colored(f"✓ Project information collected successfully", "green"))
        return project_info
    except Exception as e:
        logger.error(colored(f"Error collecting project information: {str(e)}", "red"))
        sys.exit(1)

# -------------------- File Analysis Module --------------------

def get_file_samples():
    """Collects file samples from the repository for AI analysis."""
    try:
        # Extensions to prioritize
        important_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.c', '.cpp', 
                               '.h', '.cs', '.php', '.rb', '.md', '.html', '.css', '.json', '.yml', '.yaml']
        
        # Directories to exclude
        exclude_dirs = ['node_modules', 'venv', '.git', '__pycache__', 'dist', 'build', 'target']
        exclude_pattern = re.compile(f'({"|".join(exclude_dirs)})')
        
        # Get all files recursively
        all_files = []
        for ext in important_extensions:
            pattern = f"**/*{ext}"
            files = [f for f in glob.glob(pattern, recursive=True) 
                     if not exclude_pattern.search(f)]
            all_files.extend(files)
        
        # Limit to the most important files
        selected_files = all_files[:MAX_FILES_TO_ANALYZE]
        
        if not selected_files:
            logger.warning(colored("No suitable files found for AI analysis", "yellow"))
            return None
            
        # Read content of selected files
        file_samples = {}
        total_chars = 0
        
        for file_path in selected_files:
            try:
                if os.path.getsize(file_path) > 1000000:  # Skip files > 1MB
                    continue
                    
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(MAX_CONTENT_LENGTH)
                    file_samples[file_path] = content
                    total_chars += len(content)
                    
                    # If we've collected enough content, stop
                    if total_chars >= MAX_CONTENT_LENGTH * 3:
                        break
            except Exception as e:
                logger.warning(colored(f"Warning: Could not read {file_path}: {str(e)}", "yellow"))
                
        logger.info(colored(f"✓ Analyzed {len(file_samples)} files for AI tagging", "green"))
        return file_samples
    except Exception as e:
        logger.warning(colored(f"Error collecting file samples: {str(e)}", "yellow"))
        return None

# -------------------- AI Integration Module --------------------

def generate_ai_tags(file_samples):
    """Uses OpenAI to generate tags based on file contents."""
    api_response = None
    
    if not OPENAI_API_KEY:
        logger.warning(colored("OpenAI API key not found. Set OPENAI_API_KEY in .env file to use AI tagging.", "yellow"))
        return None, None
        
    if not file_samples:
        return None, None
        
    try:
        # Prepare sample data for the API
        file_content_summary = "\n\n".join([f"Filename: {path}\n\n{content[:1000]}" 
                                          for path, content in file_samples.items()])
        
        # Prepare the API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        payload = {
            "model": "o3-mini",
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that analyzes code repositories and generates descriptive tags."
                },
                {
                    "role": "user",
                    "content": f"Analyze these files from a code repository and suggest 2-3 specific, descriptive tags that best categorize what this project is about. Respond with ONLY the tags, separated by commas, without explanation or other text. Examples of good tags: 'web-framework', 'machine-learning', 'utility-tool', 'game-development', 'data-processing'.\n\n{file_content_summary}"
                }
            ],
            "temperature": 1
        }
        
        logger.info(colored("Contacting OpenAI for AI-generated tags...", "cyan"))
        response = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            logger.warning(colored(f"OpenAI API Error: {response.status_code} - {response.text}", "yellow"))
            return None, None
            
        api_response = response.json()
        tags_text = api_response["choices"][0]["message"]["content"].strip()
        
        # Clean up the tags (remove quotes, split by comma, strip whitespace)
        ai_tags = [tag.strip().lower().replace(' ', '-') for tag in tags_text.split(',')]
        
        # Limit to 3 tags
        ai_tags = ai_tags[:3]
        
        logger.info(colored(f"✓ AI generated tags: {', '.join(ai_tags)}", "green"))
        return ai_tags, api_response
    except Exception as e:
        logger.warning(colored(f"Error generating AI tags: {str(e)}", "yellow"))
        return None, None

# -------------------- Project Manager Integration Module --------------------

def create_project_entry(project_info, custom_tag=None, skip_ai_tags=False):
    """Create project entry in JSON format."""
    api_response = None
    try:
        # Default tags - just parent folder name
        tags = [
            project_info["ParentRootFolderName"]
        ]
        
        # Add custom tag if provided
        if custom_tag:
            tags.append(custom_tag)
        
        # Add AI-generated tags by default unless disabled
        if not skip_ai_tags:
            file_samples = get_file_samples()
            ai_tags, api_response = generate_ai_tags(file_samples)
            if ai_tags:
                tags.extend(ai_tags)
            
        entry = {
            "name": project_info["rootFolderName"],
            "rootPath": project_info["rootFolderPath"],
            "paths": [],
            "tags": tags,
            "enabled": True
        }
        logger.info(colored("✓ Project entry created successfully", "green"))
        return entry, api_response
    except Exception as e:
        logger.error(colored(f"Error creating project entry: {str(e)}", "red"))
        sys.exit(1)

def update_projects_file(new_entry):
    """Update the projects.json file with the new entry."""
    try:
        # Check if file exists
        if not os.path.exists(PROJECTS_FILE):
            logger.error(colored(f"Error: Projects file not found at {PROJECTS_FILE}", "red"))
            sys.exit(1)

        # Read existing content
        with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            try:
                projects = json.loads(content)
            except json.JSONDecodeError:
                logger.error(colored("Error: Invalid JSON in projects file", "red"))
                sys.exit(1)

        # Add new entry
        if not isinstance(projects, list):
            logger.error(colored("Error: Projects file does not contain a valid array", "red"))
            sys.exit(1)

        projects.append(new_entry)

        # Write updated content
        with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(projects, f, indent=4)

        logger.info(colored("✓ Projects file updated successfully", "green"))
        
        # Validate the updated file
        with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
            json.load(f)
        logger.info(colored("✓ JSON validation successful", "green"))

    except Exception as e:
        logger.error(colored(f"Error updating projects file: {str(e)}", "red"))
        sys.exit(1)

# -------------------- Logging and Receipt Functions --------------------

def write_receipt(api_response, project_entry):
    """Write a detailed receipt to the log file."""
    if not logger:
        return
        
    logger.info("\n" + "="*50)
    logger.info("PROJECT MANAGER RECEIPT")
    logger.info("="*50)
    
    # Project information
    logger.info(f"Project Name: {project_entry['name']}")
    logger.info(f"Project Path: {project_entry['rootPath']}")
    logger.info(f"Tags: {', '.join(project_entry['tags'])}")
    logger.info(f"Added to Project Manager: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # API response information if available
    if api_response:
        logger.info("\nAI TAG GENERATION DETAILS")
        logger.info("-"*50)
        logger.info(f"Model: {api_response.get('model', 'N/A')}")
        logger.info(f"Generated Tags: {api_response['choices'][0]['message']['content']}")
        logger.info(f"Token Usage: {api_response.get('usage', {}).get('total_tokens', 'N/A')} total tokens")
    
    logger.info("\nLog file location: " + os.path.abspath(log_file_path))
    logger.info("="*50)

# -------------------- Main Application Logic --------------------

def main():
    """Main function to run the project updater."""
    global logger, log_file_path
    
    # Setup logging before any other operations
    logger, log_file_path = setup_logging()
    
    parser = argparse.ArgumentParser(description='Update Cursor Project Manager with current directory')
    parser.add_argument('--folder', action='store_true', help='Add "folder" suffix to the root folder name')
    parser.add_argument('--tag', type=str, help='Add a custom tag to the project')
    parser.add_argument('--skip-ai-tags', action='store_true', help='Skip AI tag generation (enabled by default)')
    args = parser.parse_args()

    logger.info(colored("\n=== Cursor Project Updater ===\n", "cyan"))
    
    try:
        project_info = get_project_info(args.folder)
        new_entry, api_response = create_project_entry(project_info, args.tag, args.skip_ai_tags)
        update_projects_file(new_entry)
        logger.info(colored("\n✓ Project successfully added to Cursor Project Manager!", "green"))
        
        # Write receipt at the end
        write_receipt(api_response, new_entry)
        
        # Print log file location
        print(colored(f"\nLog file created at: {os.path.abspath(log_file_path)}", "cyan"))
        
    except Exception as e:
        logger.error(colored(f"\nError: {str(e)}", "red"))
        sys.exit(1)

if __name__ == "__main__":
    main() 