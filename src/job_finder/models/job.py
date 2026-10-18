from datetime import date

from pydantic import BaseModel, Field


class JobSearch(BaseModel):
    query: str = Field(min_length=1)
    location: str = ""
    limit: int = Field(default=25, ge=1)
    posted_within_days: int | None = Field(
        default=None,
        ge=1,
        strict=True,
        description="Only jobs posted in the last N days; None leaves dates unrestricted.",
    )


class Job(BaseModel):
    title: str
    company: str
    location: str
    description: str
    url: str
    posted: date | None = None
