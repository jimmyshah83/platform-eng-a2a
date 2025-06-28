"""
Platform Engineering A2A Demo Package.

This package contains demonstrations of Azure MCP agent integration with A2A protocol,
including a planner agent that can delegate Azure operations to the Azure MCP agent.
"""

from .planner import PlannerAgent
from .azure_mcp import AzureAgent, AzureMCPAgent, AzureMCPTool, AzureMCPAgentExecutor

__all__ = ["PlannerAgent", "AzureAgent", "AzureMCPAgent", "AzureMCPTool", "AzureMCPAgentExecutor"]
