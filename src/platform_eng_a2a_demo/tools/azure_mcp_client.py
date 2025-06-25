"""
Azure MCP Client for interacting with Azure services through MCP protocol.
"""
import logging
import os

from langchain_openai import AzureChatOpenAI
from mcp import ClientSession, StdioServerParameters, stdio_client
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from pydantic import SecretStr

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("azure_mcp_client")


class AzureMCPClient:
    """
    Azure MCP Client for interacting with Azure services through MCP protocol.
    """

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
            azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME_41"],
            api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            temperature=0,
            azure_ad_token=SecretStr(self.token_provider())
        )
        self.server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@azure/mcp@latest", "server", "start"],
            env=None
        )

    async def create_azure_mcp_client(self):
        """
        Creates an agent that interacts with Azure MCP server.
        Returns:
            list: Available tools from the MCP session.
        """
        logger.info("Creating Azure MCP Agent")
        async with stdio_client(self.server_params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                tools = await session.list_tools()
                available_tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool_obj.name,
                            "description": tool_obj.description,
                            "parameters": tool_obj.parameters,
                            "required": tool_obj.required,
                            "type": tool_obj.type,
                            "enum": tool_obj.enum,
                            "default": tool_obj.default,
                            "example": tool_obj.example,
                            "examples": tool_obj.examples,
                        }
                    }
                    for _, tool_obj in tools
                ]
                logger.debug("Available tools: %s", available_tools)
                
                return available_tools
                