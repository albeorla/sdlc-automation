# Implementation Guide for SDLC Streamlining Scripts

This guide provides detailed instructions for implementing the Python scripts developed as part of the SDLC and product planning streamlining project.

## Overview

The scripts in this project are designed to automate various aspects of the software development lifecycle and product planning process. They can be implemented in several ways depending on your team's workflow and preferences.

## Implementation Options

### 1. GitHub Actions Integration

Many of the scripts are designed to work well as GitHub Actions, which allows them to run automatically on specific events.

#### Example GitHub Action Workflow for Commit Message Validation

```yaml
# .github/workflows/validate-commits.yml
name: Validate Commit Messages

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
      
      - name: Validate commit messages
        run: |
          python scripts/phase2/commit_message_validator.py --check-last-commit
```

#### Example GitHub Action for Documentation Updates

```yaml
# .github/workflows/check-documentation.yml
name: Check Documentation Updates

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  check-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Check documentation updates
        run: |
          python scripts/phase2/documentation_update_checker.py --base-ref ${{ github.event.pull_request.base.ref }} --head-ref ${{ github.event.pull_request.head.ref }}
      
      - name: Comment on PR
        if: ${{ success() }}
        uses: actions/github-script@v6
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          script: |
            const fs = require('fs');
            const comment = fs.readFileSync('github_action_output/doc_update_comment.json', 'utf8');
            const commentData = JSON.parse(comment);
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: commentData.message
            });
```

### 2. Pre-commit Hooks

For scripts that validate code or commit messages, implementing them as pre-commit hooks ensures validation happens locally before commits are pushed.

#### Installation

1. Install the pre-commit framework:
   ```bash
   pip install pre-commit
   ```

2. Create a `.pre-commit-config.yaml` file in your repository:
   ```yaml
   repos:
   - repo: local
     hooks:
     - id: commit-message-validator
       name: Validate Commit Message
       entry: python scripts/phase2/commit_message_validator.py
       args: [--commit-msg-file]
       language: python
       stages: [commit-msg]
   ```

3. Install the hooks:
   ```bash
   pre-commit install --hook-type commit-msg
   ```

### 3. CLI Tools

All scripts are designed to work as command-line tools with proper argument parsing, making them easy to use manually or integrate into existing build scripts.

#### Example Usage

```bash
# Generate work items from an Epic
python scripts/phase2/auto_work_item_creation.py /path/to/epic.md

# Validate commit messages
python scripts/phase2/commit_message_validator.py --check-last-commit

# Generate release notes
python scripts/phase2/release_notes_generator.py --from v1.0.0 --to v1.1.0 --version 1.1.0 --output release_notes.md

# Check architectural patterns
python scripts/phase2/architecture_pattern_checker.py --base-ref main --head-ref feature-branch

# Generate PR description
python scripts/phase2/pr_description_generator.py --output pr_description.md

# Convert roadmap item to Epic
python scripts/phase2/roadmap_to_epic_tool.py
```

### 4. MCP Workflow Integration

The scripts can be called from MCP workflows (.mcp-workflows/*.yml files) to enhance existing processes.

#### Example MCP Workflow Integration

```yaml
# .mcp-workflows/github_pr_creation_mode.yml
name: GitHub PR Creation Mode
description: Create a pull request with auto-populated description
steps:
  - name: Generate PR description
    command: python scripts/phase2/pr_description_generator.py --output pr_description.md
  
  - name: Create draft PR
    command: gh pr create --draft --title "$(head -n 1 pr_description.md | sed 's/# //')" --body-file pr_description.md
```

### 5. Installation as a Package

For easier management and distribution, the scripts can be installed as a Python package.

#### Setup Script (setup.py)

```python
from setuptools import setup, find_packages

setup(
    name="sdlc-streamlining",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'create-work-items=phase2.auto_work_item_creation:main',
            'validate-commit=phase2.commit_message_validator:main',
            'update-task-files=phase2.file_task_updater:main',
            'check-docs=phase2.documentation_update_checker:main',
            'generate-release-notes=phase2.release_notes_generator:main',
            'generate-pr-description=phase2.pr_description_generator:main',
            'check-architecture=phase2.architecture_pattern_checker:main',
            'enhance-pr-review=phase2.pr_review_enhancer:main',
            'roadmap-to-epic=phase2.roadmap_to_epic_tool:main',
        ],
    },
    install_requires=[
        # List dependencies here
    ],
)
```

#### Installation

```bash
pip install -e .
```

## Recommended Implementation Approach

Based on the nature of your development workflow, we recommend the following implementation approach:

1. **Core Scripts as GitHub Actions**:
   - Commit message validation
   - Documentation update checking
   - Architecture pattern checking
   - PR review enhancement

2. **Developer Tools as CLI**:
   - Work item creation
   - PR description generation
   - Release notes generation
   - Roadmap to Epic conversion

3. **Local Validation as Pre-commit Hooks**:
   - Commit message validation

## Directory Structure

We recommend organizing the scripts in the following directory structure:

```
repository/
├── .github/
│   └── workflows/
│       ├── validate-commits.yml
│       ├── check-documentation.yml
│       ├── check-architecture.yml
│       └── enhance-pr-review.yml
├── scripts/
│   └── phase2/
│       ├── auto_work_item_creation.py
│       ├── commit_message_validator.py
│       ├── file_task_updater.py
│       ├── documentation_update_checker.py
│       ├── release_notes_generator.py
│       ├── pr_description_generator.py
│       ├── architecture_pattern_checker.py
│       ├── pr_review_enhancer.py
│       └── roadmap_to_epic_tool.py
├── .pre-commit-config.yaml
└── setup.py
```

## Next Steps

1. Choose your preferred implementation approach
2. Set up the necessary configuration files
3. Test each script in your environment
4. Train your team on the new tools and workflows
5. Monitor usage and gather feedback for improvements

## Support

If you encounter any issues or have questions about implementing these scripts, please contact the development team or create an issue in the repository.
