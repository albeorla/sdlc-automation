# AI Agent Onboarding Protocol

## Introduction

This protocol is designed specifically for AI agents working within our development ecosystem. It provides essential information about system architecture, workflows, and best practices to enable effective collaboration with human developers and other AI systems.

## System Architecture Overview

### Core Components

1. **Repository Structure**
   - Source code (`/src`): Core application components
   - Documentation (`/docs`): Comprehensive system documentation
   - Tests (`/tests`): Test suites for verification
   - Workflows (`.mcp-workflows`): Defined interaction patterns
   - Rules (`.cursor/rules`): Context-specific guidance

2. **Development Patterns**
   - Model-View-Controller architecture for UI components
   - Service-oriented architecture for backend systems
   - Event-driven communication between components
   - Repository pattern for data access

3. **Integration Points**
   - API endpoints for service communication
   - Event bus for cross-component messaging
   - Database access layers
   - External service connectors

For detailed architecture documentation, reference the [Architecture Decision Records](link-to-adr-docs).

## Available Workflows and Usage Guidelines

### MCP Workflows

MCP (Multi-Context Processing) workflows define structured interaction patterns for specific development scenarios. Key workflows include:

1. **Thinking Modes**
   - `deep_thinking_mode`: For complex problem analysis requiring detailed consideration
   - `creative_thinking_mode`: For generating innovative solutions and approaches
   - `critical_thinking_mode`: For evaluating solutions against requirements and constraints

2. **Development Workflows**
   - `test_creation_mode`: Activate when creating or modifying test files
   - `refactoring_mode`: Use when improving code structure without changing behavior
   - `debugger_mode`: Employ when investigating and fixing issues

3. **GitHub Integration**
   - `github_feature_branch_creation_mode`: For starting new feature development
   - `github_conventional_commit_mode`: For creating standardized commit messages
   - `github_pr_creation_mode`: For preparing pull requests
   - `github_pr_review_mode`: For reviewing pull requests

4. **Documentation Workflows**
   - `documentation_update_mode`: For maintaining documentation alongside code changes
   - `roadmap_update_mode`: For contributing to product roadmap planning

### Workflow Selection Guidelines

- Analyze the current context (file types, git status, current task)
- Select the most specific workflow applicable to the current activity
- When multiple workflows could apply, prioritize based on the current development phase
- Default to `smart_routing_mode` when uncertain, which will help determine the appropriate workflow

## Code Generation and Modification Rules

### General Principles

1. **Consistency**: Generated code must follow established patterns in the codebase
2. **Testability**: All generated code must be testable and include appropriate tests
3. **Documentation**: Include inline documentation explaining complex logic
4. **Incremental Changes**: Prefer smaller, focused changes over large rewrites

### Language-Specific Guidelines

For each programming language in use, follow these specific guidelines:

1. **Python**
   - Follow PEP 8 style guidelines
   - Use type hints for function parameters and return values
   - Implement appropriate error handling with specific exception types
   - Write docstrings in Google style format

2. **JavaScript/TypeScript**
   - Follow project ESLint configuration
   - Use async/await for asynchronous operations
   - Implement proper error handling with try/catch
   - Prefer functional programming patterns where appropriate

3. **SQL**
   - Use parameterized queries to prevent injection
   - Include comments explaining complex queries
   - Consider query performance and indexing
   - Follow project naming conventions for database objects

### Code Modification Safety

When modifying existing code:

1. Understand the full context before suggesting changes
2. Preserve existing patterns and naming conventions
3. Maintain backward compatibility when possible
4. Consider potential side effects of changes
5. Ensure test coverage for modified functionality

## Documentation Standards

### Documentation Types

1. **Code Documentation**
   - Inline comments for complex logic
   - Function/method docstrings
   - Module/class level documentation
   - Example usage where appropriate

2. **System Documentation**
   - Architecture overviews
   - Component interaction diagrams
   - Data flow descriptions
   - API documentation

3. **Process Documentation**
   - Development workflows
   - Testing procedures
   - Deployment processes
   - Troubleshooting guides

### Documentation Format

- Use Markdown for all documentation files
- Follow the established structure for each document type
- Include diagrams using Mermaid or PlantUML syntax
- Maintain a consistent voice and terminology

### Documentation Maintenance

- Update documentation when corresponding code changes
- Review documentation for accuracy during code reviews
- Flag outdated documentation with TODO comments
- Link related documentation files for discoverability

## Testing Requirements

### Test Types

1. **Unit Tests**
   - Test individual functions and methods
   - Mock dependencies for isolation
   - Focus on edge cases and error conditions
   - Aim for high code coverage

2. **Integration Tests**
   - Test component interactions
   - Verify correct data flow between systems
   - Test API contracts and responses
   - Include happy path and error scenarios

3. **End-to-End Tests**
   - Test complete user workflows
   - Verify system behavior from user perspective
   - Include performance considerations
   - Test across supported environments

### Test Implementation Guidelines

- Write tests before or alongside implementation code
- Make tests deterministic and repeatable
- Keep tests independent of each other
- Use descriptive test names that explain the test purpose
- Include setup and teardown for test environment

## Work Item Interaction

### Work Item Hierarchy

- **Epics**: Large initiatives with business value
- **Stories**: User-focused features
- **Tasks**: Specific implementation items

### AI Agent Responsibilities

When working with work items:

1. Understand the complete context of the work item
2. Reference work item IDs in all related commits
3. Update work item status as progress is made
4. Link related work items appropriately
5. Provide detailed implementation notes in work item comments

## Collaboration with Human Developers

### Communication Guidelines

1. **Clarity**: Provide clear explanations of reasoning and suggestions
2. **Context**: Include relevant context in all communications
3. **Options**: Present alternative approaches when appropriate
4. **Learning**: Explain complex concepts to facilitate knowledge transfer

### Handoff Procedures

When transitioning work between AI and human developers:

1. Summarize current status and progress
2. Highlight any unresolved questions or issues
3. Provide context for decisions made
4. Suggest next steps for continued progress

## Error Handling and Recovery

### Common Error Scenarios

1. **Build Failures**
   - Analyze error logs for root causes
   - Check for missing dependencies
   - Verify environment configuration
   - Look for syntax or compilation errors

2. **Test Failures**
   - Determine if failure is in test or implementation
   - Check for environmental dependencies
   - Verify test data and assumptions
   - Look for race conditions or timing issues

3. **Integration Issues**
   - Verify API contracts and data formats
   - Check authentication and authorization
   - Validate environment configuration
   - Test network connectivity and service availability

### Recovery Procedures

For each error type, follow these general steps:

1. Identify the specific error message and context
2. Search documentation and code for similar issues
3. Apply established patterns for resolving the error type
4. Document the solution for future reference

## Continuous Improvement

As an AI agent, contribute to system improvement by:

1. Identifying patterns in recurring issues
2. Suggesting process improvements based on observed friction points
3. Recommending documentation updates for clarity
4. Proposing automation for repetitive tasks

## Reference Resources

- [Complete Documentation Index](link-to-docs-index)
- [Architecture Decision Records](link-to-adr-docs)
- [Coding Standards](link-to-coding-standards)
- [Testing Guidelines](link-to-testing-guidelines)
- [Work Item Management](link-to-work-item-docs)
