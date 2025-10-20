"""Planner Demo - Main module for testing the Planner Agent."""

import asyncio
import json
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
    print(f"\n{'#'*60}")
    print(f"# PLANNER DEMO STARTING")
    print(f"{'#'*60}\n")
    
    try:
        # Create and run the planner agent
        print("[Main] Creating PlannerAgent instance...")
        planner = PlannerAgent()
        
        # Run the async function
        print(f"[Main] Running planner.invoke() with query: '{query}'")
        result = asyncio.run(planner.invoke(query))
        
        print(f"\n{'#'*60}")
        print(f"# RESULT")
        print(f"{'#'*60}")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"{'#'*60}\n")
        
    except (ValueError, RuntimeError, ImportError) as e:
        logger.error("An error occurred: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()  # Click will handle the query argument via command line or prompt 