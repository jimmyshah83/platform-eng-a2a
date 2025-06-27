"""
Azure MCP Client for interacting with Azure services through MCP protocol.
"""

import logging
import os

from typing import cast
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, StructuredTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from pydantic import SecretStr, BaseModel
from mcp.types import EmbeddedResource, ImageContent, Tool as MCPTool
from mcp import ClientSession, StdioServerParameters, stdio_client

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
    
    message: str

class AzureMCPClient:
    """
    Azure MCP Client for interacting with Azure services through MCP protocol.
    """
    
    SYSTEM_INSTRUCTION = (
        "You are a helpful assistant that can use the tools provided to help the user."
    )

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
        self.server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@azure/mcp@latest", "server", "start"],
            env=None
        )

    async def _create_azure_mcp_agent(self):
        """
        Creates and returns an agent that interacts with Azure MCP server.
        Returns:
            azure_mcp_agent: The created agent.
        """
        logger.info("Creating Azure MCP Agent")
        async with stdio_client(self.server_params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                langchain_mcp_tools = await _load_mcp_tools(session)
                for tool in langchain_mcp_tools:
                    print(tool.name)
                azure_mcp_agent = create_react_agent(
                    self.llm,
                    tools=langchain_mcp_tools,
                    checkpointer=memory,
                    prompt=self.SYSTEM_INSTRUCTION,
                    response_format=ResponseFormat,
                )
                return azure_mcp_agent

    async def invoke_agent(self, user_message: str):
        """
        Creates the agent and invokes it with the provided user message.
        Prints the response.
        """
        agent = await self._create_azure_mcp_agent()
        context_id = "demo-thread-1"
        config = cast(RunnableConfig, {'configurable': {'thread_id': context_id}})
        response = agent.invoke({'messages': [('user', user_message)]}, config)
        print("Agent response:", response)

def _convert_mcp_tool_to_langchain_tool(tool: MCPTool) -> BaseTool:
    """Convert an MCP tool to a LangChain tool."""
    return StructuredTool(
        name=tool.name,
        description=tool.description or "",
        args_schema=tool.inputSchema
    )

async def _load_mcp_tools(session: ClientSession) -> list[BaseTool]:
    """Load all available MCP tools and convert them to LangChain tools."""
    tools = await session.list_tools()
    return [_convert_mcp_tool_to_langchain_tool(tool) for tool in tools.tools] 

if __name__ == "__main__":
    import asyncio
    CLIENT = AzureMCPClient()
    asyncio.run(CLIENT.invoke_agent("List all of the resource groups in my subscription id 57123c17-af1a-4ec2-9494-a214fb148bf4"))