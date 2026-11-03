
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.services.database import Base


class CustomerProfile(Base):
    __tablename__ = "customer_profiles"

    customer_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True
    )

    age_band: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    pension_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    monthly_contribution: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="GBP"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
