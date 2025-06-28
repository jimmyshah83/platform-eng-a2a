"""
A2A Tool for interacting with Azure MCP agent via A2A protocol.

This module contains a tool function that handles communication with the Azure MCP agent
through the A2A protocol using Langchain's @tool decorator.
"""

import asyncio
import logging
from typing import Any, AsyncIterable
from uuid import uuid4

import httpx
from langchain_core.tools import tool

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
)

logger = logging.getLogger(__name__)


@tool
def azure_mcp_agent(query: str, base_url: str = "http://localhost:10001") -> str:
    """
    Interact with Azure services through the Azure MCP agent.
    
    Args:
        query: The query to send to the Azure MCP agent
        base_url: Base URL for the A2A server (default: http://localhost:10001)
        
    Returns:
        str: Response from the Azure MCP agent
    """
    return asyncio.run(_invoke_azure_mcp_agent(query, base_url))


async def _invoke_azure_mcp_agent(query: str, base_url: str) -> str:
    """Invoke the Azure MCP agent with a query."""
    timeout = httpx.Timeout(60.0)
    
    async with httpx.AsyncClient(timeout=timeout) as httpx_client:
        # Initialize A2ACardResolver
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )
        
        try:
            logger.info("Fetching agent card from: %s/.well-known/agent.json", base_url)
            agent_card = await resolver.get_agent_card()
            logger.info("Successfully fetched agent card")
            
            # Initialize A2A Client
            a2a_client = A2AClient(
                httpx_client=httpx_client,
                agent_card=agent_card
            )
            
        except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException) as e:
            logger.error("Failed to initialize A2A client: %s", e)
            raise RuntimeError(f"Failed to initialize A2A client: {e}") from e
        except ValueError as e:
            logger.error("Invalid configuration for A2A client: %s", e)
            raise RuntimeError(f"Invalid configuration for A2A client: {e}") from e
        
        # Prepare the message
        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {'kind': 'text', 'text': query}
                ],
                'messageId': uuid4().hex,
            },
        }
        
        request = SendMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**send_message_payload)
        )
        
        try:
            logger.info("Sending query to Azure MCP agent: %s", query)
            response = await a2a_client.send_message(request)
            response_dict = response.model_dump(mode='json', exclude_none=True)
            logger.info("Response received from Azure MCP agent: %s", response_dict)
            return response_dict['message']['parts'][0]['text']
            
        except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException) as e:
            logger.error("Error invoking Azure MCP agent: %s", e)
            return f"Error: {str(e)}"
        except ValueError as e:
            logger.error("Invalid request format: %s", e)
            return f"Error: Invalid request format - {str(e)}"


async def stream_azure_mcp_agent(query: str, base_url:
    str = "http://localhost:10001") -> AsyncIterable[str]:
    """Stream responses from the Azure MCP agent."""
    timeout = httpx.Timeout(60.0)
    
    async with httpx.AsyncClient(timeout=timeout) as httpx_client:
        # Initialize A2ACardResolver
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )
        
        try:
            logger.info("Fetching agent card from: %s/.well-known/agent.json", base_url)
            agent_card = await resolver.get_agent_card()
            logger.info("Successfully fetched agent card")
            
            # Initialize A2A Client
            a2a_client = A2AClient(
                httpx_client=httpx_client,
                agent_card=agent_card
            )
            
        except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException) as e:
            logger.error("Failed to initialize A2A client: %s", e)
            yield f"Error: Failed to initialize A2A client - {str(e)}"
            return
        except ValueError as e:
            logger.error("Invalid configuration for A2A client: %s", e)
            yield f"Error: Invalid configuration for A2A client - {str(e)}"
            return
        
        # Prepare the streaming message
        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {'kind': 'text', 'text': query}
                ],
                'messageId': uuid4().hex,
            },
        }
        
        streaming_request = SendStreamingMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**send_message_payload)
        )
        
        try:
            logger.info("Streaming query to Azure MCP agent: %s", query)
            stream_response = a2a_client.send_message_streaming(streaming_request)
            
            async for chunk in stream_response:
                chunk_dict = chunk.model_dump(mode='json', exclude_none=True)
                logger.debug("Received chunk: %s", chunk_dict)
                yield chunk_dict
                            
        except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException) as e:
            logger.error("Error streaming from Azure MCP agent: %s", e)
            yield f"Error: {str(e)}"
        except ValueError as e:
            logger.error("Invalid streaming request format: %s", e)
            yield f"Error: Invalid request format - {str(e)}" 