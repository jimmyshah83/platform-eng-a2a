"""
Azure MCP module for Azure service integration.

This module contains the Azure MCP agent and related components for
interacting with Azure services through the MCP protocol.
"""

from .azure_agent import AzureMCPAgent
from .agent_executor import AzureMCPAgentExecutor

__all__ = ["AzureMCPAgent", "AzureMCPAgentExecutor"] 