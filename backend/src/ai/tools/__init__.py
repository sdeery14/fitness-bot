"""AI agent tools using OpenAI Agents SDK function_tool decorator.

This package contains tool functions that agents can use to:
- Query exercise database
- Search USDA nutritional data
- Generate and coordinate fitness plans
- Interact with plan storage

All tools are decorated with @function_tool for automatic schema generation.
"""

from . import plan_tools

__all__ = ["plan_tools"]

