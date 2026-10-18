"""Structured tailored content, with required sections and at most three projects."""

from pydantic import BaseModel, Field


class CVEntry(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    dates: str = Field(default="", max_length=100)
    subtitle: str = Field(default="", max_length=300)
    bullets: list[str] = Field(min_length=1, max_length=4)


class CVProject(CVEntry):
    project_id: str = Field(description="Exact ID from the supplied candidate project catalog")
    bullets: list[str] = Field(min_length=2, max_length=3)


class CVExperience(CVEntry):
    bullets: list[str] = Field(min_length=2, max_length=3)


class CVHeadings(BaseModel):
    profile: str
    experience: str
    projects: str
    education: str
    languages: str
    technologies: str


class CVContent(BaseModel):
    headline: str = Field(min_length=1, max_length=200)
    headings: CVHeadings
    profile: str = Field(min_length=1, max_length=1600)
    experience: list[CVExperience] = Field(min_length=1, max_length=6)
    projects: list[CVProject] = Field(min_length=1, max_length=3)
    education: list[CVEntry] = Field(min_length=1, max_length=4)
    languages: list[str] = Field(min_length=1, max_length=4)
