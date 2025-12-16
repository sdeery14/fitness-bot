"""Check latest fitness plan for lower back recovery."""
import asyncio
import asyncpg
from datetime import datetime


async def main():
    conn = await asyncpg.connect('postgresql://fitnessuser:fitnesspass@localhost:5432/fitnessdb')
    
    # Get latest plan
    plan = await conn.fetchrow("""
        SELECT 
            fp.id,
            fp.version,
            fp.status,
            fp.goal_type,
            fp.goal_description,
            fp.created_at
        FROM fitness_plans fp
        WHERE fp.user_id = '71e043ab-2169-4cbe-9d1c-597b1450d0ac'
        ORDER BY fp.created_at DESC
        LIMIT 1
    """)
    
    if not plan:
        print("No plan found")
        await conn.close()
        return
    
    print(f"Latest Plan ID: {plan['id']}")
    print(f"Version: {plan['version']}")
    print(f"Status: {plan['status']}")
    print(f"Goal: {plan['goal_type']}")
    print(f"Description: {plan['goal_description']}")
    print(f"Created: {plan['created_at']}")
    print()
    
    # Get phases
    phases = await conn.fetch("""
        SELECT id, name, phase_number, start_date, end_date
        FROM phases
        WHERE fitness_plan_id = $1
        ORDER BY phase_number
    """, plan['id'])
    
    print(f"Phases: {len(phases)}")
    for phase in phases:
        print(f"  Phase {phase['phase_number']}: {phase['name']}")
        
        # Get workouts for this phase
        workouts = await conn.fetch("""
            SELECT id, name, workout_type, duration_minutes, intensity_level
            FROM workouts
            WHERE phase_id = $1
            ORDER BY id
        """, phase['id'])
        
        print(f"    Workouts: {len(workouts)}")
        for workout in workouts:
            print(f"      - {workout['name']} ({workout['workout_type']}, {workout['duration_minutes']}min, {workout['intensity_level']} intensity)")
            
            # Get exercises for this workout
            exercises = await conn.fetch("""
                SELECT exercise_order, name, exercise_type, sets, reps
                FROM exercises
                WHERE workout_id = $1
                ORDER BY exercise_order
                LIMIT 5
            """, workout['id'])
            
            print(f"        Exercises: {len(exercises)} total")
            for ex in exercises[:3]:  # Show first 3
                sets_reps = f"{ex['sets']}x{ex['reps']}" if ex['sets'] and ex['reps'] else "time-based"
                print(f"          {ex['exercise_order']}. {ex['name']} ({ex['exercise_type']}, {sets_reps})")
    
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
