#!/usr/bin/env python3

"""
Automatic Story/Task Creation Script

This script automates the creation of Stories and Tasks from an approved Epic or PRD.
It parses the Epic/PRD content, identifies key requirements, and generates appropriate
linked Stories and Tasks based on templates.
"""

import os
import re
import json
import argparse
from datetime import datetime

# Configuration
TEMPLATES_DIR = os.path.expanduser("~/project/templates")
OUTPUT_DIR = os.path.expanduser("~/project/work_items")

# Ensure directories exist
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Templates
STORY_TEMPLATE = """# Story: {title}

## User Value
{user_value}

## Acceptance Criteria
{acceptance_criteria}

## Estimation
{estimation}

---
*Additional details to be added during implementation:*
- Implementation Notes
- Test Scenarios
- UI/UX Requirements
- API Changes
- Database Changes
- Dependencies
- Related Documentation

## Parent Epic
{epic_id}
"""

TASK_TEMPLATE = """# Task: {title}

## Description
{description}

## Acceptance Criteria
{acceptance_criteria}

## Estimation
{estimation}

---
*Additional details to be added during implementation:*
- Implementation Approach
- Test Requirements
- Dependencies
- Assignee
- Files Changed
- Related PRs

## Parent Story
{story_id}
"""

def parse_epic(epic_file):
    """Parse an Epic file to extract key information."""
    try:
        with open(epic_file, 'r') as f:
            content = f.read()
        
        # Extract Epic ID and title
        title_match = re.search(r'# Epic: (.*)', content)
        epic_id = os.path.basename(epic_file).replace('.md', '')
        epic_title = title_match.group(1).strip() if title_match else "Unknown Epic"
        
        # Extract scope items that will become Stories
        scope_match = re.search(r'## Scope Summary\s+(.*?)(?=\n##|\Z)', content, re.DOTALL)
        scope_text = scope_match.group(1).strip() if scope_match else ""
        
        # Extract potential story items from scope
        story_items = []
        if scope_text:
            # Look for bullet points or numbered items
            items = re.findall(r'[-*]\s+(.*?)(?=\n[-*]|\Z)', scope_text, re.DOTALL)
            if not items:  # Try numbered list
                items = re.findall(r'\d+\.\s+(.*?)(?=\n\d+\.|\Z)', scope_text, re.DOTALL)
            
            # If still no items, split by newlines
            if not items:
                items = [line.strip() for line in scope_text.split('\n') if line.strip()]
            
            story_items = [item.strip() for item in items if item.strip()]
        
        return {
            "epic_id": epic_id,
            "title": epic_title,
            "story_items": story_items
        }
    
    except Exception as e:
        print(f"Error parsing Epic file: {e}")
        return None

def generate_stories(epic_data):
    """Generate Stories from Epic data."""
    stories = []
    
    for i, item in enumerate(epic_data["story_items"]):
        # Generate a story ID
        story_id = f"{epic_data['epic_id']}-S{i+1}"
        
        # Create a story title from the item
        title = item if len(item) < 60 else item[:57] + "..."
        
        # Generate user value from the item
        user_value = f"As a user, I need {item.lower()} so that I can achieve the goals outlined in the Epic."
        
        # Generate placeholder acceptance criteria
        acceptance_criteria = "- The feature is implemented according to specifications\n- All tests pass\n- Documentation is updated"
        
        # Default estimation
        estimation = "TBD"
        
        # Create the story content
        story_content = STORY_TEMPLATE.format(
            title=title,
            user_value=user_value,
            acceptance_criteria=acceptance_criteria,
            estimation=estimation,
            epic_id=epic_data["epic_id"]
        )
        
        stories.append({
            "id": story_id,
            "title": title,
            "content": story_content
        })
    
    return stories

def generate_tasks(stories):
    """Generate Tasks from Stories."""
    tasks = []
    
    for story in stories:
        # Generate standard implementation task
        impl_task_id = f"{story['id']}-T1"
        impl_task_title = f"Implement {story['title']}"
        impl_task_desc = f"Implement the functionality described in the parent story."
        impl_task_content = TASK_TEMPLATE.format(
            title=impl_task_title,
            description=impl_task_desc,
            acceptance_criteria="- Code implements all required functionality\n- Code follows project standards\n- Code is properly documented",
            estimation="4-8 hours",
            story_id=story['id']
        )
        
        # Generate standard testing task
        test_task_id = f"{story['id']}-T2"
        test_task_title = f"Test {story['title']}"
        test_task_desc = f"Create and execute tests for the functionality described in the parent story."
        test_task_content = TASK_TEMPLATE.format(
            title=test_task_title,
            description=test_task_desc,
            acceptance_criteria="- Unit tests cover all code paths\n- Integration tests verify functionality\n- All tests pass",
            estimation="2-4 hours",
            story_id=story['id']
        )
        
        # Generate standard documentation task
        doc_task_id = f"{story['id']}-T3"
        doc_task_title = f"Document {story['title']}"
        doc_task_desc = f"Update documentation to reflect the changes made in the parent story."
        doc_task_content = TASK_TEMPLATE.format(
            title=doc_task_title,
            description=doc_task_desc,
            acceptance_criteria="- User documentation is updated\n- API documentation is updated if applicable\n- Internal documentation reflects changes",
            estimation="1-2 hours",
            story_id=story['id']
        )
        
        tasks.extend([
            {"id": impl_task_id, "title": impl_task_title, "content": impl_task_content},
            {"id": test_task_id, "title": test_task_title, "content": test_task_content},
            {"id": doc_task_id, "title": doc_task_title, "content": doc_task_content}
        ])
    
    return tasks

def save_work_items(stories, tasks):
    """Save generated work items to files."""
    # Create directories for stories and tasks
    stories_dir = os.path.join(OUTPUT_DIR, "stories")
    tasks_dir = os.path.join(OUTPUT_DIR, "tasks")
    os.makedirs(stories_dir, exist_ok=True)
    os.makedirs(tasks_dir, exist_ok=True)
    
    # Save stories
    for story in stories:
        file_path = os.path.join(stories_dir, f"{story['id']}.md")
        with open(file_path, 'w') as f:
            f.write(story['content'])
        print(f"Created Story: {story['id']} - {story['title']}")
    
    # Save tasks
    for task in tasks:
        file_path = os.path.join(tasks_dir, f"{task['id']}.md")
        with open(file_path, 'w') as f:
            f.write(task['content'])
        print(f"Created Task: {task['id']} - {task['title']}")
    
    # Create a summary file
    summary = {
        "generated_at": datetime.now().isoformat(),
        "stories": [{"id": s["id"], "title": s["title"]} for s in stories],
        "tasks": [{"id": t["id"], "title": t["title"]} for t in tasks]
    }
    
    summary_path = os.path.join(OUTPUT_DIR, "generation_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nGeneration summary saved to {summary_path}")
    print(f"Total: {len(stories)} Stories and {len(tasks)} Tasks generated")

def main():
    parser = argparse.ArgumentParser(description='Generate Stories and Tasks from an Epic')
    parser.add_argument('epic_file', help='Path to the Epic markdown file')
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.epic_file):
        print(f"Error: Epic file '{args.epic_file}' not found")
        return 1
    
    # Parse Epic
    print(f"Parsing Epic file: {args.epic_file}")
    epic_data = parse_epic(args.epic_file)
    if not epic_data:
        print("Failed to parse Epic file")
        return 1
    
    # Generate Stories
    print(f"Generating Stories from Epic: {epic_data['title']}")
    stories = generate_stories(epic_data)
    if not stories:
        print("No Stories could be generated from the Epic")
        return 1
    
    # Generate Tasks
    print(f"Generating Tasks from {len(stories)} Stories")
    tasks = generate_tasks(stories)
    
    # Save work items
    save_work_items(stories, tasks)
    
    return 0

if __name__ == "__main__":
    exit(main())
