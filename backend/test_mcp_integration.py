"""Test script to verify MCP query agent integration.

This script tests the query_agent's ability to connect to postgres-mcp
via stdio transport and execute basic queries.

Run this to verify:
1. postgres-mcp is installed (via uv tool install postgres-mcp)
2. The MCP server can spawn and communicate via stdio
3. Basic SQL queries work through the MCP server
"""
import asyncio
import os

from agents import Runner

# Set up environment
os.environ["DATABASE_URI"] = (
    "postgresql://fitness_user:fitness_pass_dev@localhost:5432/fitness_bot"
)

from src.ai.app_agents.query_agent import query_agent


async def test_query_agent():
    """Test basic query_agent functionality."""
    print("=" * 60)
    print("Testing MCP Query Agent Integration")
    print("=" * 60)

    # Test 1: List schemas
    print("\n[Test 1] Listing database schemas...")
    try:
        result = await Runner.run(
            starting_agent=query_agent,
            input="List all schemas in the database",
            session=None,
        )
        print(f"✓ Result: {result.final_output}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 2: Get exercises table structure
    print("\n[Test 2] Getting exercises table structure...")
    try:
        result = await Runner.run(
            starting_agent=query_agent,
            input="Get details about the exercises table in the public schema",
            session=None,
        )
        print(f"✓ Result: {result.final_output}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 3: Count exercises
    print("\n[Test 3] Counting exercises in database...")
    try:
        result = await Runner.run(
            starting_agent=query_agent,
            input="How many exercises are in the exercises table?",
            session=None,
        )
        print(f"✓ Result: {result.final_output}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 4: Query exercises by muscle group
    print("\n[Test 4] Finding chest exercises...")
    try:
        result = await Runner.run(
            starting_agent=query_agent,
            input="Find all exercises that target the chest muscles",
            session=None,
        )
        print(f"✓ Result: {result.final_output}")
    except Exception as e:
        print(f"✗ Error: {e}")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    print("\nPrerequisites:")
    print("1. PostgreSQL running on localhost:5432")
    print("2. Database 'fitness_bot' with user 'fitness_user'")
    print("3. postgres-mcp installed (uv tool install postgres-mcp)")
    print("4. Exercises table seeded with data")
    print()

    asyncio.run(test_query_agent())
