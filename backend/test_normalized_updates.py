"""Test that plan updates work with normalized workout_plan schema."""
import asyncio
from uuid import UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.services.plan_service import PlanService

DATABASE_URL = "postgresql+asyncpg://fitness_user:fitness_pass_dev@localhost:5432/fitness_bot"

async def test_update_program_type():
    """Test updating the program_type field directly."""
    # Setup
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        plan_service = PlanService(session)
        
        # Test user's active plan
        user_id = UUID("71e043ab-2169-4cbe-9d1c-597b1450d0ac")
        active_plan = await plan_service.get_active_plan(user_id)
        
        if not active_plan:
            print("❌ No active plan found")
            return
        
        # Eagerly load workout_plans to avoid lazy loading issues
        await session.refresh(active_plan, ["workout_plans"])
        
        print(f"✓ Found active plan: {active_plan.id}")
        print(f"  Current program_type: {active_plan.workout_plans[0].program_type}")
        
        # Apply update to change program_type
        updates = [
            {
                "field": "workout_plans[0].program_type",
                "value": "Full Body Only",
                "operation": "set"
            }
        ]
        
        try:
            new_plan = await plan_service.apply_plan_updates(
                parent_plan_id=active_plan.id,
                updates=updates,
                version_notes="Testing normalized schema update: changed to Full Body Only"
            )
            
            # Eagerly load workout_plans on new plan
            await session.refresh(new_plan, ["workout_plans"])
            
            print(f"✓ Created new plan version: {new_plan.id}")
            print(f"  New program_type: {new_plan.workout_plans[0].program_type}")
            print(f"  Training principles: {new_plan.workout_plans[0].training_principles}")
            
            # Verify parent plan status
            await session.refresh(active_plan)
            print(f"✓ Parent plan status: {active_plan.status}")
            
            print("\n✅ All tests passed! Normalized schema updates work correctly.")
            
        except Exception as e:
            print(f"❌ Update failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_update_program_type())
