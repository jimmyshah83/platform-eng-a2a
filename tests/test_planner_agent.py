import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from pydantic import ValidationError

from src.platform_eng_a2a_demo.planner_agent import PlannerAgent, PlannerAgentResponseFormat


@pytest.mark.unit
class TestPlannerAgentResponseFormat:
    """Test cases for PlannerAgentResponseFormat model."""
    
    def test_valid_response_format_input_required(self):
        """Test creating a valid response format with input_required status."""
        response = PlannerAgentResponseFormat(
            status='input_required',
            message='Please provide more details'
        )
        assert response.status == 'input_required'
        assert response.message == 'Please provide more details'
    
    def test_valid_response_format_completed(self):
        """Test creating a valid response format with completed status."""
        response = PlannerAgentResponseFormat(
            status='completed',
            message='Infrastructure plan created successfully'
        )
        assert response.status == 'completed'
        assert response.message == 'Infrastructure plan created successfully'
    
    def test_valid_response_format_error(self):
        """Test creating a valid response format with error status."""
        response = PlannerAgentResponseFormat(
            status='error',
            message='Failed to process request'
        )
        assert response.status == 'error'
        assert response.message == 'Failed to process request'
    
    def test_default_status(self):
        """Test that default status is input_required."""
        response = PlannerAgentResponseFormat(message='Test message')
        assert response.status == 'input_required'
    
    def test_invalid_status(self):
        """Test that invalid status raises validation error."""
        with pytest.raises(ValidationError):
            PlannerAgentResponseFormat(
                status='invalid_status',
                message='Test message'
            )
    
    def test_missing_message(self):
        """Test that missing message raises validation error."""
        with pytest.raises(ValidationError):
            PlannerAgentResponseFormat(status='completed')


@pytest.mark.unit
class TestPlannerAgent:
    """Test cases for PlannerAgent class."""
    
    @pytest.fixture
    def mock_azure_chat_openai(self):
        """Mock AzureChatOpenAI."""
        with patch('src.platform_eng_a2a_demo.planner_agent.AzureChatOpenAI') as mock:
            yield mock
    
    @pytest.fixture
    def mock_create_react_agent(self):
        """Mock create_react_agent."""
        with patch('src.platform_eng_a2a_demo.planner_agent.create_react_agent') as mock:
            yield mock
    
    @pytest.fixture
    def planner_agent(self, mock_env_vars, mock_azure_chat_openai, mock_create_react_agent):
        """Create a PlannerAgent instance for testing."""
        mock_llm = Mock()
        mock_azure_chat_openai.return_value = mock_llm
        
        mock_agent = Mock()
        mock_create_react_agent.return_value = mock_agent
        
        agent = PlannerAgent()
        return agent
    
    def test_init_with_default_params(self, mock_env_vars, mock_azure_chat_openai, mock_create_react_agent):
        """Test PlannerAgent initialization with default parameters."""
        mock_llm = Mock()
        mock_azure_chat_openai.return_value = mock_llm
            
        mock_agent = Mock()
        mock_create_react_agent.return_value = mock_agent
        
        agent = PlannerAgent()
        
        # Verify AzureChatOpenAI was called with correct default parameters
        mock_azure_chat_openai.assert_called_once_with(
            azure_endpoint='https://test.openai.azure.com/',
            azure_api_key='test-api-key-12345',
            azure_deployment='test-deployment-name',
            openai_api_version='2024-12-01-preview',
            temperature=0.0
        )
        
        # Verify create_react_agent was called with correct parameters
        mock_create_react_agent.assert_called_once()
        args, kwargs = mock_create_react_agent.call_args
        assert args[0] == mock_llm
        assert 'checkpointer' in kwargs
        assert 'prompt' in kwargs
        assert 'response_format' in kwargs
        assert kwargs['response_format'] == PlannerAgentResponseFormat
    
    def test_init_with_custom_params(self, mock_azure_chat_openai, mock_create_react_agent):
        """Test PlannerAgent initialization with custom parameters."""
        mock_llm = Mock()
        mock_azure_chat_openai.return_value = mock_llm
        
        mock_agent = Mock()
        mock_create_react_agent.return_value = mock_agent
        
        custom_params = {
            'azure_endpoint': 'https://custom.openai.azure.com/',
            'api_key': 'custom-api-key',
            'api_version': '2024-01-01',
            'deployment_name': 'custom-deployment',
            'temperature': 0.5
        }
        
        agent = PlannerAgent(**custom_params)
        
        mock_azure_chat_openai.assert_called_once_with(
            azure_endpoint='https://custom.openai.azure.com/',
            azure_api_key='custom-api-key',
            azure_deployment='custom-deployment',
            openai_api_version='2024-01-01',
            temperature=0.5
        )
    
    def test_invoke_valid_query(self, planner_agent):
        """Test invoke method with valid query."""
        # Setup mocks
        mock_response = {
            'is_task_complete': True,
            'require_user_input': False,
            'content': 'Infrastructure plan created'
        }
        
        planner_agent.get_agent_response = Mock(return_value=mock_response)
        
        query = "Create an Azure App Service with PostgreSQL database"
        context_id = "test-context-123"
        
        result = planner_agent.invoke(query, context_id)
        
        # Verify agent was invoked with correct parameters
        planner_agent.planner_agent.invoke.assert_called_once()
        args, kwargs = planner_agent.planner_agent.invoke.call_args
        
        expected_messages = [('user', query)]
        assert args[0]['messages'] == expected_messages
        
        expected_config = {'configurable': {'thread_id': context_id}}
        assert args[1] == expected_config
        
        # Verify get_agent_response was called with config
        planner_agent.get_agent_response.assert_called_once_with(expected_config)
        
        assert result == mock_response
    
    def test_invoke_empty_query(self, planner_agent):
        """Test invoke method with empty query raises ValueError."""
        with pytest.raises(ValueError, match="User request cannot be empty"):
            planner_agent.invoke("", "test-context")
    
    def test_invoke_none_query(self, planner_agent):
        """Test invoke method with None query raises ValueError."""
        with pytest.raises(ValueError, match="User request cannot be empty"):
            planner_agent.invoke(None, "test-context")
    
    def test_invoke_whitespace_query(self, planner_agent):
        """Test invoke method with whitespace-only query raises ValueError."""
        with pytest.raises(ValueError, match="User request cannot be empty"):
            planner_agent.invoke("   \n\t  ", "test-context")
    
    def test_get_agent_response_input_required(self, planner_agent):
        """Test get_agent_response with input_required status."""
        mock_response = PlannerAgentResponseFormat(
            status='input_required',
            message='Please provide more details about the database requirements'
        )
        
        mock_state = Mock()
        mock_state.values = {'structured_response': mock_response}
        planner_agent.planner_agent.get_state.return_value = mock_state
        
        config = {'configurable': {'thread_id': 'test-context'}}
        result = planner_agent.get_agent_response(config)
        
        expected = {
            'is_task_complete': False,
            'require_user_input': True,
            'content': 'Please provide more details about the database requirements'
        }
        
        assert result == expected
    
    def test_get_agent_response_completed(self, planner_agent):
        """Test get_agent_response with completed status."""
        mock_response = PlannerAgentResponseFormat(
            status='completed',
            message='Infrastructure plan created successfully'
        )
        
        mock_state = Mock()
        mock_state.values = {'structured_response': mock_response}
        planner_agent.planner_agent.get_state.return_value = mock_state
        
        config = {'configurable': {'thread_id': 'test-context'}}
        result = planner_agent.get_agent_response(config)
        
        expected = {
            'is_task_complete': True,
            'require_user_input': False,
            'content': 'Infrastructure plan created successfully'
        }
        
        assert result == expected
    
    def test_get_agent_response_error(self, planner_agent):
        """Test get_agent_response with error status."""
        mock_response = PlannerAgentResponseFormat(
            status='error',
            message='Failed to generate infrastructure plan'
        )
        
        mock_state = Mock()
        mock_state.values = {'structured_response': mock_response}
        planner_agent.planner_agent.get_state.return_value = mock_state
        
        config = {'configurable': {'thread_id': 'test-context'}}
        result = planner_agent.get_agent_response(config)
        
        expected = {
            'is_task_complete': False,
            'require_user_input': True,
            'content': 'Failed to generate infrastructure plan'
        }
        
        assert result == expected
    
    def test_get_agent_response_no_structured_response(self, planner_agent):
        """Test get_agent_response when no structured_response is available."""
        mock_state = Mock()
        mock_state.values = {'structured_response': None}
        planner_agent.planner_agent.get_state.return_value = mock_state
        
        config = {'configurable': {'thread_id': 'test-context'}}
        result = planner_agent.get_agent_response(config)
        
        expected = {
            'is_task_complete': False,
            'require_user_input': True,
            'content': 'We are unable to process your request at the moment. Please try again.'
        }
        
        assert result == expected
    
    def test_get_agent_response_invalid_structured_response(self, planner_agent):
        """Test get_agent_response when structured_response is not the expected type."""
        mock_state = Mock()
        mock_state.values = {'structured_response': "invalid response"}
        planner_agent.planner_agent.get_state.return_value = mock_state
        
        config = {'configurable': {'thread_id': 'test-context'}}
        result = planner_agent.get_agent_response(config)
        
        expected = {
            'is_task_complete': False,
            'require_user_input': True,
            'content': 'We are unable to process your request at the moment. Please try again.'
        }
        
        assert result == expected
    
    def test_get_agent_response_empty_values(self, planner_agent):
        """Test get_agent_response when state values is empty."""
        mock_state = Mock()
        mock_state.values = {}
        planner_agent.planner_agent.get_state.return_value = mock_state
        
        config = {'configurable': {'thread_id': 'test-context'}}
        result = planner_agent.get_agent_response(config)
        
        expected = {
            'is_task_complete': False,
            'require_user_input': True,
            'content': 'We are unable to process your request at the moment. Please try again.'
        }
        
        assert result == expected
    
    def test_system_instruction_content(self):
        """Test that the system instruction contains expected content."""
        instruction = PlannerAgent.SYSTEM_INSTRUCTION
        
        assert "Azure platform engineer" in instruction
        assert "infrastructure provisioning" in instruction
        assert "step-by-step plan" in instruction
        assert "resource types" in instruction
        assert "configurations" in instruction
        assert "dependencies" in instruction
    
    def test_supported_content_types(self):
        """Test that supported content types are correctly defined."""
        supported_types = PlannerAgent.SUPPORTED_CONTENT_TYPES
        
        assert 'text' in supported_types
        assert 'text/plain' in supported_types
        assert len(supported_types) == 2


@pytest.mark.integration
class TestPlannerAgentIntegration:
    """Integration tests for PlannerAgent that test the full flow."""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing."""
        with patch.dict(os.environ, {
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
            'AZURE_OPENAI_API_KEY': 'test-api-key',
            'AZURE_OPENAI_DEPLOYMENT_NAME': 'test-deployment'
        }):
            yield
    
    @patch('src.platform_eng_a2a_demo.planner_agent.create_react_agent')
    @patch('src.platform_eng_a2a_demo.planner_agent.AzureChatOpenAI')
    def test_full_workflow_completed_task(self, mock_azure_chat_openai, mock_create_react_agent, mock_env_vars):
        """Test a complete workflow where the task is completed successfully."""
        # Setup mocks
        mock_llm = Mock()
        mock_azure_chat_openai.return_value = mock_llm
        
        mock_agent = Mock()
        mock_create_react_agent.return_value = mock_agent
        
        # Mock the response format
        mock_response = PlannerAgentResponseFormat(
            status='completed',
            message='Here is your Azure infrastructure plan:\n1. Create Resource Group\n2. Deploy App Service\n3. Configure Database'
        )
        
        mock_state = Mock()
        mock_state.values = {'structured_response': mock_response}
        mock_agent.get_state.return_value = mock_state
        
        # Create agent and invoke
        agent = PlannerAgent()
        query = "I need to deploy a web application with a database on Azure"
        context_id = "integration-test-123"
        
        result = agent.invoke(query, context_id)
        
        # Verify the full workflow
        assert result['is_task_complete'] is True
        assert result['require_user_input'] is False
        assert 'Azure infrastructure plan' in result['content']
        assert 'Resource Group' in result['content']
        assert 'App Service' in result['content']
        assert 'Database' in result['content']
    
    @patch('src.platform_eng_a2a_demo.planner_agent.create_react_agent')
    @patch('src.platform_eng_a2a_demo.planner_agent.AzureChatOpenAI')
    def test_full_workflow_input_required(self, mock_azure_chat_openai, mock_create_react_agent, mock_env_vars):
        """Test a workflow where additional input is required."""
        # Setup mocks
        mock_llm = Mock()
        mock_azure_chat_openai.return_value = mock_llm
        
        mock_agent = Mock()
        mock_create_react_agent.return_value = mock_agent
        
        # Mock the response format
        mock_response = PlannerAgentResponseFormat(
            status='input_required',
            message='I need more information about your requirements. What type of database do you prefer? (PostgreSQL, MySQL, or SQL Server)'
        )
        
        mock_state = Mock()
        mock_state.values = {'structured_response': mock_response}
        mock_agent.get_state.return_value = mock_state
        
        # Create agent and invoke
        agent = PlannerAgent()
        query = "Deploy a web application"
        context_id = "integration-test-456"
        
        result = agent.invoke(query, context_id)
        
        # Verify the workflow requires more input
        assert result['is_task_complete'] is False
        assert result['require_user_input'] is True
        assert 'database do you prefer' in result['content']
        assert 'PostgreSQL, MySQL, or SQL Server' in result['content']


if __name__ == '__main__':
    pytest.main([__file__])
