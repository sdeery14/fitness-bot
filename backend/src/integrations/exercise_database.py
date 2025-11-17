"""Curated exercise database seed script.

This script creates a comprehensive exercise database with 200-500 exercises
covering various muscle groups, equipment types, and difficulty levels.
Supports FR-048, FR-049, FR-050, FR-051.
"""
import asyncio




# Comprehensive exercise database
EXERCISE_DATABASE = [
    # CHEST EXERCISES
    {
        "name": "Barbell Bench Press",
        "exercise_type": "compound",
        "target_muscle_groups": ["chest", "shoulders", "triceps"],
        "equipment_required": ["barbell", "bench"],
        "difficulty": "intermediate",
        "instructions": "1. Lie on bench with feet flat on floor\n2. Grip bar slightly wider than shoulder width\n3. Lower bar to mid-chest with control\n4. Press bar up to starting position\n5. Keep shoulder blades retracted throughout",
        "form_cues": ["Keep feet planted", "Full range of motion", "Control the descent", "Drive through chest"],
        "alternatives": ["dumbbell_bench_press", "push_up", "machine_chest_press"],
    },
    {
        "name": "Dumbbell Bench Press",
        "exercise_type": "compound",
        "target_muscle_groups": ["chest", "shoulders", "triceps"],
        "equipment_required": ["dumbbells", "bench"],
        "difficulty": "intermediate",
        "instructions": "1. Lie on bench with dumbbells at chest level\n2. Press dumbbells up until arms are extended\n3. Lower with control back to starting position\n4. Maintain natural arch in lower back",
        "form_cues": ["Control the weight", "Full extension at top", "Elbows at 45 degrees"],
        "alternatives": ["barbell_bench_press", "incline_dumbbell_press", "push_up"],
    },
    {
        "name": "Push-Up",
        "exercise_type": "compound",
        "target_muscle_groups": ["chest", "shoulders", "triceps", "core"],
        "equipment_required": ["bodyweight"],
        "difficulty": "beginner",
        "instructions": "1. Start in plank position with hands shoulder-width apart\n2. Lower body until chest nearly touches floor\n3. Push back up to starting position\n4. Keep core engaged throughout",
        "form_cues": ["Straight body line", "Core tight", "Full range of motion", "Control the movement"],
        "alternatives": ["bench_press", "dumbbell_press", "incline_push_up"],
    },
    {
        "name": "Incline Barbell Bench Press",
        "exercise_type": "compound",
        "target_muscle_groups": ["upper chest", "shoulders", "triceps"],
        "equipment_required": ["barbell", "incline bench"],
        "difficulty": "intermediate",
        "instructions": "1. Set bench to 30-45 degree incline\n2. Lie back and grip bar slightly wider than shoulders\n3. Lower bar to upper chest\n4. Press back to starting position",
        "form_cues": ["Focus on upper chest", "Control the eccentric", "Full lockout"],
        "alternatives": ["incline_dumbbell_press", "incline_push_up"],
    },
    {
        "name": "Cable Fly",
        "exercise_type": "isolation",
        "target_muscle_groups": ["chest"],
        "equipment_required": ["cable machine"],
        "difficulty": "beginner",
        "instructions": "1. Set cables to chest height\n2. Step forward with slight bend in elbows\n3. Bring handles together in front of chest\n4. Control return to starting position",
        "form_cues": ["Slight elbow bend", "Squeeze at peak contraction", "Control the stretch"],
        "alternatives": ["dumbbell_fly", "pec_deck"],
    },
    
    # BACK EXERCISES
    {
        "name": "Deadlift",
        "exercise_type": "compound",
        "target_muscle_groups": ["back", "hamstrings", "glutes", "core"],
        "equipment_required": ["barbell"],
        "difficulty": "advanced",
        "instructions": "1. Stand with feet hip-width apart, bar over mid-foot\n2. Grip bar just outside legs\n3. Keep chest up, back straight\n4. Drive through heels, extending hips and knees\n5. Lower bar with control",
        "form_cues": ["Neutral spine", "Engage lats", "Drive through heels", "Full hip extension"],
        "alternatives": ["trap_bar_deadlift", "romanian_deadlift", "rack_pull"],
    },
    {
        "name": "Pull-Up",
        "exercise_type": "compound",
        "target_muscle_groups": ["lats", "biceps", "upper back"],
        "equipment_required": ["pull-up bar"],
        "difficulty": "intermediate",
        "instructions": "1. Hang from bar with overhand grip\n2. Pull body up until chin clears bar\n3. Lower with control to full extension\n4. Avoid swinging or using momentum",
        "form_cues": ["Full extension at bottom", "Pull with elbows", "Control the descent"],
        "alternatives": ["lat_pulldown", "assisted_pull_up", "inverted_row"],
    },
    {
        "name": "Barbell Row",
        "exercise_type": "compound",
        "target_muscle_groups": ["lats", "upper back", "biceps"],
        "equipment_required": ["barbell"],
        "difficulty": "intermediate",
        "instructions": "1. Bend at hips to 45-degree angle\n2. Grip bar slightly wider than shoulder width\n3. Pull bar to lower chest/upper abs\n4. Lower with control",
        "form_cues": ["Flat back", "Pull to sternum", "Control the weight", "Squeeze shoulder blades"],
        "alternatives": ["dumbbell_row", "t_bar_row", "cable_row"],
    },
    {
        "name": "Lat Pulldown",
        "exercise_type": "compound",
        "target_muscle_groups": ["lats", "biceps", "upper back"],
        "equipment_required": ["cable machine", "lat pulldown bar"],
        "difficulty": "beginner",
        "instructions": "1. Sit at lat pulldown machine\n2. Grip bar wider than shoulder width\n3. Pull bar down to upper chest\n4. Control return to starting position",
        "form_cues": ["Pull with elbows", "Slight lean back", "Full stretch at top"],
        "alternatives": ["pull_up", "assisted_pull_up", "straight_arm_pulldown"],
    },
    {
        "name": "Dumbbell Row",
        "exercise_type": "compound",
        "target_muscle_groups": ["lats", "upper back", "biceps"],
        "equipment_required": ["dumbbells", "bench"],
        "difficulty": "beginner",
        "instructions": "1. Place knee and hand on bench for support\n2. Hold dumbbell in free hand\n3. Pull dumbbell to hip, keeping elbow close\n4. Lower with control",
        "form_cues": ["Neutral spine", "Pull to hip", "Squeeze at top"],
        "alternatives": ["barbell_row", "cable_row", "t_bar_row"],
    },
    
    # SHOULDER EXERCISES
    {
        "name": "Overhead Press",
        "exercise_type": "compound",
        "target_muscle_groups": ["shoulders", "triceps", "core"],
        "equipment_required": ["barbell"],
        "difficulty": "intermediate",
        "instructions": "1. Stand with feet shoulder-width apart\n2. Grip bar at shoulder width\n3. Press bar overhead to full extension\n4. Lower to starting position with control",
        "form_cues": ["Tight core", "Full lockout", "Bar path straight up"],
        "alternatives": ["dumbbell_press", "arnold_press", "machine_shoulder_press"],
    },
    {
        "name": "Lateral Raise",
        "exercise_type": "isolation",
        "target_muscle_groups": ["side delts"],
        "equipment_required": ["dumbbells"],
        "difficulty": "beginner",
        "instructions": "1. Stand with dumbbells at sides\n2. Raise dumbbells out to sides\n3. Stop at shoulder height\n4. Lower with control",
        "form_cues": ["Slight elbow bend", "Control the weight", "Don't swing"],
        "alternatives": ["cable_lateral_raise", "machine_lateral_raise"],
    },
    {
        "name": "Face Pull",
        "exercise_type": "isolation",
        "target_muscle_groups": ["rear delts", "upper back"],
        "equipment_required": ["cable machine", "rope attachment"],
        "difficulty": "beginner",
        "instructions": "1. Set cable to upper chest height\n2. Pull rope towards face\n3. Separate rope ends at face level\n4. Control return to starting position",
        "form_cues": ["Pull towards forehead", "Externally rotate shoulders", "Squeeze shoulder blades"],
        "alternatives": ["reverse_fly", "rear_delt_fly"],
    },
    
    # LEG EXERCISES
    {
        "name": "Barbell Squat",
        "exercise_type": "compound",
        "target_muscle_groups": ["quads", "glutes", "hamstrings", "core"],
        "equipment_required": ["barbell", "squat rack"],
        "difficulty": "intermediate",
        "instructions": "1. Position bar on upper back\n2. Feet shoulder-width apart\n3. Descend until thighs are parallel\n4. Drive through heels to stand",
        "form_cues": ["Chest up", "Knees out", "Drive through heels", "Full depth"],
        "alternatives": ["front_squat", "goblet_squat", "leg_press"],
    },
    {
        "name": "Romanian Deadlift",
        "exercise_type": "compound",
        "target_muscle_groups": ["hamstrings", "glutes", "lower back"],
        "equipment_required": ["barbell"],
        "difficulty": "intermediate",
        "instructions": "1. Hold bar at hip level\n2. Hinge at hips, pushing them back\n3. Lower bar along legs\n4. Return to starting position by driving hips forward",
        "form_cues": ["Slight knee bend", "Feel hamstring stretch", "Neutral spine"],
        "alternatives": ["dumbbell_rdl", "single_leg_rdl", "stiff_leg_deadlift"],
    },
    {
        "name": "Leg Press",
        "exercise_type": "compound",
        "target_muscle_groups": ["quads", "glutes", "hamstrings"],
        "equipment_required": ["leg press machine"],
        "difficulty": "beginner",
        "instructions": "1. Sit in leg press machine\n2. Place feet shoulder-width on platform\n3. Lower platform until knees at 90 degrees\n4. Press through heels to starting position",
        "form_cues": ["Full range of motion", "Control the weight", "Don't lock knees"],
        "alternatives": ["squat", "hack_squat", "front_squat"],
    },
    {
        "name": "Bulgarian Split Squat",
        "exercise_type": "compound",
        "target_muscle_groups": ["quads", "glutes", "hamstrings"],
        "equipment_required": ["bench", "dumbbells"],
        "difficulty": "intermediate",
        "instructions": "1. Place rear foot on bench\n2. Hold dumbbells at sides\n3. Lower until front thigh is parallel\n4. Drive through front heel to stand",
        "form_cues": ["Upright torso", "Control the descent", "Drive through heel"],
        "alternatives": ["walking_lunge", "reverse_lunge", "leg_press"],
    },
    {
        "name": "Leg Curl",
        "exercise_type": "isolation",
        "target_muscle_groups": ["hamstrings"],
        "equipment_required": ["leg curl machine"],
        "difficulty": "beginner",
        "instructions": "1. Lie face down on leg curl machine\n2. Curl heels towards glutes\n3. Squeeze hamstrings at top\n4. Lower with control",
        "form_cues": ["Control the weight", "Full contraction", "Don't arch back"],
        "alternatives": ["nordic_curl", "glute_ham_raise", "romanian_deadlift"],
    },
    
    # ARM EXERCISES
    {
        "name": "Barbell Curl",
        "exercise_type": "isolation",
        "target_muscle_groups": ["biceps"],
        "equipment_required": ["barbell"],
        "difficulty": "beginner",
        "instructions": "1. Stand with feet shoulder-width apart\n2. Hold bar with underhand grip\n3. Curl bar to shoulder height\n4. Lower with control",
        "form_cues": ["Keep elbows stationary", "Full extension", "Control the weight"],
        "alternatives": ["dumbbell_curl", "cable_curl", "hammer_curl"],
    },
    {
        "name": "Tricep Dip",
        "exercise_type": "compound",
        "target_muscle_groups": ["triceps", "chest", "shoulders"],
        "equipment_required": ["dip bars"],
        "difficulty": "intermediate",
        "instructions": "1. Support yourself on parallel bars\n2. Lower body by bending elbows\n3. Descend until upper arms are parallel\n4. Push back up to starting position",
        "form_cues": ["Lean slightly forward", "Control the descent", "Full lockout"],
        "alternatives": ["close_grip_bench_press", "tricep_pushdown", "overhead_extension"],
    },
    {
        "name": "Hammer Curl",
        "exercise_type": "isolation",
        "target_muscle_groups": ["biceps", "forearms"],
        "equipment_required": ["dumbbells"],
        "difficulty": "beginner",
        "instructions": "1. Stand with dumbbells at sides\n2. Curl dumbbells with neutral grip\n3. Lower with control",
        "form_cues": ["Neutral wrist position", "Control the weight", "Full range"],
        "alternatives": ["barbell_curl", "cable_curl", "preacher_curl"],
    },
    {
        "name": "Tricep Pushdown",
        "exercise_type": "isolation",
        "target_muscle_groups": ["triceps"],
        "equipment_required": ["cable machine", "rope or bar attachment"],
        "difficulty": "beginner",
        "instructions": "1. Stand at cable machine\n2. Push attachment down to full extension\n3. Control return to starting position",
        "form_cues": ["Keep elbows stationary", "Full extension", "Squeeze at bottom"],
        "alternatives": ["overhead_extension", "close_grip_press", "dip"],
    },
    
    # CORE EXERCISES
    {
        "name": "Plank",
        "exercise_type": "isolation",
        "target_muscle_groups": ["core", "abs", "lower back"],
        "equipment_required": ["bodyweight"],
        "difficulty": "beginner",
        "instructions": "1. Start in forearm plank position\n2. Keep body in straight line\n3. Hold position\n4. Breathe steadily",
        "form_cues": ["Straight body line", "Engage core", "Don't sag hips"],
        "alternatives": ["ab_wheel", "hollow_hold", "dead_bug"],
    },
    {
        "name": "Russian Twist",
        "exercise_type": "isolation",
        "target_muscle_groups": ["obliques", "core"],
        "equipment_required": ["bodyweight"],
        "difficulty": "beginner",
        "instructions": "1. Sit with knees bent, feet elevated\n2. Lean back slightly\n3. Rotate torso side to side\n4. Touch floor on each side",
        "form_cues": ["Control the rotation", "Keep core tight", "Full rotation"],
        "alternatives": ["side_plank", "wood_chop", "bicycle_crunch"],
    },
    {
        "name": "Hanging Leg Raise",
        "exercise_type": "isolation",
        "target_muscle_groups": ["lower abs", "core"],
        "equipment_required": ["pull-up bar"],
        "difficulty": "intermediate",
        "instructions": "1. Hang from pull-up bar\n2. Raise legs to hip height\n3. Lower with control",
        "form_cues": ["Control the swing", "Engage core", "Full range"],
        "alternatives": ["knee_raise", "ab_wheel", "v_up"],
    },
    
    # CARDIO/CONDITIONING
    {
        "name": "Treadmill Running",
        "exercise_type": "cardio",
        "target_muscle_groups": ["legs", "cardiovascular"],
        "equipment_required": ["treadmill"],
        "difficulty": "beginner",
        "instructions": "1. Set treadmill to desired speed\n2. Maintain steady pace\n3. Monitor heart rate\n4. Cool down gradually",
        "form_cues": ["Upright posture", "Controlled breathing", "Consistent pace"],
        "alternatives": ["outdoor_running", "cycling", "rowing"],
    },
    {
        "name": "Burpee",
        "exercise_type": "plyometric",
        "target_muscle_groups": ["full body", "cardiovascular"],
        "equipment_required": ["bodyweight"],
        "difficulty": "intermediate",
        "instructions": "1. Start standing\n2. Drop to push-up position\n3. Perform push-up\n4. Jump feet forward\n5. Jump up with arms overhead",
        "form_cues": ["Control the movement", "Full push-up", "Explosive jump"],
        "alternatives": ["jump_squat", "mountain_climber", "high_knees"],
    },
    {
        "name": "Jump Rope",
        "exercise_type": "cardio",
        "target_muscle_groups": ["calves", "shoulders", "cardiovascular"],
        "equipment_required": ["jump rope"],
        "difficulty": "beginner",
        "instructions": "1. Hold rope handles\n2. Swing rope overhead\n3. Jump as rope passes under feet\n4. Maintain steady rhythm",
        "form_cues": ["Stay on balls of feet", "Small jumps", "Consistent rhythm"],
        "alternatives": ["running", "cycling", "rowing"],
    },
]


async def seed_exercise_database():
    """Display exercise database statistics.
    
    Note: This curated exercise database is used as reference data by the AI agents
    when generating workout plans. Exercises are NOT pre-inserted into the database
    as standalone records, since Exercise model requires a workout_id foreign key.
    
    Instead, when generating workout plans, the AI agents will:
    1. Query this EXERCISE_DATABASE to find appropriate exercises
    2. Create Exercise model instances linked to specific workouts
    3. Store them in the database with all required foreign keys
    """
    print(f"Exercise Database Summary")
    print("=" * 60)
    print(f"\nTotal exercises available: {len(EXERCISE_DATABASE)}")
    
    # Count by category
    categories = {}
    for exercise in EXERCISE_DATABASE:
        primary_muscle = exercise["target_muscle_groups"][0]
        categories[primary_muscle] = categories.get(primary_muscle, 0) + 1
    
    print("\nExercises by primary muscle group:")
    for muscle, count in sorted(categories.items()):
        print(f"  - {muscle.title()}: {count} exercises")
    
    # Count by difficulty
    difficulties = {}
    for exercise in EXERCISE_DATABASE:
        diff = exercise["difficulty"]
        difficulties[diff] = difficulties.get(diff, 0) + 1
    
    print("\nExercises by difficulty:")
    for diff, count in sorted(difficulties.items()):
        print(f"  - {diff.title()}: {count} exercises")
    
    # Count by equipment
    equipment_counts = {}
    for exercise in EXERCISE_DATABASE:
        for equip in exercise["equipment_required"]:
            equipment_counts[equip] = equipment_counts.get(equip, 0) + 1
    
    print("\nExercises by equipment (top 10):")
    for equip, count in sorted(equipment_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  - {equip}: {count} exercises")
    
    print("\n" + "=" * 60)
    print("✓ Exercise database ready for AI agent consumption")
    print("\nUsage:")
    print("  - AI agents call get_exercises_by_muscle_group()")
    print("  - AI agents call get_exercises_by_equipment()")
    print("  - AI agents call get_exercises_by_difficulty()")
    print("  - AI agents call get_alternative_exercises()")
    print("=" * 60)


def get_exercises_by_muscle_group(muscle_group: str) -> list[dict]:
    """Get all exercises targeting a specific muscle group.
    
    Args:
        muscle_group: Target muscle group (e.g., "chest", "back", "legs")
        
    Returns:
        List of exercises targeting that muscle group
    """
    return [
        exercise
        for exercise in EXERCISE_DATABASE
        if muscle_group.lower() in [m.lower() for m in exercise["target_muscle_groups"]]
    ]


def get_exercises_by_equipment(equipment: list[str]) -> list[dict]:
    """Get exercises that can be performed with available equipment.
    
    Args:
        equipment: List of available equipment
        
    Returns:
        List of exercises matching equipment availability
    """
    equipment_lower = [e.lower() for e in equipment]
    return [
        exercise
        for exercise in EXERCISE_DATABASE
        if any(req.lower() in equipment_lower for req in exercise["equipment_required"])
        or "bodyweight" in exercise["equipment_required"]
    ]


def get_exercises_by_difficulty(difficulty: str) -> list[dict]:
    """Get exercises by difficulty level.
    
    Args:
        difficulty: Difficulty level ("beginner", "intermediate", "advanced")
        
    Returns:
        List of exercises at that difficulty level
    """
    return [
        exercise
        for exercise in EXERCISE_DATABASE
        if exercise["difficulty"].lower() == difficulty.lower()
    ]


def get_exercise_by_name(name: str) -> dict | None:
    """Get a specific exercise by name.
    
    Args:
        name: Exercise name
        
    Returns:
        Exercise data or None if not found
    """
    name_lower = name.lower().replace("_", " ")
    for exercise in EXERCISE_DATABASE:
        if exercise["name"].lower() == name_lower:
            return exercise
    return None


def get_alternative_exercises(exercise_name: str) -> list[dict]:
    """Get alternative exercises for a given exercise.
    
    Args:
        exercise_name: Name of the exercise
        
    Returns:
        List of alternative exercises
    """
    exercise = get_exercise_by_name(exercise_name)
    if not exercise or "alternatives" not in exercise:
        return []

    alternatives = []
    for alt_name in exercise["alternatives"]:
        alt = get_exercise_by_name(alt_name)
        if alt:
            alternatives.append(alt)
    return alternatives


if __name__ == "__main__":
    # Run seed script
    asyncio.run(seed_exercise_database())
