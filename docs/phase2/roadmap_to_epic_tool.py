#!/usr/bin/env python3

"""
Roadmap to Epic Transition Tool

This script facilitates the transition from Roadmap items to Epics in the backlog.
It guides users through Epic creation from Roadmap items, ensuring strategic alignment
and proper documentation of business value.
"""

import os
import re
import sys
import json
import argparse
import subprocess
from datetime import datetime, timedelta

# Configuration
ROADMAP_DIR = os.path.expanduser("~/project/roadmap")
EPICS_DIR = os.path.expanduser("~/project/work_items/epics")
TEMPLATES_DIR = os.path.expanduser("~/project/templates")

# Ensure directories exist
os.makedirs(ROADMAP_DIR, exist_ok=True)
os.makedirs(EPICS_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Epic template
EPIC_TEMPLATE = """# Epic: {title}

## Business Value
{business_value}

## Strategic Alignment
{strategic_alignment}

## Success Metrics
{success_metrics}

## Scope Summary
{scope_summary}

---
*Additional details to be filled in after approval:*
- Out of Scope
- Dependencies
- Stakeholders
- Risks
- Estimated Timeline
- Related Documentation

## Roadmap Reference
{roadmap_reference}
"""

def list_roadmap_items():
    """List all roadmap items in the roadmap directory."""
    if not os.path.exists(ROADMAP_DIR):
        print(f"Roadmap directory {ROADMAP_DIR} does not exist")
        return []
    
    roadmap_files = [f for f in os.listdir(ROADMAP_DIR) if f.endswith('.md')]
    roadmap_items = []
    
    for filename in roadmap_files:
        file_path = os.path.join(ROADMAP_DIR, filename)
        item_id = os.path.splitext(filename)[0]
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Extract title
            title_match = re.search(r'# (.+)', content)
            title = title_match.group(1) if title_match else "Unknown"
            
            # Extract quarter/timeframe
            timeframe_match = re.search(r'## Timeframe\s+(.*?)(?=\n##|\Z)', content, re.DOTALL)
            timeframe = timeframe_match.group(1).strip() if timeframe_match else "Unknown"
            
            roadmap_items.append({
                "id": item_id,
                "title": title,
                "timeframe": timeframe,
                "file_path": file_path
            })
        
        except Exception as e:
            print(f"Error reading roadmap item {filename}: {e}")
    
    return roadmap_items

def parse_roadmap_item(file_path):
    """Parse a roadmap item file to extract key information."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract title
        title_match = re.search(r'# (.+)', content)
        title = title_match.group(1) if title_match else "Unknown"
        
        # Extract description
        description_match = re.search(r'## Description\s+(.*?)(?=\n##|\Z)', content, re.DOTALL)
        description = description_match.group(1).strip() if description_match else ""
        
        # Extract business value
        value_match = re.search(r'## Business Value\s+(.*?)(?=\n##|\Z)', content, re.DOTALL)
        business_value = value_match.group(1).strip() if value_match else ""
        
        # Extract strategic alignment
        alignment_match = re.search(r'## Strategic Alignment\s+(.*?)(?=\n##|\Z)', content, re.DOTALL)
        strategic_alignment = alignment_match.group(1).strip() if alignment_match else ""
        
        # Extract features/capabilities
        features_match = re.search(r'## Features/Capabilities\s+(.*?)(?=\n##|\Z)', content, re.DOTALL)
        features = features_match.group(1).strip() if features_match else ""
        
        # Extract timeframe
        timeframe_match = re.search(r'## Timeframe\s+(.*?)(?=\n##|\Z)', content, re.DOTALL)
        timeframe = timeframe_match.group(1).strip() if timeframe_match else ""
        
        return {
            "title": title,
            "description": description,
            "business_value": business_value,
            "strategic_alignment": strategic_alignment,
            "features": features,
            "timeframe": timeframe
        }
    
    except Exception as e:
        print(f"Error parsing roadmap item: {e}")
        return None

def generate_epic_id(roadmap_id):
    """Generate an Epic ID based on the roadmap item ID."""
    # Add a timestamp to ensure uniqueness
    timestamp = datetime.now().strftime("%m%d%H%M")
    return f"{roadmap_id}-E{timestamp}"

def estimate_timeline(timeframe):
    """Estimate a timeline based on the roadmap timeframe."""
    current_date = datetime.now()
    
    # Parse quarter information (e.g., "Q2 2023")
    quarter_match = re.search(r'Q([1-4])\s+(\d{4})', timeframe)
    if quarter_match:
        quarter = int(quarter_match.group(1))
        year = int(quarter_match.group(2))
        
        # Calculate start and end dates for the quarter
        start_month = (quarter - 1) * 3 + 1
        end_month = quarter * 3
        
        start_date = datetime(year, start_month, 1)
        if end_month == 12:
            end_date = datetime(year, end_month, 31)
        else:
            end_date = datetime(year, end_month + 1, 1) - timedelta(days=1)
        
        # Format dates
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        return f"{start_str} to {end_str}"
    
    # Check for "Next X months" pattern
    months_match = re.search(r'Next\s+(\d+)\s+months', timeframe, re.IGNORECASE)
    if months_match:
        months = int(months_match.group(1))
        end_date = current_date + timedelta(days=30 * months)
        
        start_str = current_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        return f"{start_str} to {end_str}"
    
    # Default to a generic 3-month timeline
    end_date = current_date + timedelta(days=90)
    start_str = current_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    return f"{start_str} to {end_str} (estimated)"

def extract_success_metrics(business_value, description):
    """Extract or generate success metrics based on business value and description."""
    # Look for metrics in the business value
    metrics_matches = re.findall(r'(increase|decrease|improve|reduce|enhance|optimize|achieve)\s+([^,.]+)', 
                               business_value + " " + description, re.IGNORECASE)
    
    metrics = []
    for action, target in metrics_matches:
        metrics.append(f"- {action.capitalize()} {target}")
    
    # If no metrics found, generate generic ones
    if not metrics:
        metrics = [
            "- Successful implementation of all planned features",
            "- User adoption rate meets or exceeds expectations",
            "- No critical bugs reported after release"
        ]
    
    return "\n".join(metrics)

def extract_scope_items(features):
    """Extract scope items from features/capabilities section."""
    # Look for bullet points
    items = re.findall(r'- (.+)', features)
    
    # If no bullet points, split by newlines
    if not items:
        items = [line.strip() for line in features.split('\n') if line.strip()]
    
    # Format as bullet points
    scope_items = []
    for item in items:
        scope_items.append(f"- {item}")
    
    return "\n".join(scope_items)

def create_epic_from_roadmap(roadmap_item):
    """Create an Epic from a roadmap item."""
    # Parse roadmap item
    item_data = parse_roadmap_item(roadmap_item["file_path"])
    if not item_data:
        print(f"Failed to parse roadmap item {roadmap_item['id']}")
        return None
    
    # Generate Epic ID
    epic_id = generate_epic_id(roadmap_item["id"])
    
    # Extract success metrics
    success_metrics = extract_success_metrics(item_data["business_value"], item_data["description"])
    
    # Extract scope items
    scope_summary = extract_scope_items(item_data["features"])
    
    # Create Epic content
    epic_content = EPIC_TEMPLATE.format(
        title=item_data["title"],
        business_value=item_data["business_value"],
        strategic_alignment=item_data["strategic_alignment"],
        success_metrics=success_metrics,
        scope_summary=scope_summary,
        roadmap_reference=f"Derived from Roadmap Item: {roadmap_item['id']}"
    )
    
    # Save Epic file
    epic_file_path = os.path.join(EPICS_DIR, f"{epic_id}.md")
    try:
        with open(epic_file_path, 'w') as f:
            f.write(epic_content)
        
        print(f"Created Epic {epic_id} from Roadmap Item {roadmap_item['id']}")
        return {
            "id": epic_id,
            "title": item_data["title"],
            "file_path": epic_file_path
        }
    
    except Exception as e:
        print(f"Error creating Epic file: {e}")
        return None

def interactive_mode():
    """Run the tool in interactive mode, guiding the user through the process."""
    print("Roadmap to Epic Transition Tool")
    print("===============================\n")
    
    # List roadmap items
    roadmap_items = list_roadmap_items()
    if not roadmap_items:
        print("No roadmap items found. Please create roadmap items first.")
        return 1
    
    print("Available Roadmap Items:")
    for i, item in enumerate(roadmap_items):
        print(f"{i+1}. [{item['id']}] {item['title']} ({item['timeframe']})")
    
    # Select roadmap item
    while True:
        try:
            selection = input("\nSelect a roadmap item (number): ")
            index = int(selection) - 1
            if 0 <= index < len(roadmap_items):
                selected_item = roadmap_items[index]
                break
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a number.")
    
    print(f"\nSelected: {selected_item['title']}")
    
    # Parse roadmap item
    item_data = parse_roadmap_item(selected_item["file_path"])
    if not item_data:
        print("Failed to parse roadmap item.")
        return 1
    
    # Display and confirm roadmap item details
    print("\nRoadmap Item Details:")
    print(f"Title: {item_data['title']}")
    print(f"Business Value: {item_data['business_value']}")
    print(f"Strategic Alignment: {item_data['strategic_alignment']}")
    print(f"Timeframe: {item_data['timeframe']}")
    
    confirm = input("\nCreate Epic from this roadmap item? (y/n): ")
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        return 0
    
    # Create Epic
    epic = create_epic_from_roadmap(selected_item)
    if not epic:
        print("Failed to create Epic.")
        return 1
    
    print(f"\nEpic created successfully: {epic['id']}")
    print(f"File: {epic['file_path']}")
    
    # Ask if user wants to view the created Epic
    view = input("\nView created Epic? (y/n): ")
    if view.lower() == 'y':
        try:
            with open(epic['file_path'], 'r') as f:
                print("\n" + "=" * 80 + "\n")
                print(f.read())
                print("\n" + "=" * 80)
        except Exception as e:
            print(f"Error reading Epic file: {e}")
    
    return 0

def batch_mode(roadmap_ids=None):
    """Run the tool in batch mode, processing multiple roadmap items."""
    print("Roadmap to Epic Transition Tool (Batch Mode)")
    print("===========================================\n")
    
    # List roadmap items
    roadmap_items = list_roadmap_items()
    if not roadmap_items:
        print("No roadmap items found. Please create roadmap items first.")
        return 1
    
    # Filter by IDs if specified
    if roadmap_ids:
        filtered_items = [item for item in roadmap_items if item['id'] in roadmap_ids]
        if not filtered_items:
            print(f"No roadmap items found with IDs: {', '.join(roadmap_ids)}")
            return 1
        roadmap_items = filtered_items
    
    print(f"Processing {len(roadmap_items)} roadmap items...")
    
    # Process each roadmap item
    created_epics = []
    for item in roadmap_items:
        print(f"\nProcessing: {item['title']} [{item['id']}]")
        epic = create_epic_from_roadmap(item)
        if epic:
            created_epics.append(epic)
    
    # Summarize results
    print("\nBatch Processing Complete")
    print(f"Created {len(created_epics)} Epics from {len(roadmap_items)} Roadmap Items")
    
    if created_epics:
        print("\nCreated Epics:")
        for epic in created_epics:
            print(f"- {epic['id']}: {epic['title']}")
    
    return 0

def main():
    parser = argparse.ArgumentParser(description='Transition Roadmap items to Epics')
    parser.add_argument('--batch', action='store_true', help='Run in batch mode')
    parser.add_argument('--roadmap-id', action='append', help='Specific roadmap item ID to process')
    args = parser.parse_args()
    
    # Create directories if they don't exist
    os.makedirs(ROADMAP_DIR, exist_ok=True)
    os.makedirs(EPICS_DIR, exist_ok=True)
    
    # Run in appropriate mode
    if args.batch:
        return batch_mode(args.roadmap_id)
    else:
        return interactive_mode()

if __name__ == "__main__":
    exit(main())
