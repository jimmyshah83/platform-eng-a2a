"""
Planner Agent - A Langchain React agent that invokes Azure MCP agent via A2AClient.

This module contains the PlannerAgent class that acts as a planning layer,
delegating Azure-specific operations to the Azure MCP agent through the A2A protocol.
"""

import asyncio
import logging
from typing import Any, AsyncIterable, Dict, Optional
import os
from dotenv import load_dotenv

import httpx
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field, SecretStr
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from .tools.a2a_tool import azure_mcp_agent

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize memory for conversation state
memory = MemorySaver()


class PlannerResponse(BaseModel):
    """Response format for the planner agent."""
    
    status: str = Field(description="Status of the operation: 'planning', 'delegating', 'completed', 'error'")
    message: str = Field(description="Response message or explanation")
    requires_azure_operation: bool = Field(description="Whether this requires Azure operations")
    azure_query: Optional[str] = Field(description="The query to send to Azure MCP agent", default=None)


class PlannerAgent:
    """
    Planner Agent - A Langchain React agent that plans and delegates to Azure MCP agent.
    
    This agent acts as a planning layer that:
    1. Analyzes user queries to determine if Azure operations are needed
    2. Plans the approach for Azure operations
    3. Delegates Azure-specific tasks to the Azure MCP agent via A2A protocol
    4. Provides a unified interface for both planning and Azure operations
    """
    
    SYSTEM_PROMPT = """You are a planning agent that helps users with Azure operations and general tasks.

Your capabilities:
1. Analyze user queries to determine if they require Azure operations
2. Plan the approach for complex tasks
3. Delegate Azure-specific operations to the Azure MCP agent
4. Provide helpful explanations and guidance

When a user asks about Azure resources, services, or operations:
- Use the azure_mcp_agent tool to interact with Azure
- Provide clear explanations of what you're doing
- Handle errors gracefully and suggest alternatives

For general questions or non-Azure tasks:
- Provide helpful responses directly
- Suggest relevant Azure services when appropriate

Always be helpful, clear, and professional in your responses."""

    def __init__(self, base_url: str = "http://localhost:10001"):
        """
        Initialize the Planner Agent.
        
        Args:
            base_url: Base URL for the A2A server
        """
        self.base_url = base_url
        self.llm = None
        self.agent = None
        self._initialized = False
    
    async def _initialize(self):
        """Initialize the LLM and agent."""
        if self._initialized:
            return
            
        # Initialize Azure OpenAI LLM
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default"
        )
        
        self.llm = AzureChatOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
            api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            temperature=0,
            azure_ad_token=SecretStr(token_provider())
        )
        
        # Create the React agent
        self.agent = create_react_agent(
            self.llm,
            tools=[azure_mcp_agent],
            checkpointer=memory,
            prompt=self.SYSTEM_PROMPT,
            response_format=PlannerResponse,
        )
        
        self._initialized = True
    
    async def invoke(self, query: str, context_id: str = "default") -> Dict[str, Any]:
        """
        Invoke the planner agent with a query.
        
        Args:
            query: The user query
            context_id: Conversation context identifier
            
        Returns:
            Dict containing the response and status
        """
        await self._initialize()
        
        if not self.agent:
            raise RuntimeError("Agent not initialized")
        
        inputs = {'messages': [('user', query)]}
        config = RunnableConfig({'configurable': {'thread_id': context_id}})
        
        try:
            result = await self.agent.ainvoke(inputs, config)
            return self._format_response(result)
        except (ValueError, RuntimeError) as e:
            logger.error("Error in planner agent: %s", e)
            return {
                'status': 'error',
                'message': f"Error processing request: {str(e)}",
                'requires_azure_operation': False
            }
        except httpx.HTTPError as e:
            logger.error("HTTP error in planner agent: %s", e)
            return {
                'status': 'error',
                'message': f"Network error: {str(e)}",
                'requires_azure_operation': False
            }
    
    async def stream(self, query: str, context_id: str = "default") -> AsyncIterable[Dict[str, Any]]:
        """
        Stream responses from the planner agent.
        
        Args:
            query: The user query
            context_id: Conversation context identifier
            
        Yields:
            Dict containing streaming response chunks
        """
        await self._initialize()
        
        if not self.agent:
            raise RuntimeError("Agent not initialized")
        
        inputs = {'messages': [('user', query)]}
        config = RunnableConfig({'configurable': {'thread_id': context_id}})
        
        try:
            async for item in self.agent.astream(inputs, config, stream_mode='values'):
                if 'messages' in item and item['messages']:
                    message = item['messages'][-1]
                    
                    if isinstance(message, AIMessage):
                        if message.tool_calls:
                            yield {
                                'status': 'delegating',
                                'message': 'Delegating to Azure MCP agent...',
                                'requires_azure_operation': True
                            }
                        else:
                            content = message.content if hasattr(message, 'content') else str(message)
                            yield {
                                'status': 'planning',
                                'message': content,
                                'requires_azure_operation': False
                            }
            
            # Get final response
            final_result = await self.agent.ainvoke(inputs, config)
            yield self._format_response(final_result)
            
        except (ValueError, RuntimeError) as e:
            logger.error("Error in planner agent stream: %s", e)
            yield {
                'status': 'error',
                'message': f"Error processing request: {str(e)}",
                'requires_azure_operation': False
            }
        except httpx.HTTPError as e:
            logger.error("HTTP error in planner agent stream: %s", e)
            yield {
                'status': 'error',
                'message': f"Network error: {str(e)}",
                'requires_azure_operation': False
            }
    
    def _format_response(self, result) -> Dict[str, Any]:
        """Format the agent response."""
        if hasattr(result, 'structured_response') and result.structured_response:
            response = result.structured_response
            return {
                'status': response.status,
                'message': response.message,
                'requires_azure_operation': response.requires_azure_operation,
                'azure_query': response.azure_query
            }
        
        # Fallback formatting
        content = result.get('messages', [{}])[-1].get('content', 'No response available')
        return {
            'status': 'completed',
            'message': content,
            'requires_azure_operation': False
        }


async def main():
    """Demo function to test the Planner Agent."""
    logger.info("=" * 60)
    logger.info("🧠 Planner Agent Demo")
    logger.info("=" * 60)
    
    agent = PlannerAgent()
    
    # Test queries
    test_queries = [
        "List all resource groups in my subscription",
        "What is the weather like today?",
        "Create a new storage account in East US",
        "How do I deploy a web app to Azure?",
        "What is 2 + 2?"
    ]
    
    for query in test_queries:
        logger.info("\n📝 Query: %s", query)
        logger.info("-" * 40)
        
        try:
            # Test non-streaming
            response = await agent.invoke(query)
            logger.info("Response: %s", response)
            
            # Test streaming
            # logger.info("Streaming response:")
            # async for chunk in agent.stream(query):
            #     logger.info("  %s", chunk)
                
        except (ValueError, RuntimeError, httpx.HTTPError) as e:
            logger.error("Error: %s", e)

    logger.info("\n✅ Demo completed")


if __name__ == "__main__":
    asyncio.run(main()) 