#!/usr/bin/env python3

"""
CI/CD Enhancement for Architectural Pattern Adherence

This script analyzes code to verify adherence to architectural patterns
using static analysis. It can be integrated into CI/CD pipelines to
automatically check for architectural violations.
"""

import os
import re
import sys
import json
import argparse
import subprocess
from collections import defaultdict

# Configuration
ARCHITECTURE_PATTERNS = {
    "layered": {
        "description": "Layered architecture with clear separation between UI, business logic, and data access",
        "layers": ["ui", "service", "repository"],
        "allowed_dependencies": {
            "ui": ["service"],
            "service": ["repository"],
            "repository": []
        }
    },
    "microservice": {
        "description": "Microservice architecture with independent services communicating via APIs",
        "components": ["api", "service", "model", "client"],
        "boundaries": ["service_boundary"]
    },
    "event_driven": {
        "description": "Event-driven architecture with publishers, subscribers, and event handlers",
        "components": ["publisher", "subscriber", "event", "handler"],
        "patterns": ["publish_subscribe", "event_sourcing"]
    }
}

# Module mapping to architectural components
MODULE_MAPPING = {
    "src/ui/": {"pattern": "layered", "component": "ui"},
    "src/service/": {"pattern": "layered", "component": "service"},
    "src/repository/": {"pattern": "layered", "component": "repository"},
    "src/api/": {"pattern": "microservice", "component": "api"},
    "src/events/": {"pattern": "event_driven", "component": "publisher"}
}

def analyze_imports(file_path):
    """Analyze import statements in a file to detect dependencies."""
    if not os.path.exists(file_path):
        return []
    
    # Determine file type
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    imports = []
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        if ext == '.py':
            # Python imports
            import_patterns = [
                r'import\s+([\w\.]+)',
                r'from\s+([\w\.]+)\s+import'
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                imports.extend(matches)
        
        elif ext in ['.js', '.ts']:
            # JavaScript/TypeScript imports
            import_patterns = [
                r'import.*from\s+[\'"](.+)[\'"]',
                r'require\([\'"](.+)[\'"]\)'
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                imports.extend(matches)
        
        elif ext in ['.java']:
            # Java imports
            import_pattern = r'import\s+([\w\.]+);'
            matches = re.findall(import_pattern, content)
            imports.extend(matches)
        
        return imports
    
    except Exception as e:
        print(f"Error analyzing imports in {file_path}: {e}")
        return []

def map_file_to_component(file_path):
    """Map a file to its architectural component based on its path."""
    for module_path, mapping in MODULE_MAPPING.items():
        if file_path.startswith(module_path):
            return mapping
    
    return None

def check_layered_architecture(files_and_imports):
    """Check adherence to layered architecture pattern."""
    violations = []
    
    for file_path, imports in files_and_imports.items():
        file_component = map_file_to_component(file_path)
        
        if not file_component or file_component["pattern"] != "layered":
            continue
        
        layer = file_component["component"]
        allowed = ARCHITECTURE_PATTERNS["layered"]["allowed_dependencies"].get(layer, [])
        
        for import_path in imports:
            import_component = None
            
            # Map import to component
            for module_path, mapping in MODULE_MAPPING.items():
                if module_path in import_path:
                    import_component = mapping
                    break
            
            if import_component and import_component["pattern"] == "layered":
                import_layer = import_component["component"]
                
                if import_layer not in allowed:
                    violations.append({
                        "file": file_path,
                        "violation_type": "layered_architecture",
                        "description": f"Layer '{layer}' should not depend on layer '{import_layer}'",
                        "import": import_path,
                        "severity": "high"
                    })
    
    return violations

def check_microservice_boundaries(files_and_imports):
    """Check adherence to microservice architecture boundaries."""
    # Group files by service
    services = defaultdict(list)
    
    for file_path in files_and_imports.keys():
        # Extract service name from path (e.g., src/services/user-service/...)
        match = re.search(r'src/services/([^/]+)', file_path)
        if match:
            service_name = match.group(1)
            services[service_name].append(file_path)
    
    violations = []
    
    # Check for cross-service dependencies
    for file_path, imports in files_and_imports.items():
        file_service = None
        match = re.search(r'src/services/([^/]+)', file_path)
        if match:
            file_service = match.group(1)
        
        if not file_service:
            continue
        
        for import_path in imports:
            for service_name, service_files in services.items():
                if service_name != file_service and any(service_path in import_path for service_path in service_files):
                    violations.append({
                        "file": file_path,
                        "violation_type": "microservice_boundary",
                        "description": f"Service '{file_service}' should not directly import from service '{service_name}'",
                        "import": import_path,
                        "severity": "critical"
                    })
    
    return violations

def check_event_driven_pattern(files_and_imports):
    """Check adherence to event-driven architecture pattern."""
    violations = []
    
    # Check for direct calls between publishers and subscribers
    for file_path, imports in files_and_imports.items():
        file_component = map_file_to_component(file_path)
        
        if not file_component or file_component["pattern"] != "event_driven":
            continue
        
        component = file_component["component"]
        
        if component == "publisher":
            # Publishers should not directly import subscribers
            for import_path in imports:
                if "subscriber" in import_path or "handler" in import_path:
                    violations.append({
                        "file": file_path,
                        "violation_type": "event_driven_pattern",
                        "description": "Publishers should not directly import subscribers or handlers",
                        "import": import_path,
                        "severity": "medium"
                    })
    
    return violations

def analyze_files(files):
    """Analyze a list of files for architectural pattern adherence."""
    files_and_imports = {}
    
    for file_path in files:
        imports = analyze_imports(file_path)
        files_and_imports[file_path] = imports
    
    # Run checks
    violations = []
    violations.extend(check_layered_architecture(files_and_imports))
    violations.extend(check_microservice_boundaries(files_and_imports))
    violations.extend(check_event_driven_pattern(files_and_imports))
    
    return violations

def get_changed_files(base_ref, head_ref):
    """Get list of files changed between two refs."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', base_ref, head_ref],
            capture_output=True,
            text=True,
            check=True
        )
        
        files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        
        # Filter to only include source code files
        code_extensions = ['.py', '.js', '.ts', '.java', '.c', '.cpp', '.go', '.rs']
        code_files = [f for f in files if any(f.endswith(ext) for ext in code_extensions)]
        
        return code_files
    
    except subprocess.CalledProcessError as e:
        print(f"Error getting changed files: {e}")
        return []

def generate_report(violations, output_format="text"):
    """Generate a report of architectural violations."""
    if output_format == "json":
        return json.dumps(violations, indent=2)
    
    # Text format
    if not violations:
        return "No architectural pattern violations found."
    
    report = "Architectural Pattern Violations\n"
    report += "===============================\n\n"
    
    # Group by severity
    by_severity = defaultdict(list)
    for v in violations:
        by_severity[v["severity"]].append(v)
    
    for severity in ["critical", "high", "medium", "low"]:
        if severity in by_severity:
            report += f"{severity.upper()} Severity Violations:\n"
            report += "-" * (len(severity) + 19) + "\n\n"
            
            for v in by_severity[severity]:
                report += f"File: {v['file']}\n"
                report += f"Violation: {v['description']}\n"
                report += f"Import: {v['import']}\n"
                report += "\n"
    
    return report

def main():
    parser = argparse.ArgumentParser(description='Check architectural pattern adherence')
    parser.add_argument('--base-ref', help='Base reference (e.g., main)')
    parser.add_argument('--head-ref', help='Head reference (e.g., feature-branch)')
    parser.add_argument('--files', nargs='+', help='Specific files to check')
    parser.add_argument('--output', choices=['text', 'json'], default='text', help='Output format')
    parser.add_argument('--output-file', help='Output file (defaults to stdout)')
    args = parser.parse_args()
    
    # Get files to analyze
    files = []
    
    if args.files:
        files = args.files
    elif args.base_ref and args.head_ref:
        print(f"Getting files changed between {args.base_ref} and {args.head_ref}")
        files = get_changed_files(args.base_ref, args.head_ref)
    else:
        parser.print_help()
        return 1
    
    if not files:
        print("No files to analyze")
        return 0
    
    print(f"Analyzing {len(files)} files for architectural pattern adherence")
    
    # Analyze files
    violations = analyze_files(files)
    
    # Generate report
    report = generate_report(violations, args.output)
    
    # Output report
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(report)
        print(f"Report written to {args.output_file}")
    else:
        print("\n" + report)
    
    # Return non-zero exit code if violations found
    return 1 if violations else 0

if __name__ == "__main__":
    exit(main())
