"""Candidate facts shared by ranking and CV generation."""

import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CVHeader:
    name: str
    email: str
    linkedin: str
    portfolio: str
    github: str


@dataclass(frozen=True)
class PersonalEntry:
    title: str
    dates: str
    subtitle: str
    description: str
    technologies: tuple[str, ...] = ()


@dataclass(frozen=True)
class PersonalProject(PersonalEntry):
    id: str = ""
    url: str = ""


@dataclass(frozen=True)
class PersonalInfo:
    header: CVHeader
    summary: str
    experience: tuple[PersonalEntry, ...]
    education: tuple[PersonalEntry, ...]
    projects: tuple[PersonalProject, ...]
    languages: tuple[str, ...]
    interests: tuple[str, ...]
    location: str = ""
    ranking_constraints: tuple[str, ...] = ()

    def to_prompt(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)
