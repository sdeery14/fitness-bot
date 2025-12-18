"""Quick test to verify TDEE calculation integration works correctly."""

from src.ai.schemas import UserBiometrics
from src.utils.calorie_calculator import calculate_tdee


def test_tdee_calculation():
    """Test TDEE calculation with sample biometrics."""
    
    # Test case 1: 30-year-old moderately active male
    male_biometrics = UserBiometrics(
        age=30,
        biological_sex="male",
        height_cm=180.0,
        weight_kg=80.0,
        activity_level="moderately_active"
    )
    male_tdee = calculate_tdee(male_biometrics)
    print(f"Test 1 - Male (30yo, 180cm, 80kg, moderately_active):")
    print(f"  TDEE: {int(male_tdee)} cal/day")
    assert 2400 <= male_tdee <= 2800, f"Expected ~2600 cal, got {male_tdee}"
    print("  ✓ Pass\n")
    
    # Test case 2: 25-year-old lightly active female
    female_biometrics = UserBiometrics(
        age=25,
        biological_sex="female",
        height_cm=165.0,
        weight_kg=60.0,
        activity_level="lightly_active"
    )
    female_tdee = calculate_tdee(female_biometrics)
    print(f"Test 2 - Female (25yo, 165cm, 60kg, lightly_active):")
    print(f"  TDEE: {int(female_tdee)} cal/day")
    assert 1700 <= female_tdee <= 2100, f"Expected ~1900 cal, got {female_tdee}"
    print("  ✓ Pass\n")
    
    # Test case 3: 40-year-old very active male (athlete)
    athlete_biometrics = UserBiometrics(
        age=40,
        biological_sex="male",
        height_cm=185.0,
        weight_kg=90.0,
        activity_level="very_active"
    )
    athlete_tdee = calculate_tdee(athlete_biometrics)
    print(f"Test 3 - Athlete (40yo, 185cm, 90kg, very_active):")
    print(f"  TDEE: {int(athlete_tdee)} cal/day")
    assert 3000 <= athlete_tdee <= 3600, f"Expected ~3300 cal, got {athlete_tdee}"
    print("  ✓ Pass\n")
    
    print("✅ All TDEE calculation tests passed!")
    return True


if __name__ == "__main__":
    test_tdee_calculation()
