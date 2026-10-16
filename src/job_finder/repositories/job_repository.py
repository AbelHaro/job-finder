from abc import ABC, abstractmethod

from job_finder.models.job import Job as CollectedJob
from job_finder.models.stored_job import Job


class JobRepository(ABC):
    @abstractmethod
    def save_job(self, job: CollectedJob) -> Job:
        """Persist a collected job and return its stored representation."""

    @abstractmethod
    def save_jobs(self, jobs: list[CollectedJob]) -> list[Job]:
        """Persist a list of collected jobs and return their stored representations."""

    @abstractmethod
    def get_unseen_jobs(self) -> list[Job]:
        """Return jobs with no match score, oldest first."""

    @abstractmethod
    def save_match_score(self, job_id: int, score: float) -> None:
        """Save a match score between zero and one for an existing job."""
