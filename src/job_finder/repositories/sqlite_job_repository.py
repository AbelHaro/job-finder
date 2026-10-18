"""Atomic listing upserts. Callers own the session transaction."""

import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy import case, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from job_finder.models.job import Job as CollectedJob
from job_finder.models.stored_job import Job
from job_finder.repositories.job_repository import JobRepository


def content_hash(job: CollectedJob) -> str:
    payload = json.dumps([job.title, job.company, job.description], ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class SQLiteJobRepository(JobRepository):
    """Persist jobs using a caller-managed session and transaction."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save_job(self, job: CollectedJob) -> Job:

        statement = insert(Job).values(
            **job.model_dump(), content_hash=content_hash(job)
        )
        incoming = statement.excluded
        changed = Job.content_hash != incoming.content_hash
        match_changed = changed | (Job.location != incoming.location)
        statement = statement.on_conflict_do_update(
            index_elements=[Job.url],
            set_={
                "title": incoming.title,
                "company": incoming.company,
                "location": incoming.location,
                "description": incoming.description,
                "posted": incoming.posted,
                "last_seen_at": datetime.now(UTC).replace(tzinfo=None),
                "content_hash": incoming.content_hash,
                "match_score": case((match_changed, None), else_=Job.match_score),
            },
        ).returning(Job)
        return self.session.scalars(
            statement, execution_options={"populate_existing": True}
        ).one()

    def save_jobs(self, jobs: list[CollectedJob]) -> list[Job]:
        """Upsert jobs in input order within the caller's transaction."""
        return [self.save_job(job) for job in jobs]

    def get_unseen_jobs(self) -> list[Job]:
        """Return jobs with no match score, oldest first."""
        statement = (
            select(Job).where(Job.match_score.is_(None)).order_by(Job.first_seen_at, Job.id)
        )
        return list(self.session.scalars(statement).all())

    def get_jobs_pending_cv_ids(self, min_score: float) -> list[int]:
        statement = (
            select(Job.id)
            .where(Job.match_score >= min_score, Job.cv_generated.is_(False))
            .order_by(Job.id)
        )
        return list(self.session.scalars(statement).all())

    def save_match_score(self, job_id: int, score: float) -> None:
        if not 0 <= score <= 1:
            raise ValueError("score must be between 0 and 1")
        job = self.session.get(Job, job_id)
        if job is None:
            raise ValueError(f"Job {job_id} does not exist")
        job.match_score = score
        self.session.flush()

    def mark_cv_generated(self, job_id: int, path: str) -> None:
        job = self.session.get(Job, job_id)
        if job is None:
            raise ValueError(f"Job {job_id} does not exist")
        job.cv_generated = True
        job.cv_generated_at = datetime.now(UTC).replace(tzinfo=None)
        job.cv_path = path
        self.session.flush()
