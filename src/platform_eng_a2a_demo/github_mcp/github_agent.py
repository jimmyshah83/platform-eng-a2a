"""
GitHub MCP Client for interacting with GitHub services through MCP protocol.
"""

import logging
import os

from typing import cast, AsyncIterable, Any, Literal
from langchain_openai import AzureChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel
from mcp.types import EmbeddedResource, ImageContent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection

from dotenv import load_dotenv
load_dotenv()

memory = MemorySaver()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("github_mcp_client")

NonTextContent = ImageContent | EmbeddedResource

class ResponseFormat(BaseModel):
    """Respond to the user in this format."""

    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str

class GitHubMCPAgent:
    """
    GitHub MCP Client for interacting with GitHub services through MCP protocol.
    """
    SYSTEM_INSTRUCTION = (
        "You are a helpful assistant that can use GitHub tools to help the user manage repositories, "
        "pull requests, issues, and other GitHub operations. Always be careful with repository operations "
        "and confirm before making any destructive changes."
    )
    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain', 'json', 'json/structured']

    def __init__(self):
        """
        Initializes the GitHubMCPClient with necessary configurations.
        """
        logger.info("Initializing GitHub MCP Client")
        
        # Check for required GitHub token
        github_token = os.environ.get("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")

        self.llm = AzureChatOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
            api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            temperature=0,
        )
        
        # Initialize GitHub MCP client
        self.mcp_client = MultiServerMCPClient(
            {
                "github": {
                    "command": "docker",
                    "args": [
                        "run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
                        "ghcr.io/github/github-mcp-server"
                    ],
                    "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": github_token},
                    "transport": "stdio",
                    "cwd": None,
                    "encoding": "utf-8",
                    "encoding_error_handler": "strict",
                    "session_kwargs": None
                }
            }
        )

    async def _create_github_mcp_agent(self):
        """
        Creates and returns an agent that interacts with GitHub MCP server.
        Returns:
            github_mcp_agent: The created agent.
        """
        logger.info("Creating GitHub MCP Agent")
        langchain_mcp_tools = await self.mcp_client.get_tools()
        for tool in langchain_mcp_tools:
            logger.info("Available GitHub tool: %s", tool.name)
        github_mcp_agent = create_react_agent(
            self.llm,
            tools=langchain_mcp_tools,
            checkpointer=memory,
            prompt=self.SYSTEM_INSTRUCTION,
            response_format=ResponseFormat,
        )
        return github_mcp_agent

    async def invoke_agent(self, query: str, context_id: str) -> dict[str, Any]:
        """
        Creates the agent and invokes it with the provided user message.
        Prints the response.
        """
        agent = await self._create_github_mcp_agent()
        config = cast(RunnableConfig, {'configurable': {'thread_id': context_id}})
        await agent.ainvoke({'messages': [('user', query)]}, config)
        return self.get_agent_response(agent, config)

    async def stream(self, query: str, context_id: str) -> AsyncIterable[dict[str, Any]]:
        """Stream the agent responses for a given query.
        
        Args:
            query: The user query
            context_id: The context identifier for the conversation
            
        Yields:
            dict[str, Any]: Stream of agent responses
        """
        agent = await self._create_github_mcp_agent()
        inputs = {'messages': [('user', query)]}
        config = cast(RunnableConfig, {'configurable': {'thread_id': context_id}})

        for item in agent.stream(inputs, config, stream_mode='values'):
            message = item['messages'][-1]
            if (
                isinstance(message, AIMessage)
                and message.tool_calls
                and len(message.tool_calls) > 0
            ):
                yield {
                    'is_task_complete': False,
                    'require_user_input': False,
                    'content': 'Processing your GitHub request...',
                }
            elif isinstance(message, ToolMessage):
                yield {
                    'is_task_complete': False,
                    'require_user_input': False,
                    'content': 'Executing GitHub tools...',
                }

        yield self.get_agent_response(agent, config)

    def get_agent_response(self, agent, config) -> dict[str, Any]:
        """Get the final agent response from the current state.
        
        Args:
            agent: The agent instance
            config: The runnable configuration
            
        Returns:
            dict: The formatted agent response
        """
        current_state = agent.get_state(config)
        structured_response = current_state.values.get('structured_response')
        if structured_response and isinstance(
            structured_response, ResponseFormat
        ):
            if structured_response.status == 'input_required':
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            if structured_response.status == 'error':
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            if structured_response.status == 'completed':
                return {
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': structured_response.message,
                }

        return {
            'is_task_complete': False,
            'require_user_input': True,
            'content': (
                'We are unable to process your GitHub request at the moment. '
                'Please try again.'
            ),
        }