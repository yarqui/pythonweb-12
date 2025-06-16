from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db

health_router = APIRouter(prefix="/utils", tags=["utils"])


@health_router.get(
    "/healthchecker",
    summary="Health Check",
    description="Check if the application and database connection are active.",
)
async def health_checker(db: AsyncSession = Depends(get_db)):
    """
    Performs a health check on the application and its database connection.
    """
    try:
        result = await db.execute(text("SELECT 1"))

        if result.scalar_one() != 1:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is not configured correctly",
            )

        return {"message": "Application and database connection are healthy"}

    except Exception as e:
        print(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error connecting to the database",
        ) from e
