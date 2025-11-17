"""Progress tracking endpoints for adherence and measurements."""
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, status

from src.api.deps import CurrentUserId, DatabaseSession
from src.schemas import create_success_response
from src.schemas.progress import MeasurementCreate, MeasurementRead
from src.services.progress_service import ProgressService

router = APIRouter()


# Add fitness_plan_id field to MeasurementCreate if not present
class MeasurementCreateWithPlan(MeasurementCreate):
    """Extended measurement creation with plan reference."""

    fitness_plan_id: UUID | None = None


@router.get("/")
async def get_progress_summary(
    user_id: CurrentUserId,
    db: DatabaseSession,
    fitness_plan_id: UUID | None = None,
):
    """Get comprehensive progress summary for the user.

    Returns adherence statistics, current streak, recent milestones,
    and latest body measurements.

    Args:
        user_id: Current authenticated user ID
        db: Database session
        fitness_plan_id: Optional fitness plan ID to filter by

    Returns:
        Progress summary with adherence, streaks, and measurements
    """
    service = ProgressService(db)
    summary = await service.get_progress_summary(
        user_id=user_id,
        fitness_plan_id=fitness_plan_id,
    )

    return create_success_response(data=summary)


@router.post("/measurements", status_code=status.HTTP_201_CREATED)
async def log_measurement(
    request: MeasurementCreateWithPlan,
    user_id: CurrentUserId,
    db: DatabaseSession,
):
    """Log body measurements.

    Records weight, body fat percentage, and body measurements
    for progress tracking.

    Args:
        request: Measurement data
        user_id: Current authenticated user ID
        db: Database session

    Returns:
        Created measurement record

    Raises:
        HTTPException: If validation fails
    """
    service = ProgressService(db)

    # Convert to Decimal for precision
    weight_lbs = Decimal(str(request.weight_lbs)) if request.weight_lbs else None
    body_fat = Decimal(str(request.body_fat_percentage)) if request.body_fat_percentage else None

    record = await service.log_measurement(
        user_id=user_id,
        fitness_plan_id=request.fitness_plan_id,
        weight_lbs=weight_lbs,
        body_fat_percentage=body_fat,
        measurements=request.measurements,
        energy_level=request.energy_level,
        mood=request.mood,
        user_notes=request.user_notes,
    )

    return create_success_response(
        data={
            "id": str(record.id),
            "record_date": record.record_date.isoformat(),
            "weight_lbs": float(record.weight_lbs) if record.weight_lbs else None,
            "body_fat_percentage": float(record.body_fat_percentage) if record.body_fat_percentage else None,
            "measurements": record.measurements,
            "message": "Measurement logged successfully",
        }
    )


@router.get("/measurements")
async def get_measurements(
    user_id: CurrentUserId,
    db: DatabaseSession,
    limit: int = 10,
):
    """Get measurement history for the user.

    Returns recent body measurements ordered by date (most recent first).

    Args:
        user_id: Current authenticated user ID
        db: Database session
        limit: Maximum number of measurements to return (1-100, default 10)

    Returns:
        List of measurements
    """
    from sqlalchemy import desc, select

    from src.models.progress import ProgressRecord

    # Query measurements
    stmt = (
        select(ProgressRecord)
        .where(ProgressRecord.user_id == user_id)
        .where(ProgressRecord.record_type == "measurement")
        .order_by(desc(ProgressRecord.record_date))
        .limit(limit)
    )

    result = await db.execute(stmt)
    records = result.scalars().all()

    # Convert to response schema
    measurements = [
        MeasurementRead(
            id=r.id,
            record_date=r.record_date,
            weight_lbs=float(r.weight_lbs) if r.weight_lbs else None,
            body_fat_percentage=float(r.body_fat_percentage) if r.body_fat_percentage else None,
            measurements=r.measurements,
            energy_level=r.energy_level,
            mood=r.mood,
            user_notes=r.user_notes,
        )
        for r in records
    ]

    return create_success_response(
        data={
            "measurements": [m.model_dump() for m in measurements],
            "count": len(measurements),
        }
    )

