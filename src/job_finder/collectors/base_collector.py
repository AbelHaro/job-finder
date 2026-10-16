from abc import ABC, abstractmethod

from job_finder.models.job import Job, JobSearch


class BaseCollector(ABC):
    @abstractmethod
    def collect(self, search: JobSearch) -> list[Job]:
        """Return up to search.limit jobs; return [] when none match."""
        ...
