#!/usr/bin/env python3

"""
PR Description Auto-Population Enhancement

This script enhances the MCP workflow for PR creation by automatically
populating PR descriptions based on linked work items. It extracts details
from linked Tasks/Stories and generates a formatted PR description.
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
STORIES_DIR = os.path.join(WORK_ITEMS_DIR, "stories")
TASKS_DIR = os.path.join(WORK_ITEMS_DIR, "tasks")
PR_TEMPLATE_FILE = os.path.expanduser("~/project/templates/pr_template.md")

# Default PR template if template file doesn't exist
DEFAULT_PR_TEMPLATE = """# Pull Request: {title}

## Description
{description}

## Related Work Items
{work_items}

## Changes
{changes}

## Testing
{testing}

## Documentation
{documentation}

## Checklist
- [ ] Code follows project standards
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CI/CD pipeline passes
"""

def get_current_branch():
    """Get the name of the current git branch."""
    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting current branch: {e}")
        return None

def extract_work_item_ids_from_branch(branch_name):
    """Extract work item IDs from branch name using common patterns."""
    # Look for patterns like feature/PROJ-123, bugfix/PROJ-456, etc.
    match = re.search(r'(?:feature|bugfix|fix|hotfix|release)/([A-Z]+-\d+)', branch_name)
    if match:
        return [match.group(1)]
    
    # Look for patterns like feature/PROJ-EPIC-S1, etc.
    match = re.search(r'(?:feature|bugfix|fix|hotfix|release)/([A-Z]+-[A-Z0-9]+-[ST]\d+)', branch_name)
    if match:
        return [match.group(1)]
    
    return []

def extract_work_item_ids_from_commits():
    """Extract work item IDs from recent commit messages."""
    try:
        result = subprocess.run(
            ['git', 'log', '--max-count=10', '--pretty=format:%s%n%b'],
            capture_output=True,
            text=True,
            check=True
        )
        
        content = result.stdout.strip()
        
        # Look for work item references like #PROJ-123 or #PROJ-EPIC-S1
        matches = re.findall(r'#([A-Z]+-\d+|[A-Z]+-[A-Z0-9]+-[ST]\d+)', content)
        
        return list(set(matches))  # Remove duplicates
    
    except subprocess.CalledProcessError as e:
        print(f"Error extracting work item IDs from commits: {e}")
        return []

def find_work_item_files(work_item_ids):
    """Find work item files based on IDs."""
    work_item_files = []
    
    for work_id in work_item_ids:
        # Determine if it's a Story or Task based on ID format
        if re.match(r'[A-Z]+-[A-Z0-9]+-S\d+', work_id):
            # It's a Story
            file_path = os.path.join(STORIES_DIR, f"{work_id}.md")
            if os.path.exists(file_path):
                work_item_files.append({"id": work_id, "type": "Story", "path": file_path})
        elif re.match(r'[A-Z]+-[A-Z0-9]+-T\d+', work_id):
            # It's a Task
            file_path = os.path.join(TASKS_DIR, f"{work_id}.md")
            if os.path.exists(file_path):
                work_item_files.append({"id": work_id, "type": "Task", "path": file_path})
        elif re.match(r'[A-Z]+-\d+', work_id):
            # It could be an Epic or other work item
            # Check in both directories
            story_path = os.path.join(STORIES_DIR, f"{work_id}.md")
            task_path = os.path.join(TASKS_DIR, f"{work_id}.md")
            
            if os.path.exists(story_path):
                work_item_files.append({"id": work_id, "type": "Story", "path": story_path})
            elif os.path.exists(task_path):
                work_item_files.append({"id": work_id, "type": "Task", "path": task_path})
    
    return work_item_files

def extract_work_item_details(work_item):
    """Extract relevant details from a work item file."""
    try:
        with open(work_item["path"], 'r') as f:
            content = f.read()
        
        details = {
            "id": work_item["id"],
            "type": work_item["type"],
            "title": "",
            "description": "",
            "acceptance_criteria": [],
            "user_value": ""
        }
        
        # Extract title
        title_match = re.search(r'# (?:Story|Task): (.*)', content)
        if title_match:
            details["title"] = title_match.group(1).strip()
        
        # Extract description (for Tasks)
        if work_item["type"] == "Task":
            desc_match = re.search(r'## Description\s+(.*?)(?=\n##|\Z)', content, re.DOTALL)
            if desc_match:
                details["description"] = desc_match.group(1).strip()
        
        # Extract user value (for Stories)
        if work_item["type"] == "Story":
            value_match = re.search(r'## User Value\s+(.*?)(?=\n##|\Z)', content, re.DOTALL)
            if value_match:
                details["user_value"] = value_match.group(1).strip()
        
        # Extract acceptance criteria
        ac_match = re.search(r'## Acceptance Criteria\s+(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if ac_match:
            criteria_text = ac_match.group(1).strip()
            # Split by bullet points
            criteria = re.findall(r'- (.*?)(?=\n-|\Z)', criteria_text, re.DOTALL)
            if criteria:
                details["acceptance_criteria"] = [c.strip() for c in criteria]
            else:
                details["acceptance_criteria"] = [criteria_text]
        
        return details
    
    except Exception as e:
        print(f"Error extracting details from {work_item['path']}: {e}")
        return None

def get_changed_files():
    """Get list of files changed in the current branch compared to main."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'origin/main...HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        
        return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    
    except subprocess.CalledProcessError as e:
        print(f"Error getting changed files: {e}")
        return []

def categorize_changes(files):
    """Categorize changed files by type."""
    categories = {
        "Code": [],
        "Tests": [],
        "Documentation": [],
        "Configuration": [],
        "Other": []
    }
    
    for file in files:
        if file.endswith(('.py', '.js', '.ts', '.java', '.c', '.cpp', '.go', '.rs')):
            if '/tests/' in file or file.startswith('tests/') or '_test.' in file or file.endswith('_test.py'):
                categories["Tests"].append(file)
            else:
                categories["Code"].append(file)
        elif file.endswith(('.md', '.txt', '.rst', '.adoc')):
            categories["Documentation"].append(file)
        elif file.endswith(('.json', '.yaml', '.yml', '.toml', '.ini', '.cfg')):
            categories["Configuration"].append(file)
        else:
            categories["Other"].append(file)
    
    return categories

def generate_pr_description(work_items, changed_files):
    """Generate a PR description based on work items and changed files."""
    # Load PR template
    template = DEFAULT_PR_TEMPLATE
    if os.path.exists(PR_TEMPLATE_FILE):
        with open(PR_TEMPLATE_FILE, 'r') as f:
            template = f.read()
    
    # Generate PR title
    if len(work_items) == 1:
        title = work_items[0]["title"]
    else:
        title = "Multiple changes"
    
    # Generate description
    description = ""
    for item in work_items:
        if item["type"] == "Story":
            description += f"Implements Story {item['id']}: {item['title']}\n\n"
            if item["user_value"]:
                description += f"{item['user_value']}\n\n"
        else:
            description += f"Addresses Task {item['id']}: {item['title']}\n\n"
            if item["description"]:
                description += f"{item['description']}\n\n"
    
    # Generate work items section
    work_items_section = ""
    for item in work_items:
        work_items_section += f"- {item['type']} [{item['id']}](link-to-work-item): {item['title']}\n"
    
    # Generate changes section
    categorized_changes = categorize_changes(changed_files)
    changes_section = ""
    
    for category, files in categorized_changes.items():
        if files:
            changes_section += f"### {category}\n"
            for file in files:
                changes_section += f"- {file}\n"
            changes_section += "\n"
    
    # Generate testing section
    testing_section = "Please describe the tests that you ran to verify your changes."
    if work_items:
        testing_section += "\n\nAcceptance Criteria:\n"
        for item in work_items:
            if item["acceptance_criteria"]:
                for criterion in item["acceptance_criteria"]:
                    testing_section += f"- [ ] {criterion}\n"
    
    # Generate documentation section
    documentation_section = "Please describe any documentation changes required."
    if categorized_changes["Documentation"]:
        documentation_section += "\n\nUpdated documentation:\n"
        for doc in categorized_changes["Documentation"]:
            documentation_section += f"- {doc}\n"
    
    # Fill in template
    pr_description = template.format(
        title=title,
        description=description,
        work_items=work_items_section,
        changes=changes_section,
        testing=testing_section,
        documentation=documentation_section
    )
    
    return pr_description

def main():
    parser = argparse.ArgumentParser(description='Generate PR description from work items')
    parser.add_argument('--output', help='Output file (defaults to stdout)')
    parser.add_argument('--work-item', action='append', help='Specific work item ID to include')
    args = parser.parse_args()
    
    # Get current branch
    branch = get_current_branch()
    if not branch:
        print("Error: Could not determine current branch")
        return 1
    
    print(f"Current branch: {branch}")
    
    # Get work item IDs
    work_item_ids = []
    
    # From command line arguments
    if args.work_item:
        work_item_ids.extend(args.work_item)
    
    # From branch name
    branch_ids = extract_work_item_ids_from_branch(branch)
    work_item_ids.extend(branch_ids)
    
    # From commit messages
    commit_ids = extract_work_item_ids_from_commits()
    work_item_ids.extend(commit_ids)
    
    # Remove duplicates
    work_item_ids = list(set(work_item_ids))
    
    if not work_item_ids:
        print("Warning: No work item IDs found in branch name or commit messages")
    else:
        print(f"Found work item IDs: {', '.join(work_item_ids)}")
    
    # Find work item files
    work_item_files = find_work_item_files(work_item_ids)
    
    if not work_item_files:
        print("Error: Could not find any work item files")
        return 1
    
    print(f"Found {len(work_item_files)} work item files")
    
    # Extract work item details
    work_items = []
    for item in work_item_files:
        details = extract_work_item_details(item)
        if details:
            work_items.append(details)
    
    if not work_items:
        print("Error: Could not extract details from work items")
        return 1
    
    # Get changed files
    changed_files = get_changed_files()
    
    if not changed_files:
        print("Warning: No changed files found")
    else:
        print(f"Found {len(changed_files)} changed files")
    
    # Generate PR description
    pr_description = generate_pr_description(work_items, changed_files)
    
    # Output PR description
    if args.output:
        with open(args.output, 'w') as f:
            f.write(pr_description)
        print(f"PR description written to {args.output}")
    else:
        print("\n" + "=" * 80 + "\n")
        print(pr_description)
        print("\n" + "=" * 80)
    
    return 0

if __name__ == "__main__":
    exit(main())
