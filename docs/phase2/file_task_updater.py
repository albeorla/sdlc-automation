#!/usr/bin/env python3

"""
Automatic File Addition to Task Descriptions

This script monitors git operations to detect new file creation and updates
relevant Task descriptions with links to the newly created files.
"""

import os
import re
import sys
import json
import argparse
import subprocess
from datetime import datetime

# Configuration
WORK_ITEMS_DIR = os.path.expanduser("~/project/work_items")
TASKS_DIR = os.path.join(WORK_ITEMS_DIR, "tasks")
LOG_FILE = os.path.expanduser("~/project/file_addition_log.json")

def get_changed_files(since_commit=None):
    """Get list of files changed since the specified commit or in the working directory."""
    try:
        if since_commit:
            # Get files changed since the specified commit
            result = subprocess.run(
                ['git', 'diff', '--name-status', since_commit],
                capture_output=True,
                text=True,
                check=True
            )
        else:
            # Get files changed in the working directory
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                check=True
            )
        
        # Parse the output to get file paths and status
        files = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            
            if since_commit:
                # Format for git diff: A/M/D<tab>filepath
                status, filepath = line.split('\t', 1)
                files.append({'status': status, 'path': filepath})
            else:
                # Format for git status: XY filepath
                status = line[:2].strip()
                filepath = line[3:].strip()
                files.append({'status': status, 'path': filepath})
        
        return files
    
    except subprocess.CalledProcessError as e:
        print(f"Error getting changed files: {e}")
        return []

def categorize_file(filepath):
    """Categorize a file based on its path and extension."""
    # Extract file extension
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    
    # Categorize based on directory
    if '/tests/' in filepath or filepath.startswith('tests/'):
        return 'test'
    elif '/docs/' in filepath or filepath.startswith('docs/'):
        return 'documentation'
    elif '/examples/' in filepath or filepath.startswith('examples/'):
        return 'example'
    
    # Categorize based on extension
    if ext in ['.py', '.js', '.ts', '.java', '.c', '.cpp', '.go', '.rs']:
        return 'implementation'
    elif ext in ['.md', '.txt', '.rst', '.adoc']:
        return 'documentation'
    elif ext in ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg']:
        return 'configuration'
    elif ext in ['.html', '.css', '.scss', '.less']:
        return 'frontend'
    elif ext in ['.sql', '.db']:
        return 'database'
    
    # Default category
    return 'other'

def find_related_task(filepath, task_files):
    """Find the most relevant task for a given file."""
    # Extract components from filepath
    path_components = filepath.lower().split('/')
    filename = os.path.basename(filepath).lower()
    base_name, _ = os.path.splitext(filename)
    
    best_match = None
    best_score = 0
    
    for task_file in task_files:
        # Read task content
        with open(task_file, 'r') as f:
            content = f.read().lower()
        
        # Calculate relevance score
        score = 0
        
        # Check for exact filename match
        if filename in content:
            score += 10
        
        # Check for base name match
        if base_name in content:
            score += 5
        
        # Check for path component matches
        for component in path_components:
            if len(component) > 2 and component in content:  # Ignore very short components
                score += 2
        
        # Check for file category match
        category = categorize_file(filepath)
        if category in content:
            score += 3
        
        # Update best match if this task has a higher score
        if score > best_score:
            best_score = score
            best_match = task_file
    
    # Return the best match if it has a minimum score
    if best_score >= 5:
        return best_match
    
    return None

def update_task_description(task_file, filepath, category):
    """Update a task description with a reference to the new file."""
    try:
        with open(task_file, 'r') as f:
            content = f.read()
        
        # Check if the file is already mentioned
        if filepath in content:
            print(f"File {filepath} already mentioned in {task_file}")
            return False
        
        # Find the additional details section
        additional_section = "*Additional details to be added during implementation:*"
        if additional_section in content:
            # Add a Files Changed section if it doesn't exist
            if "## Files Changed" not in content:
                # Insert before the first item in additional details
                modified_content = content.replace(
                    additional_section,
                    f"{additional_section}\n\n## Files Changed\n- [{os.path.basename(filepath)}]({filepath}) - {category.capitalize()} file"
                )
            else:
                # Find the Files Changed section
                files_changed_match = re.search(r'## Files Changed\s+(.*?)(?=\n##|\Z)', content, re.DOTALL)
                if files_changed_match:
                    files_section = files_changed_match.group(0)
                    updated_files_section = f"{files_section}\n- [{os.path.basename(filepath)}]({filepath}) - {category.capitalize()} file"
                    modified_content = content.replace(files_section, updated_files_section)
                else:
                    # Fallback: add at the end
                    modified_content = f"{content}\n\n## Files Changed\n- [{os.path.basename(filepath)}]({filepath}) - {category.capitalize()} file"
        else:
            # Fallback: add at the end
            modified_content = f"{content}\n\n## Files Changed\n- [{os.path.basename(filepath)}]({filepath}) - {category.capitalize()} file"
        
        # Write the updated content
        with open(task_file, 'w') as f:
            f.write(modified_content)
        
        print(f"Updated {task_file} with reference to {filepath}")
        return True
    
    except Exception as e:
        print(f"Error updating task description: {e}")
        return False

def log_file_addition(task_file, filepath, category, success):
    """Log the file addition operation."""
    try:
        # Create or load the log file
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                log_data = json.load(f)
        else:
            log_data = {"file_additions": []}
        
        # Add the new entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_file": task_file,
            "filepath": filepath,
            "category": category,
            "success": success
        }
        
        log_data["file_additions"].append(log_entry)
        
        # Write the updated log
        with open(LOG_FILE, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    except Exception as e:
        print(f"Error logging file addition: {e}")

def process_changed_files(files):
    """Process a list of changed files and update related tasks."""
    # Ensure tasks directory exists
    if not os.path.exists(TASKS_DIR):
        print(f"Tasks directory {TASKS_DIR} does not exist")
        return
    
    # Get all task files
    task_files = [os.path.join(TASKS_DIR, f) for f in os.listdir(TASKS_DIR) if f.endswith('.md')]
    if not task_files:
        print("No task files found")
        return
    
    # Process each changed file
    for file_info in files:
        filepath = file_info['path']
        status = file_info['status']
        
        # Only process added or modified files
        if status in ['A', 'M', '??', 'AM', ' M', ' A']:
            # Categorize the file
            category = categorize_file(filepath)
            
            # Find related task
            related_task = find_related_task(filepath, task_files)
            
            if related_task:
                # Update the task description
                success = update_task_description(related_task, filepath, category)
                
                # Log the operation
                log_file_addition(related_task, filepath, category, success)
            else:
                print(f"No related task found for {filepath}")
                log_file_addition(None, filepath, category, False)

def main():
    parser = argparse.ArgumentParser(description='Update task descriptions with new files')
    parser.add_argument('--since-commit', help='Process files changed since the specified commit')
    parser.add_argument('--working-dir', action='store_true', help='Process files changed in the working directory')
    args = parser.parse_args()
    
    # Get changed files
    if args.since_commit:
        print(f"Getting files changed since commit {args.since_commit}")
        files = get_changed_files(args.since_commit)
    elif args.working_dir:
        print("Getting files changed in the working directory")
        files = get_changed_files()
    else:
        parser.print_help()
        return 1
    
    if not files:
        print("No changed files found")
        return 0
    
    print(f"Found {len(files)} changed files")
    
    # Process the changed files
    process_changed_files(files)
    
    return 0

if __name__ == "__main__":
    exit(main())
