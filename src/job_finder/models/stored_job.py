"""SQLAlchemy persistence models, separate from collector DTOs."""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("url", name="uq_jobs_url"),
        CheckConstraint(
            "match_score >= 0 AND match_score <= 1", name="ck_jobs_match_score"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_score: Mapped[float | None] = mapped_column(Float)
    cv_generated: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0"
    )
    cv_generated_at: Mapped[datetime | None] = mapped_column(DateTime())
    cv_path: Mapped[str | None] = mapped_column(Text)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime())
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    company: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    posted: Mapped[date | None] = mapped_column(Date)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(), server_default=func.now()
    )
    content_hash: Mapped[str] = mapped_column(String(64))
