"""Planner Demo - Main module for testing the Planner Agent."""

import asyncio
import logging
import sys

import click

from .planner_agent import PlannerAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--query", "query", prompt="Enter your query", help="The query to process")
def main(query):
    """Test the Planner Agent with a user query."""
    try:
        # Create and run the planner agent
        planner = PlannerAgent()
        
        # Run the async function
        result = asyncio.run(planner.invoke(query))
        
        print(f"\nResult: {result}")
        
    except (ValueError, RuntimeError, ImportError) as e:
        logger.error("An error occurred: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()  # Click will handle the query argument via command line or prompt 