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
    def get_jobs_pending_cv_ids(self, min_score: float) -> list[int]:
        """Return IDs with a score at least min_score and no generated CV, ordered by ID."""

    @abstractmethod
    def get_generated_jobs_by_ids(self, job_ids: list[int], min_score: float) -> list[Job]:
        """Return qualifying jobs with generated CVs from these IDs, highest score first."""

    @abstractmethod
    def save_match_score(self, job_id: int, score: float) -> None:
        """Save a match score between zero and one for an existing job."""

    @abstractmethod
    def mark_cv_generated(self, job_id: int, path: str) -> None:
        """Record a successfully generated CV for an existing job."""
