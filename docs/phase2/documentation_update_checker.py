#!/usr/bin/env python3

"""
GitHub Action for Documentation Update Prompts

This script detects changes in specific modules and prompts for documentation updates
when code changes are made. It can be used in GitHub Actions workflows to automatically
comment on PRs that need documentation updates.
"""

import os
import re
import sys
import json
import argparse
import subprocess
from datetime import datetime

# Configuration
MODULE_DOC_MAPPING = {
    "src/api/": ["docs/api/", "docs/reference/api_docs.md"],
    "src/core/": ["docs/architecture/core.md"],
    "src/ui/": ["docs/ui/", "docs/reference/ui_components.md"],
    "src/database/": ["docs/database/", "docs/reference/database_schema.md"],
    "src/auth/": ["docs/security/authentication.md", "docs/api/auth.md"],
    "src/utils/": ["docs/development/utilities.md"]
}

def get_changed_files(base_ref, head_ref):
    """Get list of files changed between two refs."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', base_ref, head_ref],
            capture_output=True,
            text=True,
            check=True
        )
        
        return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    
    except subprocess.CalledProcessError as e:
        print(f"Error getting changed files: {e}")
        return []

def get_changed_modules(files):
    """Determine which modules have been changed based on file paths."""
    changed_modules = set()
    
    for file in files:
        for module in MODULE_DOC_MAPPING.keys():
            if file.startswith(module):
                changed_modules.add(module)
                break
    
    return list(changed_modules)

def get_affected_docs(modules):
    """Get documentation files affected by changes to the specified modules."""
    affected_docs = set()
    
    for module in modules:
        if module in MODULE_DOC_MAPPING:
            for doc in MODULE_DOC_MAPPING[module]:
                affected_docs.add(doc)
    
    return list(affected_docs)

def check_doc_updates(files, affected_docs):
    """Check if any of the affected documentation files have been updated."""
    updated_docs = set()
    
    for file in files:
        for doc in affected_docs:
            if file.startswith(doc) or (doc.endswith('/') and file.startswith(doc)):
                updated_docs.add(doc)
                break
    
    return list(updated_docs)

def generate_pr_comment(modules, affected_docs, updated_docs):
    """Generate a PR comment prompting for documentation updates."""
    if not affected_docs:
        return None
    
    if set(affected_docs) == set(updated_docs):
        return {
            "type": "success",
            "message": "✅ All affected documentation has been updated. Thank you for keeping the documentation current!"
        }
    
    missing_docs = [doc for doc in affected_docs if doc not in updated_docs]
    
    comment = "## Documentation Update Needed\n\n"
    comment += "Changes to the following modules typically require documentation updates:\n\n"
    
    for module in modules:
        comment += f"- `{module}`\n"
    
    comment += "\nPlease consider updating the following documentation:\n\n"
    
    for doc in missing_docs:
        comment += f"- `{doc}`\n"
    
    comment += "\nIf you believe no documentation update is needed, please explain why in a PR comment."
    
    return {
        "type": "warning",
        "message": comment
    }

def write_output_for_github_action(output):
    """Write output in a format that can be used by GitHub Actions."""
    if output:
        # Create output directory if it doesn't exist
        os.makedirs('github_action_output', exist_ok=True)
        
        # Write output to file
        with open('github_action_output/doc_update_comment.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        # Print output for GitHub Actions
        print(f"::set-output name=comment_type::{output['type']}")
        print(f"::set-output name=comment_message::{output['message']}")

def main():
    parser = argparse.ArgumentParser(description='Check for documentation updates needed')
    parser.add_argument('--base-ref', required=True, help='Base reference (e.g., main)')
    parser.add_argument('--head-ref', required=True, help='Head reference (e.g., feature-branch)')
    args = parser.parse_args()
    
    # Get changed files
    print(f"Getting files changed between {args.base_ref} and {args.head_ref}")
    files = get_changed_files(args.base_ref, args.head_ref)
    
    if not files:
        print("No changed files found")
        return 0
    
    print(f"Found {len(files)} changed files")
    
    # Get changed modules
    changed_modules = get_changed_modules(files)
    if not changed_modules:
        print("No modules with documentation requirements were changed")
        return 0
    
    print(f"Changed modules: {', '.join(changed_modules)}")
    
    # Get affected documentation
    affected_docs = get_affected_docs(changed_modules)
    if not affected_docs:
        print("No documentation updates required")
        return 0
    
    print(f"Affected documentation: {', '.join(affected_docs)}")
    
    # Check if documentation has been updated
    updated_docs = check_doc_updates(files, affected_docs)
    print(f"Updated documentation: {', '.join(updated_docs) if updated_docs else 'None'}")
    
    # Generate PR comment
    output = generate_pr_comment(changed_modules, affected_docs, updated_docs)
    
    # Write output for GitHub Actions
    if output:
        write_output_for_github_action(output)
        print(f"Documentation check result: {output['type']}")
        print(output['message'])
    
    return 0

if __name__ == "__main__":
    exit(main())
