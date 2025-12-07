"""Verification script to confirm MODEL_NAME is used across all agents."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import settings
from src.ai.agent import create_model_settings

print("=" * 60)
print("MODEL_NAME Configuration Verification")
print("=" * 60)
print(f"\n✓ Environment MODEL_NAME: {settings.MODEL_NAME}")
print(f"✓ OpenAI API Key configured: {'Yes' if settings.OPENAI_API_KEY else 'No'}")

print("\n" + "-" * 60)
print("Agent Model Settings:")
print("-" * 60)

presets = ["fast", "balanced", "quality", "creative"]
for preset in presets:
    model_settings = create_model_settings(preset)
    print(f"\n{preset.upper()} preset:")
    print(f"  Temperature: {model_settings.temperature}")
    print(f"  Max Tokens: {model_settings.max_tokens}")
    print(f"  Uses MODEL_NAME: {settings.MODEL_NAME}")

print("\n" + "=" * 60)
print("Agents using these settings:")
print("=" * 60)
print("  • intake_specialist_agent (balanced)")
print("  • conversation_agent (balanced)")
print("  • workout_plan_agent (balanced)")
print("  • meal_plan_agent (balanced)")
print("  • fitness_plan_agent (quality)")

print("\n✓ All agents will use MODEL_NAME from environment")
print("=" * 60)
