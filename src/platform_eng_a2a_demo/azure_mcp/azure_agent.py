"""
Azure MCP Client for interacting with Azure services through MCP protocol.
"""

import logging
import os

from typing import cast, AsyncIterable, Any, Literal
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from pydantic import SecretStr, BaseModel
from mcp.types import EmbeddedResource, ImageContent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection

load_dotenv()

memory = MemorySaver()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("azure_mcp_client")

NonTextContent = ImageContent | EmbeddedResource

class ResponseFormat(BaseModel):
    """Respond to the user in this format."""

    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str

class AzureMCPAgent:
    """
    Azure MCP Client for interacting with Azure services through MCP protocol.
    """
    SYSTEM_INSTRUCTION = (
        "You are a helpful assistant that can use the tools provided to help the user."
    )
    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    def __init__(self):
        """
        Initializes the AzureMCPClient with necessary configurations.
        """
        logger.info("Initializing Azure MCP Client")
        self.token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default"
        )

        self.llm = AzureChatOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
            api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            temperature=0,
            azure_ad_token=SecretStr(self.token_provider())
        )
        self.mcp_client = MultiServerMCPClient(
            {
                "azure": StdioConnection(
                    transport="stdio",
                    command="npx",
                    args=["-y", "@azure/mcp@latest", "server", "start"],
                    env=None,
                    cwd=None,
                    encoding="utf-8",
                    encoding_error_handler="strict",
                    session_kwargs=None
                )
            }
        )

    async def _create_azure_mcp_agent(self):
        """
        Creates and returns an agent that interacts with Azure MCP server.
        Returns:
            azure_mcp_agent: The created agent.
        """
        logger.info("Creating Azure MCP Agent")
        langchain_mcp_tools = await self.mcp_client.get_tools()
        for tool in langchain_mcp_tools:
            logger.info("Available tool: %s", tool.name)
        azure_mcp_agent = create_react_agent(
            self.llm,
            tools=langchain_mcp_tools,
            checkpointer=memory,
            prompt=self.SYSTEM_INSTRUCTION,
            response_format=ResponseFormat,
        )
        return azure_mcp_agent

    async def invoke_agent(self, query: str) -> dict[str, Any]:
        """
        Creates the agent and invokes it with the provided user message.
        Prints the response.
        """
        agent = await self._create_azure_mcp_agent()
        context_id = "demo-thread-1"
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
        agent = await self._create_azure_mcp_agent()
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
                    'content': 'Processing your request...',
                }
            elif isinstance(message, ToolMessage):
                yield {
                    'is_task_complete': False,
                    'require_user_input': False,
                    'content': 'Executing tools...',
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
                'We are unable to process your request at the moment. '
                'Please try again.'
            ),
        }