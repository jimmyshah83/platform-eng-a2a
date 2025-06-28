# Planner Agent

A Langchain React agent that acts as a planning layer and delegates Azure-specific operations to the Azure MCP agent via the A2A protocol.

## Overview

The Planner Agent is designed to:

1. **Analyze user queries** to determine if Azure operations are needed
2. **Plan the approach** for complex tasks
3. **Delegate Azure-specific tasks** to the Azure MCP agent via A2A protocol
4. **Provide a unified interface** for both planning and Azure operations

## Features

- **Intelligent Query Analysis**: Determines whether queries require Azure operations
- **Azure MCP Integration**: Seamlessly delegates to Azure MCP agent via A2A protocol
- **Streaming Support**: Both streaming and non-streaming response modes
- **Conversation Context**: Maintains conversation state across interactions
- **Error Handling**: Graceful error handling and recovery
- **Langchain React Agent**: Built on Langchain's React agent framework

## Architecture

```
User Query → Planner Agent → Analysis → Decision
                                    ↓
                              Azure Operation? → Yes → Azure MCP Agent (via A2A)
                                    ↓
                                   No → Direct Response
```

## Components

### PlannerAgent
The main agent class that orchestrates the planning and delegation process.

### A2ATool
A tool that handles communication with the Azure MCP agent via the A2A protocol.

### PlannerResponse
Structured response format for the planner agent.

## Usage

### Basic Usage

```python
import asyncio
from platform_eng_a2a_demo.planner_agent import PlannerAgent

async def main():
    # Initialize the planner agent
    agent = PlannerAgent(base_url='http://localhost:10001')
    
    # Send a query
    response = await agent.invoke("List all resource groups in my subscription")
    
    print(f"Status: {response['status']}")
    print(f"Message: {response['message']}")
    print(f"Requires Azure operation: {response['requires_azure_operation']}")
    
    # Clean up
    await agent.close()

asyncio.run(main())
```

### Streaming Usage

```python
async def streaming_example():
    agent = PlannerAgent(base_url='http://localhost:10001')
    
    async for chunk in agent.stream("Create a new storage account"):
        print(f"Chunk: {chunk}")
    
    await agent.close()
```

### Conversation Context

```python
async def conversation_example():
    agent = PlannerAgent(base_url='http://localhost:10001')
    context_id = "my-conversation"
    
    # First message
    response1 = await agent.invoke("I want to work with Azure resources", context_id)
    
    # Follow-up message (uses conversation context)
    response2 = await agent.invoke("List all my resource groups", context_id)
    
    await agent.close()
```

## Configuration

### Environment Variables

The planner agent requires the following environment variables for Azure OpenAI:

```bash
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
AZURE_OPENAI_API_VERSION=your_api_version
```

### A2A Server

The planner agent connects to an A2A server running on `http://localhost:10001` by default. You can customize this by passing a different `base_url` to the `PlannerAgent` constructor.

## Response Format

The planner agent returns structured responses with the following fields:

- `status`: Status of the operation ('planning', 'delegating', 'completed', 'error')
- `message`: Response message or explanation
- `requires_azure_operation`: Boolean indicating if Azure operations were required
- `azure_query`: The query sent to Azure MCP agent (if applicable)

## Example Queries

### Azure Operations (will delegate to Azure MCP agent)
- "List all resource groups in my subscription"
- "Create a new storage account in East US"
- "Show me all virtual machines"
- "Delete the resource group named 'test-rg'"

### General Questions (handled directly)
- "What is the weather like today?"
- "What is 2 + 2?"
- "Explain the difference between Azure Functions and Azure Web Apps"

### Planning Queries (may delegate or handle directly)
- "How do I deploy a web app to Azure?"
- "What's the best way to set up monitoring for my Azure resources?"

## Running the Examples

### Basic Example
```bash
python -m platform_eng_a2a_demo.example_usage
```

### Comprehensive Tests
```bash
python -m platform_eng_a2a_demo.planner_test_client
```

### Direct Agent Demo
```bash
python -m platform_eng_a2a_demo.planner_agent
```

## Error Handling

The planner agent includes comprehensive error handling:

- **Connection Errors**: Handles A2A server connection issues
- **Azure Operation Errors**: Gracefully handles Azure MCP agent errors
- **Invalid Queries**: Handles malformed or empty queries
- **Timeout Handling**: Manages long-running operations

## Dependencies

- `langchain-core`
- `langchain-openai`
- `langgraph`
- `a2a-sdk`
- `httpx`
- `azure-identity`
- `pydantic`

## Troubleshooting

### Common Issues

1. **A2A Server Not Running**
   - Ensure the A2A server is running on the expected port
   - Check the `base_url` parameter

2. **Azure Credentials**
   - Ensure Azure credentials are properly configured
   - Check environment variables for Azure OpenAI

3. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python path and module structure

### Debug Mode

Enable debug logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

When contributing to the planner agent:

1. Follow the existing code structure
2. Add appropriate error handling
3. Include tests for new features
4. Update documentation as needed

## License

This project is part of the platform-eng-a2a-demo package. 