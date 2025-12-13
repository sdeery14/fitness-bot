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
        # Get the fitness plan to see what the AI generated
        stmt = select(FitnessPlan).order_by(FitnessPlan.created_at.desc()).limit(1)
        result = await session.execute(stmt)
        plan = result.scalar_one_or_none()
        
        if plan and plan.plan_snapshot:
            phases = plan.plan_snapshot.get("phases", [])
            if phases and len(phases) > 0:
                meal_details = phases[0].get("meal_details", {})
                prep_schedule = meal_details.get("meal_prep_schedule", [])
                prep_sessions = meal_details.get("meal_prep_sessions", [])
                
                print("\n=== AI-GENERATED MEAL PREP SCHEDULE ===")
                print(f"\nSession Templates ({len(prep_sessions)}):")
                for i, session in enumerate(prep_sessions):
                    print(f"  [{i}] {session.get('session_name', 'N/A')}")
                
                print(f"\nSchedule Entries ({len(prep_schedule)}):")
                for entry in prep_schedule:
                    session_idx = entry.get("session_index", 0)
                    session_name = prep_sessions[session_idx].get("session_name", "N/A") if session_idx < len(prep_sessions) else "Invalid"
                    print(f"  Day {entry.get('day_offset', 0):2d} @ {entry.get('time', 'N/A'):8s} - Session [{session_idx}] {session_name}")
                    print(f"       Repeats: every {entry.get('repeats_every', 'N/A')} days")
        
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
        print(f"\n{'Date':<15} {'Day Name':<12} {'Session Name':<50}")
        print("=" * 80)
        
        for entry in entries:
            day_name = entry.entry_date.strftime("%A")
            session_name = entry.prep_instructions.get("session_name", "N/A")
            print(f"{entry.entry_date} {day_name:<12} {session_name:<50}")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_prep_schedule())
