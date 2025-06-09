"""
Shared pytest fixtures for the platform-eng-a2a-demo project.
"""

import pytest
import os
from unittest.mock import Mock, patch


@pytest.fixture
def mock_env_vars():
    """
    Mock environment variables commonly used in tests.
    
    This fixture provides a clean environment for testing Azure OpenAI configurations
    without requiring actual credentials.
    """
    env_vars = {
        'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_API_KEY': 'test-api-key-12345',
        'AZURE_OPENAI_DEPLOYMENT_NAME': 'test-deployment-name'
    }
    
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def sample_queries():
    """
    Provide sample queries for testing the planner agent.
    
    Returns:
        dict: A dictionary containing various types of sample queries
    """
    return {
        'simple': "Deploy a web application on Azure",
        'detailed': "Create an Azure App Service with PostgreSQL database, Redis cache, and Application Insights monitoring",
        'complex': "Design a multi-tier architecture with load balancer, web tier, API tier, database tier, and backup strategy",
        'invalid_empty': "",
        'invalid_whitespace': "   \n\t  ",
        'invalid_none': None
    }


@pytest.fixture
def sample_context_ids():
    """
    Provide sample context IDs for testing.
    
    Returns:
        list: A list of sample context IDs
    """
    return [
        "test-context-001",
        "user-session-abc123",
        "conversation-xyz789",
        "integration-test-456"
    ]


@pytest.fixture
def mock_planner_responses():
    """
    Provide mock responses for different planner agent scenarios.
    
    Returns:
        dict: A dictionary containing mock responses for various scenarios
    """
    return {
        'input_required': {
            'status': 'input_required',
            'message': 'I need more information about your requirements. What type of database do you prefer?'
        },
        'completed': {
            'status': 'completed',
            'message': 'Here is your Azure infrastructure plan:\n1. Create Resource Group\n2. Deploy App Service\n3. Configure Database'
        },
        'error': {
            'status': 'error',
            'message': 'Failed to generate infrastructure plan due to insufficient permissions'
        }
    }


@pytest.fixture
def mock_expected_responses():
    """
    Provide expected response formats for different agent states.
    
    Returns:
        dict: A dictionary containing expected response formats
    """
    return {
        'input_required': {
            'is_task_complete': False,
            'require_user_input': True,
            'content': 'I need more information about your requirements. What type of database do you prefer?'
        },
        'completed': {
            'is_task_complete': True,
            'require_user_input': False,
            'content': 'Here is your Azure infrastructure plan:\n1. Create Resource Group\n2. Deploy App Service\n3. Configure Database'
        },
        'error': {
            'is_task_complete': False,
            'require_user_input': True,
            'content': 'Failed to generate infrastructure plan due to insufficient permissions'
        },
        'fallback': {
            'is_task_complete': False,
            'require_user_input': True,
            'content': 'We are unable to process your request at the moment. Please try again.'
        }
    }


# Test markers for organizing tests
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
