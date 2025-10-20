"""Azure MCP Demo - Main module for starting the Azure MCP Agent server."""

import logging
import sys

import click
import httpx
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryPushNotifier, InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from dotenv import load_dotenv

from .azure_agent import AzureMCPAgent
from .agent_executor import AzureMCPAgentExecutor


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10001)
def main(host, port):
    """Starts the Azure MCP Agent server."""
    print(f"\n{'='*60}")
    print(f"Starting Azure MCP Agent Server")
    print(f"{'='*60}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"{'='*60}\n")
    
    try:

        print("Configuring agent capabilities...")
        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
        skill = AgentSkill(
            id="azure_operations",
            name="Azure Operations Tool",
            description="Helps with Azure resource management and operations",
            tags=["azure", "cloud", "resource management"],
            examples=["List all resource groups in my subscription"],
        )
        print("Creating agent card...")
        agent_card = AgentCard(
            name="Azure MCP Agent",
            description="Azure MCP agent for managing Azure resources and services",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=AzureMCPAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=AzureMCPAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        # --8<-- [start:DefaultRequestHandler]
        print("Initializing HTTP client and request handler...")
        httpx_client = httpx.AsyncClient()
        request_handler = DefaultRequestHandler(
            agent_executor=AzureMCPAgentExecutor(),
            task_store=InMemoryTaskStore(),
            push_notifier=InMemoryPushNotifier(httpx_client),
        )
        print("Building server application...")
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )

        print(f"\n{'='*60}")
        print(f"Server ready! Listening on http://{host}:{port}")
        print(f"{'='*60}\n")
        uvicorn.run(server.build(), host=host, port=port)
        # --8<-- [end:DefaultRequestHandler]

    except MissingAPIKeyError as e:
        logger.error("Error: %s", e)
        sys.exit(1)
    except (OSError, ValueError, RuntimeError) as e:
        logger.error("An error occurred during server startup: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main() 