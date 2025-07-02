"""Test client for GitHub MCP demo.

This module contains a test client that demonstrates how to use the A2A client
to interact with the GitHub MCP agent.
"""
import asyncio
import logging
from typing import Any
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    MessageSendParams,
    SendStreamingMessageRequest
)
from dotenv import load_dotenv

load_dotenv()

async def main() -> None:
    """Main function to test the GitHub MCP agent client."""
    # Configure logging to show INFO level messages
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)  # Get a logger instance

    base_url = 'http://localhost:10002'

    # Create httpx client with longer timeout for GitHub operations
    timeout = httpx.Timeout(60.0)  # 60 seconds timeout
    async with httpx.AsyncClient(timeout=timeout) as httpx_client:
        # Initialize A2ACardResolver
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )

        # Fetch Public Agent Card and Initialize Client
        try:
            logger.info(
                'Attempting to fetch public agent card from: %s/.well-known/agent.json',
                base_url
            )
            agent_card = await resolver.get_agent_card()
            logger.info('Successfully fetched public agent card:')
            logger.info(
                agent_card.model_dump_json(indent=2, exclude_none=True)
            )

        except httpx.HTTPError as e:
            logger.error(
                'Critical error fetching public agent card: %s', e, exc_info=True
            )
            raise RuntimeError(
                'Failed to fetch the public agent card. Cannot continue.'
            ) from e

        # Initialize A2A Client
        client = A2AClient(
            httpx_client=httpx_client, agent_card=agent_card
        )
        logger.info('A2AClient initialized.')

        # Test streaming message for GitHub operations
        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {'kind': 'text', 'text': 'List my repositories'}
                ],
                'messageId': uuid4().hex,
            },
        }

        # Test streaming message
        logger.info('Sending streaming message for GitHub operations...')
        streaming_request = SendStreamingMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**send_message_payload)
        )

        stream_response = client.send_message_streaming(streaming_request)
        print("Streaming response:")
        async for chunk in stream_response:
            print(chunk.model_dump(mode='json', exclude_none=True))


if __name__ == "__main__":
    asyncio.run(main()) 