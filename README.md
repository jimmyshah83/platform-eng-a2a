# Platform Engineering A2A Demo

This repository contains demonstrations of Agent-to-Agent (A2A) communication using the A2A protocol, featuring both a Planner Agent and an Azure MCP Agent.

## Prerequisites

- Python 3.8+
- [uv](https://docs.astral.sh/uv/) package manager
- Azure subscription with OpenAI service
- Node.js (for Azure MCP server)

## Setup

### 1. Install uv

If you haven't installed uv yet:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone and Setup Project

```bash
# Clone the repository
git clone <repository-url>
cd platform-eng-a2a

# Create virtual environment and install dependencies
uv sync
```

### 3. Environment Configuration

Create a `.env` file in the project root with your Azure OpenAI credentials:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Optional: Customize server settings
A2A_SERVER_HOST=localhost
A2A_SERVER_PORT=10001
```

### 4. Install Azure MCP Server

The Azure MCP agent requires the Azure MCP server to be available:

```bash
# Install Azure MCP server globally
npm install -g @azure/mcp
```

## Running the Demos

### Option 1: Azure MCP Agent Demo

The Azure MCP Agent provides direct access to Azure services through the MCP protocol.

#### Start the A2A Server

```bash
# Start the Azure MCP agent server
uv run azure-mcp --host localhost --port 10001
```

The server will start on `http://localhost:10001` and expose the agent card at `http://localhost:10001/.well-known/agent.json`.

#### Test the Azure MCP Agent

In a separate terminal, run the test client:

```bash
# Test the Azure MCP agent
uv run python src/platform_eng_a2a_demo/azure_mcp/test_client.py
```

The test client will:
1. Fetch the agent card from the server
2. Send a test message asking for Azure best practices
3. Display the response

### Option 2: Planner Agent Demo

The Planner Agent acts as a planning layer that can delegate Azure operations to the Azure MCP agent.

#### Start the Azure MCP Agent Server (Required)

First, start the Azure MCP agent server as described above:

```bash
uv run azure-mcp --host localhost --port 10001
```

#### Run the Planner Agent

In a separate terminal:

```bash
# Run the planner agent with a query
uv run planner --query "Help me plan a deployment strategy for Azure resources"
uv run planner --query "Show me the resource groups in my subscription"

# Or run interactively (will prompt for query)
uv run planner
```

The planner agent will:
1. Analyze your query to determine if Azure operations are needed
2. Plan the approach for complex tasks
3. Delegate Azure-specific operations to the Azure MCP agent
4. Provide unified responses

### Option 3: Currency Exchange Demo

There's also a currency exchange demo available:

```bash
uv run currency-exchange
```

## Development

### Project Structure

```
src/
├── platform_eng_a2a_demo/
│   ├── azure_mcp/           # Azure MCP Agent implementation
│   │   ├── __main__.py      # Server entry point
│   │   ├── azure_agent.py   # Azure MCP client
│   │   ├── agent_executor.py # A2A agent executor
│   │   └── test_client.py   # Test client
│   └── planner/             # Planner Agent implementation
│       ├── __main__.py      # CLI entry point
│       ├── planner_agent.py # Planner agent logic
│       └── tools/
│           └── a2a_tool.py  # A2A integration tool
└── currency_exchange_demo/  # Currency exchange demo
```

### Available Commands

- `uv run azure-mcp` - Start the Azure MCP agent server
- `uv run planner` - Run the planner agent
- `uv run currency-exchange` - Run the currency exchange demo

### Testing

Run tests with pytest:

```bash
uv run pytest
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | Yes |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Azure OpenAI deployment name | Yes |
| `AZURE_OPENAI_API_VERSION` | Azure OpenAI API version | Yes |
| `A2A_SERVER_HOST` | A2A server host (default: localhost) | No |
| `A2A_SERVER_PORT` | A2A server port (default: 10001) | No |

## Troubleshooting

### Common Issues

1. **Azure MCP Server Not Found**
   - Ensure you have Node.js installed
   - Install the Azure MCP server: `npm install -g @azure/mcp`

2. **Authentication Errors**
   - Verify your Azure credentials are properly configured
   - Ensure your Azure subscription has access to OpenAI services

3. **Port Already in Use**
   - Change the port using the `--port` flag
   - Kill any existing processes using the port

4. **Import Errors**
   - Ensure all dependencies are installed: `uv sync`
   - Check that you're running from the project root

### Debug Mode

Enable debug logging by setting the log level:

```bash
export LOG_LEVEL=DEBUG
uv run azure-mcp
```

## Architecture

### A2A Protocol

The Agent-to-Agent (A2A) protocol enables secure communication between AI agents. This demo showcases:

- **Agent Cards**: Self-describing agent metadata
- **Message Exchange**: Structured communication between agents
- **Tool Delegation**: Agents can invoke tools on behalf of other agents

### Components

1. **Azure MCP Agent**: Direct Azure service integration via MCP protocol
2. **Planner Agent**: High-level planning and task delegation
3. **A2A Client/Server**: Protocol implementation for agent communication

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

See [LICENSE](LICENSE) for details.