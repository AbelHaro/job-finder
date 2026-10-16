"""SQLAlchemy persistence models, separate from collector DTOs."""

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
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
    __table_args__ = (UniqueConstraint("url", name="uq_jobs_url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
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
    embedding: Mapped[list[float] | None] = mapped_column(JSON(none_as_null=True))
    embedding_model: Mapped[str | None] = mapped_column(Text)
