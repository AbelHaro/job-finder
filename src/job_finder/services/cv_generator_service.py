from abc import ABC, abstractmethod

from job_finder.models.personal_info import PersonalInfo
from job_finder.models.stored_job import Job


class CVGeneratorService(ABC):
    @abstractmethod
    def generate_cv(self, personal_info: PersonalInfo, job: Job) -> str:
        """Return LaTeX source tailored to the job and supplied personal facts."""
