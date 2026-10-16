from abc import ABC, abstractmethod

from job_finder.models.stored_job import Job


class JobRankingService(ABC):
    @abstractmethod
    def rank_job(self, job: Job, personal_info: str) -> float:
        """Rank a job based on personal information and return a score."""
