# TDEE Integration Implementation Summary

**Date:** 2025-12-18  
**Status:** ✅ COMPLETE  
**Branch:** 001-ai-fitness-planner

## Overview

Successfully integrated TDEE (Total Daily Energy Expenditure) calculation into the `build_fitness_plan` function as part of the percentage-based calorie architecture refactoring. This moves calorie calculations from LLMs (which are unreliable at math) to code-based calculations using user biometrics.

## Changes Made

### 1. Updated `plan_tools.py`

**Import Addition:**
```python
from src.utils.calorie_calculator import calculate_tdee
```

**`build_fitness_plan` Function:**
- Added TDEE calculation at start of function:
  ```python
  # 1. Calculate TDEE from user biometrics
  tdee = calculate_tdee(requirements.biometrics)
  print(f"Calculated TDEE: {int(tdee)} calories/day ...")
  ```
- Pass TDEE to `_build_phase_with_agents` for each phase
- Updated step numbering in comments (1-6 instead of 1-5)

**`_build_phase_with_agents` Function:**
- Added `tdee: float` parameter to function signature
- Updated docstring to document TDEE parameter
- Enhanced meal phase prompt to include:
  - User biometric details (age, sex, height, weight, activity level)
  - **Calculated TDEE with context explanation**
  - Clear guidance that TDEE is the maintenance calorie baseline

**Example Prompt Addition:**
```
User Biometrics & TDEE:
- Age: 30 years
- Sex: male
- Height: 180 cm
- Weight: 80 kg
- Activity Level: moderately_active
- **Calculated TDEE (Total Daily Energy Expenditure): 2759 calories/day**
  (This is the user's maintenance calories based on their biometrics and activity level.)
```

## Testing

Created `test_tdee_integration.py` with three test cases:

| Test Case | Description | TDEE Result | Status |
|-----------|-------------|-------------|--------|
| 1 | 30yo male, 180cm, 80kg, moderately_active | 2759 cal/day | ✅ Pass |
| 2 | 25yo female, 165cm, 60kg, lightly_active | 1850 cal/day | ✅ Pass |
| 3 | 40yo male, 185cm, 90kg, very_active | 3211 cal/day | ✅ Pass |

All tests passed successfully, confirming calculations are accurate.

## How It Works

### Flow:
1. **User provides biometrics** via `intake_specialist_agent` (age, sex, height, weight, activity level)
2. **TDEE calculated** at start of `build_fitness_plan` using Mifflin-St Jeor equation
3. **TDEE passed to each phase** via `_build_phase_with_agents`
4. **Meal phase agent receives TDEE** in prompt as context for generating `calorie_goal_modifier`
5. **Agent outputs percentages/modifiers** (0.7-1.3) instead of absolute calories
6. **Code expands percentages** to actual values using TDEE (to be implemented in database layer)

### Example Calculation:
- **User:** 30yo male, 80kg, moderately active
- **TDEE:** 2759 cal/day (maintenance)
- **Agent decides:** `calorie_goal_modifier: 1.15` (15% surplus for bulking)
- **Result:** 2759 × 1.15 = **3173 cal/day** target
- **For training day:** 3173 × 1.0 = 3173 cal
- **For rest day:** 3173 × 0.9 = 2856 cal

## Benefits

### ✅ Accuracy
- LLMs no longer guess at calorie targets
- Precise TDEE from validated formulas
- Personalized to user's specific biometrics

### ✅ Consistency
- Same biometrics = same TDEE every time
- No more "2900 cal when expecting 3000-3400" errors
- Predictable, testable behavior

### ✅ Transparency
- Users see their TDEE calculation
- Agents understand the baseline they're modifying
- Clear separation: agents set strategy (modifiers), code does math

### ✅ Flexibility
- Easy to recalculate if user's weight changes
- Modifier approach scales to any TDEE
- Day-type modifiers (training/rest/refeed) apply consistently

## Next Steps

### Immediate (Required for End-to-End):
1. **Update evaluation datasets** - Change test expectations from absolute calories to percentages
2. **Database schema migration** - Add fields for calorie_goal_modifier and macro percentages
3. **Percentage expansion** - Add post-processing to expand percentages to actual calories for storage
4. **Re-run meal_phase evaluation** - Verify "poor" ratings become "excellent"

### Future Enhancements:
- Store TDEE history for weight change tracking
- Add TDEE recalculation triggers (e.g., every 4 weeks)
- Dashboard showing TDEE vs actual calorie intake
- Adaptive TDEE adjustment based on weight progress

## Related Files

- `src/ai/tools/plan_tools.py` - TDEE integration (THIS WORK)
- `src/utils/calorie_calculator.py` - TDEE calculation utility
- `src/ai/schemas.py` - Percentage-based schemas
- `src/ai/app_agents/intake_specialist_agent.py` - Biometric collection
- `src/ai/app_agents/meal_phase_agent.py` - Percentage-based meal generation
- `docs/calorie-calculation-architecture.md` - Architecture documentation

## Commit History

1. **Refactor meal planning to use percentages instead of absolute calories**
   - Updated schemas (MealItem, Meal, DailyMealPlan, PhaseMealDetails)
   - Added UserBiometrics schema
   - Created calorie_calculator.py utility

2. **Update agents for percentage-based calorie calculation system**
   - Modified intake_specialist_agent to collect biometrics
   - Modified meal_phase_agent to output percentages/modifiers

3. **Add biometrics field to FitnessPlanInput for TDEE calculation**
   - Updated FitnessPlanInput schema

4. **Integrate TDEE calculation into build_fitness_plan function** ← THIS COMMIT
   - Calculate TDEE from biometrics
   - Pass to phase agents
   - Include in meal phase prompt

## Testing Commands

```bash
# Verify TDEE integration
cd backend
uv run python test_tdee_integration.py

# Check for syntax errors
python -m py_compile src/ai/tools/plan_tools.py

# Run full test suite (when ready)
cd src
pytest tests/test_ai_agents.py -v
```

## Success Metrics

| Metric | Before | After | Status |
|--------|--------|-------|--------|
| TDEE calculation | ❌ None | ✅ Integrated | Complete |
| Agent receives TDEE | ❌ No | ✅ Yes, in prompt | Complete |
| Calorie accuracy | ❌ LLM guesses | ✅ Code calculates | In Progress |
| Test coverage | ❌ Manual only | ✅ Automated tests | Complete |

## Notes

- TDEE is calculated using the **Mifflin-St Jeor equation** (most accurate for general population)
- Activity multipliers range from 1.2 (sedentary) to 1.9 (extra active)
- Logging added to show calculated TDEE for debugging and user transparency
- Next critical step: Update database schema to store both strategies (percentages) and calculated values (actual calories)

---

**Author:** AI Assistant  
**Reviewer:** Pending  
**Architecture Doc:** `docs/calorie-calculation-architecture.md`
