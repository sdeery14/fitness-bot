"""Test meal_phase_agent runner directly."""

import asyncio
from evaluations.agent_runners import run_meal_phase_agent

# Test inputs from the dataset
test_inputs = {
    "meal_plan_description": "Mediterranean-style nutrition plan for muscle building",
    "phase_number": 1,
    "phase_name": "Foundation Phase",
    "dietary_restrictions": ["No dairy", "Pescatarian"],
    "meal_frequency": 4
}

async def test_runner():
    """Test the meal phase agent runner."""
    print("Testing meal_phase_agent runner...")
    print(f"Inputs: {test_inputs}\n")
    
    try:
        result = await run_meal_phase_agent(**test_inputs)
        print("Success! Result keys:", list(result.keys()))
        print("\nSample output:")
        print(f"  Calories: {result.get('daily_calorie_target', 'N/A')}")
        print(f"  Sample days: {len(result.get('sample_days', []))}")
        print(f"  Has grocery list: {'grocery_list' in result}")
        return result
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_runner())
    if result:
        print("\n✅ Runner test passed!")
    else:
        print("\n❌ Runner test failed!")
