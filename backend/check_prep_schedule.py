"""Check meal prep schedule alignment."""
import asyncio
import os
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.models.schedule import ScheduleEntry, Schedule
from src.models.fitness_plan import FitnessPlan
from src.config import settings


async def check_prep_schedule():
    """Check meal prep schedule entries."""
    # Disable pager
    os.environ['PAGER'] = ''
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Get the fitness plan and its meal prep sessions from normalized tables
        from src.models.meal_prep import MealPrepSession
        from src.models.fitness_plan import Phase
        
        stmt = select(FitnessPlan).order_by(FitnessPlan.created_at.desc()).limit(1)
        result = await session.execute(stmt)
        plan = result.scalar_one_or_none()
        
        if plan:
            # Get phases for this plan
            phases_stmt = select(Phase).where(Phase.fitness_plan_id == plan.id).order_by(Phase.phase_number)
            phases_result = await session.execute(phases_stmt)
            phases = list(phases_result.scalars().all())
            
            print("\n=== MEAL PREP SESSIONS FROM DATABASE ===")
            for phase in phases:
                # Get meal prep sessions for this phase
                prep_stmt = select(MealPrepSession).where(MealPrepSession.phase_id == phase.id)
                prep_result = await session.execute(prep_stmt)
                prep_sessions = list(prep_result.scalars().all())
                
                if prep_sessions:
                    print(f"\nPhase {phase.phase_number}: {phase.name}")
                    print(f"Sessions ({len(prep_sessions)}):")
                    for session in prep_sessions:
                        print(f"  - {session.session_name}")
                        print(f"    Target Day: {session.target_day_name}")
                        print(f"    Time: {session.time}")
                        print(f"    Duration: {session.duration_minutes} min")
                        print(f"    Repeats: every {session.repeats_every} days" if session.repeats_every else "    Repeats: One-time")
        
        # Get actual schedule entries
        stmt = (
            select(ScheduleEntry)
            .where(ScheduleEntry.entry_type == "meal_prep")
            .order_by(ScheduleEntry.entry_date)
            .limit(10)
        )
        
        result = await session.execute(stmt)
        entries = result.scalars().all()
        
        print(f"\n\n=== ACTUAL SCHEDULE ENTRIES ===")
        print(f"\n{'Date':<15} {'Day Name':<12} {'Session':<50}")
        print("=" * 80)
        
        for entry in entries:
            day_name = entry.entry_date.strftime("%A")
            # Get the meal prep session details if linked
            if entry.meal_prep_session_id:
                from src.models.meal_prep import MealPrepSession
                session_stmt = select(MealPrepSession).where(MealPrepSession.id == entry.meal_prep_session_id)
                session_result = await session.execute(session_stmt)
                session = session_result.scalar_one_or_none()
                session_name = session.session_name if session else "Unknown"
            else:
                session_name = "N/A"
            print(f"{entry.entry_date} {day_name:<12} {session_name:<50}")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_prep_schedule())
