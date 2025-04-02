#!/usr/bin/env python3

"""
GitHub Action for Commit Message Linking

This script validates commit messages to ensure they follow the Conventional Commits standard
and include references to Task/Story IDs. It can be used as a pre-commit hook or in CI/CD pipelines.
"""

import re
import sys
import subprocess
import argparse
from enum import Enum

class CommitType(Enum):
    FEAT = "feat"
    FIX = "fix"
    DOCS = "docs"
    STYLE = "style"
    REFACTOR = "refactor"
    PERF = "perf"
    TEST = "test"
    BUILD = "build"
    CI = "ci"
    CHORE = "chore"

# Configuration
VALID_TYPES = [t.value for t in CommitType]
WORK_ITEM_PATTERN = r'(#[A-Z]+-[A-Z0-9]+-[ST][0-9]+|#[A-Z]+-[0-9]+)'
CONVENTIONAL_COMMIT_PATTERN = r'^({})(\([a-z0-9-]+\))?: .+'.format('|'.join(VALID_TYPES))

def get_commit_message(commit_msg_file=None):
    """Get the commit message from file or from the last commit."""
    if commit_msg_file:
        with open(commit_msg_file, 'r') as f:
            return f.read().strip()
    else:
        try:
            result = subprocess.run(
                ['git', 'log', '-1', '--pretty=%B'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error getting last commit message: {e}")
            return None

def validate_commit_format(message):
    """Validate that the commit message follows the Conventional Commits format."""
    # Check if the message follows the conventional commit format
    if not re.match(CONVENTIONAL_COMMIT_PATTERN, message, re.MULTILINE):
        return False, "Commit message does not follow Conventional Commits format"
    return True, None

def validate_work_item_reference(message):
    """Validate that the commit message includes a reference to a work item."""
    # Check if the message contains a work item reference
    if not re.search(WORK_ITEM_PATTERN, message, re.MULTILINE):
        return False, "Commit message does not include a work item reference"
    return True, None

def validate_commit_message(message):
    """Validate the commit message against all rules."""
    # Validate format
    format_valid, format_error = validate_commit_format(message)
    if not format_valid:
        return False, format_error
    
    # Validate work item reference
    ref_valid, ref_error = validate_work_item_reference(message)
    if not ref_valid:
        return False, ref_error
    
    return True, None

def print_help_message():
    """Print a help message with examples of valid commit messages."""
    print("\nCommit message format:")
    print("  <type>(<scope>): <description>")
    print("\n  <body>")
    print("\n  <footer>")
    print("\nExamples:")
    print("  feat(auth): implement OAuth2 login flow")
    print("\n  Implements user authentication via OAuth2 providers.")
    print("\n  #PROJ-123")
    print("\n  ---")
    print("\n  fix(api): correct pagination in user listing endpoint #API-456")
    print("\nValid types:", ", ".join(VALID_TYPES))
    print("Work item reference format: #PROJECT-ID or #PROJECT-EPIC-STORY")

def main():
    parser = argparse.ArgumentParser(description='Validate commit messages')
    parser.add_argument('--commit-msg-file', help='Path to commit message file')
    parser.add_argument('--check-last-commit', action='store_true', help='Check the last commit message')
    args = parser.parse_args()
    
    # Get the commit message
    if args.commit_msg_file:
        message = get_commit_message(args.commit_msg_file)
    elif args.check_last_commit:
        message = get_commit_message()
    else:
        parser.print_help()
        return 1
    
    if not message:
        print("Error: Could not retrieve commit message")
        return 1
    
    # Validate the commit message
    valid, error = validate_commit_message(message)
    
    if not valid:
        print(f"Error: {error}")
        print_help_message()
        return 1
    
    print("Commit message validation passed!")
    return 0

if __name__ == "__main__":
    exit(main())
