# GitHub MCP Server

This module provides a GitHub MCP (Model Context Protocol) server that allows you to interact with GitHub services through an AI agent. The server uses the official GitHub MCP server to provide access to GitHub repositories, pull requests, issues, and other GitHub operations.

## Features

- **Repository Management**: List, create, and manage GitHub repositories
- **Pull Request Operations**: Create, update, and manage pull requests
- **Issue Management**: Search, create, and update issues
- **Code Search**: Search through code in repositories
- **User Management**: Search and manage GitHub users
- **Branch Operations**: Create and manage repository branches
- **File Operations**: Create, update, and delete files in repositories

## Prerequisites

1. **GitHub Token**: You need a GitHub Personal Access Token with appropriate permissions
2. **Azure OpenAI**: The agent uses Azure OpenAI for processing requests
3. **Environment Variables**: Set up the required environment variables

## Environment Variables

Create a `.env` file in your project root with the following variables:

```env
# GitHub Configuration
GITHUB_TOKEN=your_github_personal_access_token

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### GitHub Token Permissions

Your GitHub Personal Access Token should have the following permissions:
- `repo` (Full control of private repositories)
- `read:org` (Read organization data)
- `read:user` (Read user data)
- `user:email` (Read user email addresses)

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Install the GitHub MCP server:
```bash
npm install -g @github/mcp
```

## Usage

### Starting the Server

Run the GitHub MCP server:

```bash
python -m src.platform_eng_a2a_demo.github_mcp --host localhost --port 10002
```

The server will start on `http://localhost:10002` by default.

### Testing the Server

Use the test client to verify the server is working:

```bash
python src/platform_eng_a2a_demo/github_mcp/test_client.py
```

### Example Queries

Here are some example queries you can try:

- **List repositories**: "List my repositories"
- **Search repositories**: "Search for repositories with 'python' in the name"
- **Create pull request**: "Create a pull request from branch 'feature/new-feature' to 'main' in repository 'my-repo'"
- **Search issues**: "Search for open issues in repository 'my-org/my-repo'"
- **Get file contents**: "Get the contents of README.md in repository 'my-org/my-repo'"
- **Create repository**: "Create a new repository called 'my-new-project'"

## Available Tools

The GitHub MCP server provides access to many GitHub operations through the official GitHub MCP server, including:

### Repositories
- `create_repository` - Create a new repository
- `get_file_contents` - Get file or directory contents
- `create_or_update_file` - Create or update a file
- `delete_file` - Delete a file
- `list_branches` - List repository branches
- `create_branch` - Create a new branch
- `list_commits` - List commits
- `get_commit` - Get commit details
- `search_repositories` - Search repositories

### Pull Requests
- `create_pull_request` - Create a new pull request
- `list_pull_requests` - List pull requests
- `get_pull_request` - Get pull request details
- `update_pull_request` - Update a pull request
- `submit_pending_pull_request_review` - Submit a pull request review

### Issues
- `create_issue` - Create a new issue
- `list_issues` - List issues
- `get_issue` - Get issue details
- `update_issue` - Update an issue
- `search_issues` - Search issues

### Code Search
- `search_code` - Search code in repositories

### Users
- `search_users` - Search GitHub users

## Architecture

The GitHub MCP server follows the same architecture as the Azure MCP server:

1. **GitHubMCPAgent**: Main agent class that handles GitHub operations
2. **GitHubMCPAgentExecutor**: Executor that manages task execution flow
3. **MCP Client**: Connects to the official GitHub MCP server
4. **LangChain Integration**: Uses LangChain for AI processing

## Error Handling

The server includes comprehensive error handling for:
- Missing GitHub token
- Invalid API responses
- Network connectivity issues
- Permission errors

## Security Considerations

- Never commit your GitHub token to version control
- Use environment variables for sensitive configuration
- Regularly rotate your GitHub Personal Access Token
- Use the minimum required permissions for your GitHub token

## Troubleshooting

### Common Issues

1. **Missing GitHub Token**: Ensure `GITHUB_TOKEN` is set in your environment
2. **Permission Errors**: Verify your GitHub token has the required permissions
3. **Network Issues**: Check your internet connection and GitHub API status
4. **Port Conflicts**: Change the port if 10002 is already in use

### Debug Mode

Enable debug logging by setting the log level:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

When contributing to this module:

1. Follow the existing code patterns
2. Add appropriate error handling
3. Include tests for new functionality
4. Update documentation for new features

## License

This module is part of the platform-eng-a2a project and follows the same license terms.

## Running with Docker

You can run the GitHub MCP server in a Docker container. Here is a sample `Dockerfile` you can use:

```Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y npm && rm -rf /var/lib/apt/lists/*

# Install GitHub MCP server globally
RUN npm install -g @github/mcp@latest

# Set workdir
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip && pip install .

# Expose the default port
EXPOSE 10002

# Set environment variables (override in docker-compose or at runtime)
ENV GITHUB_TOKEN=your_github_token \
    AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint \
    AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name \
    AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Start the server
CMD ["python", "-m", "src.platform_eng_a2a_demo.github_mcp", "--host", "0.0.0.0", "--port", "10002"]
```

### Build and Run

1. Build the Docker image:
   ```bash
   docker build -t github-mcp-server .
   ```
2. Run the container (make sure to set the required environment variables):
   ```bash
   docker run -e GITHUB_TOKEN=your_github_token \
              -e AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint \
              -e AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name \
              -e AZURE_OPENAI_API_VERSION=2024-02-15-preview \
              -p 10002:10002 github-mcp-server
   ```

This will start the GitHub MCP server inside a Docker container, accessible on port 10002. 