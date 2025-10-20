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
    print(f"\n{'='*60}")
    print(f"[A2A Tool] azure_mcp_agent tool INVOKED!")
    print(f"{'='*60}")
    print(f"[A2A Tool] Query: {query}")
    print(f"[A2A Tool] Base URL: {base_url}")
    print(f"{'='*60}\n")
    logger.info("azure_mcp_agent tool invoked with query: %s", query)
    
    result = asyncio.run(_invoke_azure_mcp_agent(query, base_url))
    
    print(f"\n[A2A Tool] Tool execution completed")
    print(f"[A2A Tool] Result: {result}\n")
    
    return result


async def _invoke_azure_mcp_agent(query: str, base_url: str) -> str:
    """Invoke the Azure MCP agent with a query."""
    print(f"[A2A Tool] Starting _invoke_azure_mcp_agent...")
    timeout = httpx.Timeout(60.0)
    
    async with httpx.AsyncClient(timeout=timeout) as httpx_client:
        # Initialize A2ACardResolver
        print(f"[A2A Tool] Initializing A2ACardResolver with base_url: {base_url}")
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )
        
        try:
            print(f"[A2A Tool] Fetching agent card from: {base_url}/.well-known/agent.json")
            logger.info("Fetching agent card from: %s/.well-known/agent.json", base_url)
            agent_card = await resolver.get_agent_card()
            print(f"[A2A Tool] Successfully fetched agent card")
            logger.info("Successfully fetched agent card")
            
            # Initialize A2A Client
            print(f"[A2A Tool] Initializing A2A Client...")
            a2a_client = A2AClient(
                httpx_client=httpx_client,
                agent_card=agent_card
            )
            print(f"[A2A Tool] A2A Client initialized successfully")
            
        except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException) as e:
            print(f"[A2A Tool] ERROR: Failed to initialize A2A client: {e}")
            logger.error("Failed to initialize A2A client: %s", e)
            raise RuntimeError(f"Failed to initialize A2A client: {e}") from e
        except ValueError as e:
            print(f"[A2A Tool] ERROR: Invalid configuration for A2A client: {e}")
            logger.error("Invalid configuration for A2A client: %s", e)
            raise RuntimeError(f"Invalid configuration for A2A client: {e}") from e
        
        # Prepare the message
        print(f"[A2A Tool] Preparing message payload...")
        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {'kind': 'text', 'text': query}
                ],
                'messageId': uuid4().hex,
            },
        }
        
        print(f"[A2A Tool] Creating SendMessageRequest...")
        request = SendMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**send_message_payload)
        )
        
        try:
            print(f"[A2A Tool] Sending query to Azure MCP agent: {query}")
            logger.info("Sending query to Azure MCP agent: %s", query)
            response = await a2a_client.send_message(request)
            response_dict = response.model_dump(mode='json', exclude_none=True)
            print(f"[A2A Tool] Response received from Azure MCP agent")
            logger.info("Response received from Azure MCP agent: %s", response_dict)
            result_text = response_dict['message']['parts'][0]['text']
            print(f"[A2A Tool] Extracted response text: {result_text}")
            return result_text
            
        except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException) as e:
            print(f"[A2A Tool] ERROR: HTTP/Connection/Timeout error: {e}")
            logger.error("Error invoking Azure MCP agent: %s", e)
            return f"Error: {str(e)}"
        except ValueError as e:
            print(f"[A2A Tool] ERROR: Invalid request format: {e}")
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