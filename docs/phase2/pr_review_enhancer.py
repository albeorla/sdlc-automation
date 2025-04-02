#!/usr/bin/env python3

"""
GitHub PR Review Mode Enhancement

This script automatically checks for common issues in pull requests before human review.
It integrates with Cursor rules to provide comprehensive automated checks and feedback.
"""

import os
import re
import sys
import json
import argparse
import subprocess
from collections import defaultdict

# Configuration
CURSOR_RULES_DIR = os.path.expanduser("~/.cursor/rules")
CODE_QUALITY_CHECKS = {
    "naming_conventions": {
        "description": "Check for adherence to naming conventions",
        "patterns": {
            "python": {
                "class": r"class\s+([A-Za-z0-9_]+)",
                "function": r"def\s+([a-z0-9_]+)",
                "constant": r"([A-Z0-9_]{2,})\s*=",
                "variable": r"([a-z0-9_]+)\s*="
            },
            "javascript": {
                "class": r"class\s+([A-Za-z0-9_]+)",
                "function": r"function\s+([a-z0-9_]+)|const\s+([a-z0-9_]+)\s*=\s*\(",
                "constant": r"const\s+([A-Z0-9_]{2,})\s*=",
                "variable": r"(let|var|const)\s+([a-z0-9_]+)\s*="
            }
        },
        "rules": {
            "class": {"pattern": r"^[A-Z][A-Za-z0-9]*$", "message": "Class names should use PascalCase"},
            "function": {"pattern": r"^[a-z][a-z0-9_]*$", "message": "Function names should use snake_case or camelCase"},
            "constant": {"pattern": r"^[A-Z][A-Z0-9_]*$", "message": "Constants should use UPPER_SNAKE_CASE"},
            "variable": {"pattern": r"^[a-z][a-z0-9_]*$", "message": "Variable names should use snake_case or camelCase"}
        }
    },
    "code_complexity": {
        "description": "Check for code complexity issues",
        "checks": {
            "function_length": {"max_lines": 50, "message": "Function is too long (> {max_lines} lines)"},
            "nested_depth": {"max_depth": 3, "message": "Nesting level is too deep (> {max_depth} levels)"},
            "parameter_count": {"max_params": 5, "message": "Too many parameters (> {max_params})"}
        }
    },
    "common_issues": {
        "description": "Check for common coding issues",
        "patterns": {
            "hardcoded_secrets": {
                "pattern": r"(password|secret|key|token|credential)s?\s*=\s*['\"][^'\"]+['\"]",
                "message": "Potential hardcoded secret detected",
                "severity": "high"
            },
            "debug_code": {
                "pattern": r"(console\.log|print|debugger|TODO|FIXME)",
                "message": "Debug code or marker detected",
                "severity": "medium"
            },
            "empty_catch": {
                "pattern": r"catch\s*\([^)]*\)\s*{\s*}",
                "message": "Empty catch block detected",
                "severity": "medium"
            }
        }
    }
}

def load_cursor_rules():
    """Load Cursor rules from the rules directory."""
    rules = {}
    
    if not os.path.exists(CURSOR_RULES_DIR):
        print(f"Cursor rules directory not found: {CURSOR_RULES_DIR}")
        return rules
    
    for filename in os.listdir(CURSOR_RULES_DIR):
        if filename.endswith('.mdc'):
            rule_path = os.path.join(CURSOR_RULES_DIR, filename)
            rule_name = os.path.splitext(filename)[0]
            
            try:
                with open(rule_path, 'r') as f:
                    content = f.read()
                
                # Extract rule description and patterns
                description_match = re.search(r'# (.+)', content)
                description = description_match.group(1) if description_match else "No description"
                
                # Extract file patterns
                file_patterns = []
                pattern_matches = re.findall(r'```cursor-filepath-patterns\s+(.*?)\s+```', content, re.DOTALL)
                if pattern_matches:
                    file_patterns = [p.strip() for p in pattern_matches[0].split('\n') if p.strip()]
                
                rules[rule_name] = {
                    "description": description,
                    "file_patterns": file_patterns,
                    "content": content
                }
            
            except Exception as e:
                print(f"Error loading rule {rule_name}: {e}")
    
    return rules

def get_changed_files(base_ref, head_ref):
    """Get list of files changed between two refs with their content."""
    try:
        # Get list of changed files
        result = subprocess.run(
            ['git', 'diff', '--name-only', base_ref, head_ref],
            capture_output=True,
            text=True,
            check=True
        )
        
        files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        
        # Get content of each file
        files_with_content = {}
        for file_path in files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    files_with_content[file_path] = content
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
        
        return files_with_content
    
    except subprocess.CalledProcessError as e:
        print(f"Error getting changed files: {e}")
        return {}

def match_file_to_rules(file_path, cursor_rules):
    """Match a file to applicable Cursor rules based on file patterns."""
    applicable_rules = []
    
    for rule_name, rule in cursor_rules.items():
        for pattern in rule["file_patterns"]:
            if re.search(pattern, file_path):
                applicable_rules.append(rule_name)
                break
    
    return applicable_rules

def check_naming_conventions(file_path, content):
    """Check naming conventions in the file content."""
    issues = []
    
    # Determine file type
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    file_type = None
    if ext == '.py':
        file_type = "python"
    elif ext in ['.js', '.ts']:
        file_type = "javascript"
    
    if not file_type:
        return issues
    
    # Get patterns for the file type
    patterns = CODE_QUALITY_CHECKS["naming_conventions"]["patterns"].get(file_type, {})
    rules = CODE_QUALITY_CHECKS["naming_conventions"]["rules"]
    
    # Check each naming convention
    for element_type, pattern in patterns.items():
        matches = re.findall(pattern, content)
        
        # Handle tuple matches (e.g., from regex groups)
        if matches and isinstance(matches[0], tuple):
            matches = [m for match in matches for m in match if m]
        
        for match in matches:
            rule = rules.get(element_type)
            if rule and not re.match(rule["pattern"], match):
                issues.append({
                    "file": file_path,
                    "line": find_line_number(content, match),
                    "issue_type": "naming_convention",
                    "element_type": element_type,
                    "name": match,
                    "message": rule["message"],
                    "severity": "medium"
                })
    
    return issues

def check_code_complexity(file_path, content):
    """Check code complexity issues in the file content."""
    issues = []
    
    # Check function length
    functions = extract_functions(file_path, content)
    for func in functions:
        # Check function length
        if len(func["lines"]) > CODE_QUALITY_CHECKS["code_complexity"]["checks"]["function_length"]["max_lines"]:
            issues.append({
                "file": file_path,
                "line": func["start_line"],
                "issue_type": "code_complexity",
                "complexity_type": "function_length",
                "function": func["name"],
                "message": CODE_QUALITY_CHECKS["code_complexity"]["checks"]["function_length"]["message"].format(
                    max_lines=CODE_QUALITY_CHECKS["code_complexity"]["checks"]["function_length"]["max_lines"]
                ),
                "severity": "medium"
            })
        
        # Check parameter count
        if len(func["parameters"]) > CODE_QUALITY_CHECKS["code_complexity"]["checks"]["parameter_count"]["max_params"]:
            issues.append({
                "file": file_path,
                "line": func["start_line"],
                "issue_type": "code_complexity",
                "complexity_type": "parameter_count",
                "function": func["name"],
                "message": CODE_QUALITY_CHECKS["code_complexity"]["checks"]["parameter_count"]["message"].format(
                    max_params=CODE_QUALITY_CHECKS["code_complexity"]["checks"]["parameter_count"]["max_params"]
                ),
                "severity": "medium"
            })
    
    return issues

def check_common_issues(file_path, content):
    """Check for common coding issues in the file content."""
    issues = []
    
    for issue_name, issue_config in CODE_QUALITY_CHECKS["common_issues"]["patterns"].items():
        matches = re.finditer(issue_config["pattern"], content)
        
        for match in matches:
            issues.append({
                "file": file_path,
                "line": find_line_number(content, match.group(0)),
                "issue_type": "common_issue",
                "issue_name": issue_name,
                "match": match.group(0),
                "message": issue_config["message"],
                "severity": issue_config["severity"]
            })
    
    return issues

def extract_functions(file_path, content):
    """Extract functions from file content with their details."""
    functions = []
    
    # Determine file type
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext == '.py':
        # Python function extraction
        function_pattern = r'def\s+([a-zA-Z0-9_]+)\s*\((.*?)\):'
        matches = re.finditer(function_pattern, content)
        
        for match in matches:
            func_name = match.group(1)
            params_str = match.group(2)
            params = [p.strip() for p in params_str.split(',') if p.strip()]
            
            # Find function body
            start_pos = match.end()
            start_line = content[:start_pos].count('\n') + 1
            
            # Extract function lines (simplified approach)
            lines = content[start_pos:].split('\n')
            func_lines = []
            
            # Find indentation level of first line
            for i, line in enumerate(lines):
                if line.strip():
                    base_indent = len(line) - len(line.lstrip())
                    func_lines.append(line)
                    break
            
            # Continue until we find a line with same or less indentation
            for line in lines[i+1:]:
                if line.strip() and (len(line) - len(line.lstrip())) <= base_indent:
                    break
                func_lines.append(line)
            
            functions.append({
                "name": func_name,
                "parameters": params,
                "start_line": start_line,
                "lines": func_lines
            })
    
    elif ext in ['.js', '.ts']:
        # JavaScript/TypeScript function extraction
        function_patterns = [
            r'function\s+([a-zA-Z0-9_]+)\s*\((.*?)\)',
            r'(const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*function\s*\((.*?)\)',
            r'(const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*\((.*?)\)\s*=>'
        ]
        
        for pattern in function_patterns:
            matches = re.finditer(pattern, content)
            
            for match in matches:
                if pattern == function_patterns[0]:
                    func_name = match.group(1)
                    params_str = match.group(2)
                else:
                    func_name = match.group(2)
                    params_str = match.group(3)
                
                params = [p.strip() for p in params_str.split(',') if p.strip()]
                
                # Find function body (simplified)
                start_pos = match.end()
                start_line = content[:start_pos].count('\n') + 1
                
                # Extract function lines (very simplified)
                lines = content[start_pos:].split('\n')
                func_lines = []
                
                # Find opening brace
                brace_count = 0
                started = False
                
                for line in lines:
                    if '{' in line and not started:
                        started = True
                        brace_count += line.count('{') - line.count('}')
                        func_lines.append(line)
                    elif started:
                        brace_count += line.count('{') - line.count('}')
                        func_lines.append(line)
                        if brace_count <= 0:
                            break
                
                functions.append({
                    "name": func_name,
                    "parameters": params,
                    "start_line": start_line,
                    "lines": func_lines
                })
    
    return functions

def find_line_number(content, substring):
    """Find the line number of a substring in the content."""
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if substring in line:
            return i + 1
    return 1  # Default to first line if not found

def generate_pr_review_report(issues, applicable_rules):
    """Generate a PR review report based on issues found."""
    if not issues and not applicable_rules:
        return "No issues found in the pull request."
    
    report = "# Automated PR Review Report\n\n"
    
    # Summarize issues by severity
    if issues:
        by_severity = defaultdict(list)
        for issue in issues:
            by_severity[issue["severity"]].append(issue)
        
        report += "## Issues Summary\n\n"
        
        for severity in ["critical", "high", "medium", "low"]:
            if severity in by_severity:
                count = len(by_severity[severity])
                report += f"- **{severity.upper()}**: {count} issue{'s' if count > 1 else ''}\n"
        
        report += "\n"
        
        # Detail issues by type
        report += "## Detailed Issues\n\n"
        
        by_type = defaultdict(list)
        for issue in issues:
            issue_type = issue["issue_type"]
            by_type[issue_type].append(issue)
        
        for issue_type, type_issues in by_type.items():
            report += f"### {issue_type.replace('_', ' ').title()}\n\n"
            
            for issue in type_issues:
                report += f"- **{issue['file']}** (line {issue['line']}): {issue['message']}\n"
                
                if "name" in issue:
                    report += f"  - Name: `{issue['name']}`\n"
                
                if "match" in issue:
                    report += f"  - Found: `{issue['match']}`\n"
                
                if "function" in issue:
                    report += f"  - Function: `{issue['function']}`\n"
                
                report += f"  - Severity: {issue['severity']}\n"
                report += "\n"
    
    # Add applicable rules
    if applicable_rules:
        report += "## Applicable Cursor Rules\n\n"
        
        for rule_name, rule_details in applicable_rules.items():
            report += f"### {rule_name}\n\n"
            report += f"{rule_details['description']}\n\n"
            
            # Extract key points from rule content
            content = rule_details["content"]
            points = re.findall(r'- (.+)', content)
            
            if points:
                report += "Key points:\n\n"
                for point in points[:5]:  # Limit to first 5 points
                    report += f"- {point}\n"
                
                if len(points) > 5:
                    report += f"- *(and {len(points) - 5} more...)*\n"
                
                report += "\n"
    
    # Add recommendations
    if issues:
        report += "## Recommendations\n\n"
        
        if any(i["severity"] in ["critical", "high"] for i in issues):
            report += "- **Address high severity issues before merging**\n"
        
        if any(i["issue_type"] == "naming_convention" for i in issues):
            report += "- **Review naming conventions** to ensure consistency\n"
        
        if any(i["issue_type"] == "code_complexity" for i in issues):
            report += "- **Consider refactoring complex functions** to improve maintainability\n"
        
        if any(i["issue_name"] == "debug_code" for i in issues if "issue_name" in i):
            report += "- **Remove debug code** before merging\n"
        
        if any(i["issue_name"] == "hardcoded_secrets" for i in issues if "issue_name" in i):
            report += "- **Remove hardcoded secrets** and use environment variables or secure storage\n"
    
    return report

def main():
    parser = argparse.ArgumentParser(description='Enhance GitHub PR review with automated checks')
    parser.add_argument('--base-ref', required=True, help='Base reference (e.g., main)')
    parser.add_argument('--head-ref', required=True, help='Head reference (e.g., feature-branch)')
    parser.add_argument('--output-file', help='Output file for the review report (defaults to stdout)')
    args = parser.parse_args()
    
    # Load Cursor rules
    print("Loading Cursor rules...")
    cursor_rules = load_cursor_rules()
    print(f"Loaded {len(cursor_rules)} Cursor rules")
    
    # Get changed files
    print(f"Getting files changed between {args.base_ref} and {args.head_ref}")
    files_with_content = get_changed_files(args.base_ref, args.head_ref)
    
    if not files_with_content:
        print("No changed files found")
        return 0
    
    print(f"Found {len(files_with_content)} changed files")
    
    # Analyze files
    all_issues = []
    applicable_rule_details = {}
    
    for file_path, content in files_with_content.items():
        print(f"Analyzing {file_path}...")
        
        # Match file to applicable rules
        applicable_rules = match_file_to_rules(file_path, cursor_rules)
        for rule_name in applicable_rules:
            applicable_rule_details[rule_name] = cursor_rules[rule_name]
        
        # Run code quality checks
        all_issues.extend(check_naming_conventions(file_path, content))
        all_issues.extend(check_code_complexity(file_path, content))
        all_issues.extend(check_common_issues(file_path, content))
    
    # Generate report
    report = generate_pr_review_report(all_issues, applicable_rule_details)
    
    # Output report
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(report)
        print(f"Report written to {args.output_file}")
    else:
        print("\n" + "=" * 80 + "\n")
        print(report)
        print("\n" + "=" * 80)
    
    # Return non-zero exit code if issues found
    return 1 if all_issues else 0

if __name__ == "__main__":
    exit(main())
