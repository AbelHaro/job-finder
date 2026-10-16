"""Atomic listing upserts. Callers own the session transaction."""

import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import case
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
        statement = statement.on_conflict_do_update(
            index_elements=[Job.url],
            set_={
                "title": incoming.title,
                "company": incoming.company,
                "location": incoming.location,
                "description": incoming.description,
                "posted": incoming.posted,
                "last_seen_at": datetime.now(timezone.utc).replace(tzinfo=None),
                "content_hash": incoming.content_hash,
                "embedding": case((changed, None), else_=Job.embedding),
                "embedding_model": case((changed, None), else_=Job.embedding_model),
            },
        ).returning(Job)
        return self.session.scalars(
            statement, execution_options={"populate_existing": True}
        ).one()
