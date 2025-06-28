"""Azure MCP demo agent module.

This module contains the AzureAgent class that wraps the AzureMCPTool
to provide a consistent interface for the A2A server.
"""
from typing import Any, AsyncIterable

from .azure_agent import AzureMCPAgent


class AzureAgent:
    """AzureAgent - a specialized assistant for Azure operations using MCP."""

    def __init__(self):
        """Initialize the AzureAgent with AzureMCPTool."""
        self.azure_mcp_tool = AzureMCPAgent()

    async def stream(self, query: str, context_id: str) -> AsyncIterable[dict[str, Any]]:
        """Stream the agent responses for a given query.
        
        Args:
            query: The user query
            context_id: The context identifier for the conversation
            
        Yields:
            dict[str, Any]: Stream of agent responses
        """
        async for item in self.azure_mcp_tool.stream(query, context_id):
            yield item

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain'] 