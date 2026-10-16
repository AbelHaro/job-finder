from abc import ABC, abstractmethod

from job_finder.models.job import Job as CollectedJob
from job_finder.models.stored_job import Job


class JobRepository(ABC):
    @abstractmethod
    def save_job(self, job: CollectedJob) -> Job:
        """Persist a collected job and return its stored representation."""
