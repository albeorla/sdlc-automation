# SDLC Automation

This repository contains the TypeScript implementation of Phase 2 (Automation & Integration) of the SDLC streamlining plan, focusing on automating manual steps and connecting system components using SOLID principles, Object-Oriented Design, and appropriate design patterns.

## Project Structure

The project follows a clean, hexagonal architecture:

- **Core Domain**: Entities and business rules
- **Application Layer**: Use cases and services
- **Adapters Layer**: Integration with external systems
- **Infrastructure Layer**: Technical implementations
- **Presentation Layer**: CLI and MCP interfaces

## Features

- Work item creation and management
- Commit message validation
- Documentation checking and release notes generation
- PR review and architecture checking
- Roadmap to epic conversion
- MCP integration

## Getting Started

### Prerequisites

- Node.js 16+
- npm or yarn
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/sdlc-automation.git
cd sdlc-automation

# Install dependencies
npm install

# Build the project
npm run build
```

### Configuration

Create a `.env` file in the root directory with the following variables:

```
# GitHub configuration
GITHUB_TOKEN=your_github_token

# OpenAI configuration (if needed)
OPENAI_API_KEY=your_openai_api_key
```

Make sure to add `.env` to your `.gitignore` file to prevent committing sensitive information.

### Usage

```bash
# Run the CLI
npm start -- [command] [options]

# Examples:
npm start -- create-work-items --epic-file path/to/epic.md
npm start -- validate-commit --message "feat(core): add new feature"
npm start -- check-documentation --base-ref main --head-ref feature-branch
```

## MCP Integration

This project can be integrated with the Model Context Protocol (MCP) framework:

1. Start the MCP server:
   ```bash
   npm start -- mcp-server
   ```

2. Configure your MCP client to connect to the server.

3. Use the provided workflows in your MCP client.

## Development

```bash
# Run in development mode
npm run dev

# Run tests
npm test

# Lint code
npm run lint

# Format code
npm run format
```

## License

MIT
