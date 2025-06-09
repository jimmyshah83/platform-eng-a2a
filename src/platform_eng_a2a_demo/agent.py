from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

from pydantic import BaseModel

from typing import Literal

from dotenv import load_dotenv
import os
load_dotenv()

memory = InMemorySaver()

class PlannerAgentResponseFormat(BaseModel):
    """Respond to the user in this format."""

    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str

class PlannerAgent:
	"""A class representing a planner agent that can plan tasks."""

	SYSTEM_INSTRUCTION = (
		"""
			You are an expert Azure platform engineer. \
			Your job is to create detailed infrastructure provisioning steps for Azure resources. \
			For each request, provide a step-by-step plan to deploy the required infrastructure. \
			Include specific resource types, configurations, and dependencies.
		""" 
	)

	def __init__(
        self,
        azure_endpoint: str = os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key: str = os.environ["AZURE_OPENAI_API_KEY"],
        api_version: str = "2024-12-01-preview",
        deployment_name: str = os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        temperature: float = 0.0,
     ):
		"""
		Initialize the PlannerAgent with Azure OpenAI configuration.

		Args:
			azure_endpoint: Azure OpenAI endpoint URL
			api_key: Azure OpenAI API key (use environment variable for security)
			api_version: Azure OpenAI API version
			deployment_name: Name of the deployed model
			temperature: Sampling temperature for response generation
		"""
  
		self.llm = AzureChatOpenAI(
			azure_endpoint=azure_endpoint,
            azure_api_key=api_key,
			azure_deployment=deployment_name,
			openai_api_version=api_version,
			temperature=temperature,
		)

		self.planner_agent = create_react_agent(
			self.llm,
			checkpointer=memory,
			prompt=self.SYSTEM_INSTRUCTION,
            response_format=PlannerAgentResponseFormat,    
		)

	def invoke(self, query, context_id) -> str:
		"""
		Invoke the planner agent to create an infrastructure provisioning plan.
		
		Args:
			query: The user's infrastructure request
			context_id: Optional context information to include in the planning
			
		Returns:
			A detailed infrastructure provisioning plan
			
		Raises:
			ValueError: If query is empty or None
			RuntimeError: If the LLM invocation fails
		"""
		if not query or not query.strip():
			raise ValueError("User request cannot be empty")
		
		config = {'configurable': {'thread_id': context_id}}
		self.planner_agent.invoke({'messages': [('user', query)]}, config)
		return self.get_agent_response(config)

	def get_agent_response(self, config):
		current_state = self.agent.get_state(config)
		structured_response = current_state.values.get('structured_response')
		if structured_response and isinstance(
			structured_response, PlannerAgentResponseFormat
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

	SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']