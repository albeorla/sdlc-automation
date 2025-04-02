#!/usr/bin/env python3

"""
Release Notes Auto-Generator

This script generates release notes from Conventional Commits in a release branch or tag.
It categorizes changes by type and includes links to relevant PRs and issues.
"""

import re
import sys
import argparse
import subprocess
from datetime import datetime

# Configuration
COMMIT_TYPES = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "perf": "Performance Improvements",
    "refactor": "Code Refactoring",
    "docs": "Documentation",
    "test": "Tests",
    "build": "Build System",
    "ci": "Continuous Integration",
    "chore": "Chores",
    "style": "Style Improvements"
}

# Regex patterns
CONVENTIONAL_COMMIT_PATTERN = r'^(feat|fix|docs|style|refactor|perf|test|build|ci|chore)(\([a-z0-9-]+\))?: (.+)'
PR_PATTERN = r'#(\d+)'
ISSUE_PATTERN = r'(#[A-Z]+-[A-Z0-9]+-[ST][0-9]+|#[A-Z]+-[0-9]+)'

def get_commits(from_ref, to_ref):
    """Get commits between two refs in conventional commit format."""
    try:
        result = subprocess.run(
            ['git', 'log', '--pretty=format:%H|%s|%b', f'{from_ref}..{to_ref}'],
            capture_output=True,
            text=True,
            check=True
        )
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            
            parts = line.split('|', 2)
            if len(parts) >= 3:
                commit_hash, subject, body = parts
                commits.append({
                    'hash': commit_hash,
                    'subject': subject,
                    'body': body
                })
            elif len(parts) == 2:
                commit_hash, subject = parts
                commits.append({
                    'hash': commit_hash,
                    'subject': subject,
                    'body': ''
                })
        
        return commits
    
    except subprocess.CalledProcessError as e:
        print(f"Error getting commits: {e}")
        return []

def parse_conventional_commit(commit):
    """Parse a commit message according to Conventional Commits format."""
    match = re.match(CONVENTIONAL_COMMIT_PATTERN, commit['subject'])
    if not match:
        return None
    
    type_name, scope, description = match.groups()
    
    # Clean up scope (remove parentheses)
    if scope:
        scope = scope[1:-1]  # Remove ( and )
    
    # Extract PR numbers
    pr_numbers = []
    pr_matches = re.findall(PR_PATTERN, commit['body'])
    if pr_matches:
        pr_numbers = [int(pr) for pr in pr_matches]
    
    # Extract issue references
    issues = []
    issue_matches = re.findall(ISSUE_PATTERN, commit['body'])
    if issue_matches:
        issues = issue_matches
    
    return {
        'hash': commit['hash'],
        'type': type_name,
        'scope': scope,
        'description': description,
        'pr_numbers': pr_numbers,
        'issues': issues,
        'body': commit['body']
    }

def categorize_commits(commits):
    """Categorize commits by type and scope."""
    categorized = {}
    
    for commit in commits:
        parsed = parse_conventional_commit(commit)
        if not parsed:
            continue
        
        type_name = parsed['type']
        scope = parsed['scope'] or 'general'
        
        if type_name not in categorized:
            categorized[type_name] = {}
        
        if scope not in categorized[type_name]:
            categorized[type_name][scope] = []
        
        categorized[type_name][scope].append(parsed)
    
    return categorized

def generate_release_notes(categorized_commits, version, date=None):
    """Generate formatted release notes from categorized commits."""
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    notes = f"# Release {version} ({date})\n\n"
    
    # Add summary
    notes += "## Summary\n\n"
    
    for type_name, scopes in categorized_commits.items():
        if type_name not in COMMIT_TYPES:
            continue
        
        type_display = COMMIT_TYPES[type_name]
        count = sum(len(commits) for commits in scopes.values())
        
        if count > 0:
            notes += f"- **{type_display}**: {count}\n"
    
    notes += "\n"
    
    # Add details by type
    for type_name, scopes in sorted(categorized_commits.items()):
        if type_name not in COMMIT_TYPES:
            continue
        
        type_display = COMMIT_TYPES[type_name]
        
        notes += f"## {type_display}\n\n"
        
        for scope, commits in sorted(scopes.items()):
            if scope != 'general':
                notes += f"### {scope.capitalize()}\n\n"
            
            for commit in commits:
                # Format the commit entry
                entry = f"- {commit['description']}"
                
                # Add PR references
                if commit['pr_numbers']:
                    prs = ', '.join([f"[#{pr}](https://github.com/your-org/your-repo/pull/{pr})" for pr in commit['pr_numbers']])
                    entry += f" ({prs})"
                
                # Add issue references
                if commit['issues']:
                    issues = ', '.join([f"[{issue}](https://github.com/your-org/your-repo/issues/{issue.replace('#', '')})" for issue in commit['issues']])
                    entry += f" - {issues}"
                
                # Add commit hash
                short_hash = commit['hash'][:7]
                entry += f" ([{short_hash}](https://github.com/your-org/your-repo/commit/{commit['hash']}))"
                
                notes += f"{entry}\n"
            
            notes += "\n"
    
    # Add breaking changes section if any
    breaking_changes = []
    for type_name, scopes in categorized_commits.items():
        for scope, commits in scopes.items():
            for commit in commits:
                if "BREAKING CHANGE:" in commit['body']:
                    breaking_change = re.search(r'BREAKING CHANGE:(.*?)(?=\n\n|\Z)', commit['body'], re.DOTALL)
                    if breaking_change:
                        breaking_changes.append({
                            'description': breaking_change.group(1).strip(),
                            'commit': commit
                        })
    
    if breaking_changes:
        notes += "## BREAKING CHANGES\n\n"
        
        for change in breaking_changes:
            commit = change['commit']
            entry = f"- **{commit['type']}**"
            
            if commit['scope']:
                entry += f"({commit['scope']})"
            
            entry += f": {change['description']}"
            
            # Add commit hash
            short_hash = commit['hash'][:7]
            entry += f" ([{short_hash}](https://github.com/your-org/your-repo/commit/{commit['hash']}))"
            
            notes += f"{entry}\n"
        
        notes += "\n"
    
    return notes

def main():
    parser = argparse.ArgumentParser(description='Generate release notes from Conventional Commits')
    parser.add_argument('--from', dest='from_ref', required=True, help='Starting reference (e.g., v1.0.0)')
    parser.add_argument('--to', dest='to_ref', required=True, help='Ending reference (e.g., v1.1.0 or HEAD)')
    parser.add_argument('--version', required=True, help='Version number for the release notes')
    parser.add_argument('--date', help='Release date (defaults to today)')
    parser.add_argument('--output', help='Output file (defaults to stdout)')
    args = parser.parse_args()
    
    # Get commits
    print(f"Getting commits from {args.from_ref} to {args.to_ref}")
    commits = get_commits(args.from_ref, args.to_ref)
    
    if not commits:
        print("No commits found")
        return 1
    
    print(f"Found {len(commits)} commits")
    
    # Categorize commits
    categorized = categorize_commits(commits)
    
    # Generate release notes
    release_notes = generate_release_notes(categorized, args.version, args.date)
    
    # Output release notes
    if args.output:
        with open(args.output, 'w') as f:
            f.write(release_notes)
        print(f"Release notes written to {args.output}")
    else:
        print(release_notes)
    
    return 0

if __name__ == "__main__":
    exit(main())
