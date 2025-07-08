#!/usr/bin/env python3
"""
Debug script to diagnose Azure MCP setup issues.
"""

import os
import logging
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment_variables():
    """Check if required environment variables are set."""
    logger.info("Checking environment variables...")
    
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        "AZURE_OPENAI_API_VERSION"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            logger.info(f"✅ {var}: {value[:20]}..." if len(value) > 20 else f"✅ {var}: {value}")
        else:
            logger.error(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    return len(missing_vars) == 0

def check_azure_cli():
    """Check if Azure CLI is authenticated."""
    logger.info("Checking Azure CLI authentication...")
    
    try:
        import subprocess
        result = subprocess.run(
            ["az", "account", "show"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode == 0:
            logger.info("✅ Azure CLI is authenticated")
            return True
        else:
            logger.error(f"❌ Azure CLI authentication failed: {result.stderr}")
            return False
    except FileNotFoundError:
        logger.error("❌ Azure CLI not found. Please install Azure CLI.")
        return False
    except subprocess.TimeoutExpired:
        logger.error("❌ Azure CLI command timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Error checking Azure CLI: {e}")
        return False

def check_npm():
    """Check if npm is available."""
    logger.info("Checking npm availability...")
    
    try:
        import subprocess
        result = subprocess.run(
            ["npm", "--version"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode == 0:
            logger.info(f"✅ npm is available: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"❌ npm check failed: {result.stderr}")
            return False
    except FileNotFoundError:
        logger.error("❌ npm not found. Please install Node.js and npm.")
        return False
    except Exception as e:
        logger.error(f"❌ Error checking npm: {e}")
        return False

async def test_azure_mcp_agent():
    """Test Azure MCP agent initialization."""
    logger.info("Testing Azure MCP agent initialization...")
    
    try:
        from .azure_agent import AzureMCPAgent
        
        agent = AzureMCPAgent()
        logger.info("✅ Azure MCP agent initialized successfully")
        
        # Test tool retrieval
        logger.info("Testing tool retrieval...")
        tools = await agent.mcp_client.get_tools()
        logger.info(f"✅ Retrieved {len(tools)} tools from Azure MCP server")
        
        for tool in tools:
            logger.info(f"  - {tool.name}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Azure MCP agent test failed: {e}")
        return False

def main():
    """Run all diagnostic checks."""
    logger.info("🔍 Starting Azure MCP setup diagnostics...")
    logger.info("=" * 50)
    
    # Check environment variables
    env_ok = check_environment_variables()
    logger.info("")
    
    # Check Azure CLI
    azure_cli_ok = check_azure_cli()
    logger.info("")
    
    # Check npm
    npm_ok = check_npm()
    logger.info("")
    
    # Test Azure MCP agent
    logger.info("Testing Azure MCP agent (this may take a moment)...")
    try:
        agent_ok = asyncio.run(test_azure_mcp_agent())
    except Exception as e:
        logger.error(f"❌ Failed to test Azure MCP agent: {e}")
        agent_ok = False
    logger.info("")
    
    # Summary
    logger.info("=" * 50)
    logger.info("📋 DIAGNOSTIC SUMMARY:")
    logger.info(f"Environment Variables: {'✅ OK' if env_ok else '❌ FAILED'}")
    logger.info(f"Azure CLI: {'✅ OK' if azure_cli_ok else '❌ FAILED'}")
    logger.info(f"npm: {'✅ OK' if npm_ok else '❌ FAILED'}")
    logger.info(f"Azure MCP Agent: {'✅ OK' if agent_ok else '❌ FAILED'}")
    
    if all([env_ok, azure_cli_ok, npm_ok, agent_ok]):
        logger.info("🎉 All checks passed! Your Azure MCP setup should work correctly.")
    else:
        logger.info("⚠️  Some checks failed. Please fix the issues above before running the Azure MCP agent.")
        
        if not env_ok:
            logger.info("💡 To fix environment variables, create a .env file with:")
            logger.info("   AZURE_OPENAI_ENDPOINT=your_endpoint")
            logger.info("   AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment")
            logger.info("   AZURE_OPENAI_API_VERSION=2024-02-15-preview")
            
        if not azure_cli_ok:
            logger.info("💡 To fix Azure CLI, run: az login")
            
        if not npm_ok:
            logger.info("💡 To fix npm, install Node.js from: https://nodejs.org/")

if __name__ == "__main__":
    main() 