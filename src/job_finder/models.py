from datetime import date

from pydantic import BaseModel, Field


class JobSearch(BaseModel):
    query: str = Field(min_length=1)
    location: str = ""
    limit: int = Field(default=25, ge=1)


class Job(BaseModel):
    title: str
    company: str
    location: str
    description: str
    url: str
    posted: date | None = None
