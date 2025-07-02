"""GitHub MCP Demo - Main module for starting the GitHub MCP Agent server."""

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

from .github_agent import GitHubMCPAgent
from .agent_executor import GitHubMCPAgentExecutor


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10002)
def main(host, port):
    """Starts the GitHub MCP Agent server."""
    try:

        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
        skill = AgentSkill(
            id="github_operations",
            name="GitHub Operations Tool",
            description="Helps with GitHub repository management, pull requests, issues, and other GitHub operations",
            tags=["github", "repository", "pull-requests", "issues"],
            examples=["List my repositories", "Create a new pull request", "Search for issues"],
        )
        agent_card = AgentCard(
            name="GitHub MCP Agent",
            description="GitHub MCP agent for managing repositories, pull requests, issues, and other GitHub operations",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=GitHubMCPAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=GitHubMCPAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        # --8<-- [start:DefaultRequestHandler]
        httpx_client = httpx.AsyncClient()
        request_handler = DefaultRequestHandler(
            agent_executor=GitHubMCPAgentExecutor(),
            task_store=InMemoryTaskStore(),
            push_notifier=InMemoryPushNotifier(httpx_client),
        )
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )

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