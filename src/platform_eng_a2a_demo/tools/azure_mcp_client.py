"""
Azure MCP Client for interacting with Azure services through MCP protocol.
"""

import logging
import os

from typing import cast, Any
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, ToolException, StructuredTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from pydantic import SecretStr, BaseModel
from mcp.types import CallToolResult, EmbeddedResource, ImageContent, TextContent, Tool as MCPTool
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


def _convert_call_tool_result(
    call_tool_result: CallToolResult,
) -> tuple[str | list[str], list[NonTextContent] | None]:

    """Convert an MCP tool call result to a LangChain tool result."""

    text_contents: list[TextContent] = []
    non_text_contents = []    
    for content in call_tool_result.content:
        if isinstance(content, TextContent):
            text_contents.append(content)
        else:
            non_text_contents.append(content)    
    tool_content: str | list[str] = [content.text for content in text_contents]    
    if len(text_contents) == 1:
        tool_content = tool_content[0]
    if call_tool_result.isError:
        raise ToolException(tool_content)    
    return tool_content, non_text_contents or None

def _convert_mcp_tool_to_langchain_tool(session: ClientSession, tool: MCPTool) -> BaseTool:
    """Convert an MCP tool to a LangChain tool."""
    async def call_tool(**arguments: Any,) -> tuple[str | list[str], list[NonTextContent] | None]:
        call_tool_result = await session.call_tool(tool.name, arguments)
        return _convert_call_tool_result(call_tool_result)    
    return StructuredTool(
        name=tool.name,
        description=tool.description or "",
        args_schema=tool.inputSchema,
        coroutine=call_tool,
        response_format="content_and_artifact",
    )

async def _load_mcp_tools(session: ClientSession) -> list[BaseTool]:
    """Load all available MCP tools and convert them to LangChain tools."""
    tools = await session.list_tools()
    return [_convert_mcp_tool_to_langchain_tool(session, tool) for tool in tools.tools] 

if __name__ == "__main__":
    import asyncio
    CLIENT = AzureMCPClient()
    asyncio.run(CLIENT.invoke_agent("List all of the resource groups in my subscription"))