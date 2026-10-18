"""Notification contract for a complete run's qualifying jobs."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from job_finder.models.stored_job import Job


class NotificationError(RuntimeError):
    """A notification could not be delivered."""


class NotificationService(ABC):
    @abstractmethod
    def send_jobs(self, jobs: Sequence[Job], min_score: float) -> None:
        """Send qualifying job details and their saved CV locations."""
