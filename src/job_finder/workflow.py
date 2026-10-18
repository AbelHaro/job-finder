"""LangGraph workflow for collecting, ranking and preparing job applications."""

import hashlib
import logging
import re
import time
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from urllib.error import HTTPError, URLError

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.orm import Session, sessionmaker

from job_finder.collectors.base_collector import BaseCollector
from job_finder.models.job import Job as CollectedJob
from job_finder.models.job import JobSearch
from job_finder.models.personal_info import PersonalInfo
from job_finder.models.stored_job import Job
from job_finder.repositories.sqlite_job_repository import SQLiteJobRepository
from job_finder.services.groq_cv_generator_service import GroqCVGeneratorService
from job_finder.services.job_ranking_service import JobRankingService

logger = logging.getLogger(__name__)


def filename_slug(value: str, limit: int = 150) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", normalized.lower()).strip("_")[:limit].rstrip("_") or "job"


def cv_filename(job_name: str) -> str:
    """Keep filenames readable and prevent job titles from becoming paths."""
    return f"abel_haro_armero_cv_{filename_slug(job_name)}.pdf"


def cv_folder_name(job: Job) -> str:
    """Identify the company and role; a stable URL hash distinguishes duplicate titles."""
    suffix = hashlib.sha256(job.url.encode()).hexdigest()[:10]
    return f"{filename_slug(job.company, 60)}_{filename_slug(job.title, 90)}_{suffix}"


@dataclass
class WorkflowState:
    search: JobSearch
    jobs: list[CollectedJob] = field(default_factory=list)
    ranked_ids: list[int] = field(default_factory=list)
    generated_paths: list[str] = field(default_factory=list)
    failed_cv_ids: list[int] = field(default_factory=list)


@dataclass
class JobFinderWorkflow:
    sessions: sessionmaker[Session]
    collector: BaseCollector
    ranker: JobRankingService
    personal_info: PersonalInfo
    cv_generator_factory: Callable[[], GroqCVGeneratorService] = GroqCVGeneratorService
    output_dir: Path = Path("generated_cvs")
    request_delay: float = 4
    collection_attempts: int = 10

    def collect_jobs(self, state: WorkflowState) -> dict:
        jobs = []
        for attempt in range(1, self.collection_attempts + 1):
            try:
                jobs = self.collector.collect(state.search)
                break
            except HTTPError as exc:
                message = (
                    "LinkedIn rate limited the request."
                    if exc.code == 429
                    else f"LinkedIn returned HTTP {exc.code}."
                )
                logger.warning("Collection attempt %s | %s", attempt, message)
            except (URLError, TimeoutError, ValueError) as exc:
                logger.warning("Collection attempt %s | Error: %s", attempt, exc)
        if not jobs:
            logger.warning("No jobs collected; processing previously saved jobs.")
        return {"jobs": jobs}

    def store_jobs(self, state: WorkflowState) -> dict:
        with self.sessions.begin() as session:
            SQLiteJobRepository(session).save_jobs(state.jobs)
        return {}

    def rank_jobs(self, state: WorkflowState) -> dict:
        ranked_ids = []
        # Each score commits separately so a later API failure preserves progress.
        with self.sessions() as session:
            repository = SQLiteJobRepository(session)
            with session.begin():
                unseen_ids = [job.id for job in repository.get_unseen_jobs()]
                logger.info("Found %s unseen jobs to rank.", len(unseen_ids))
            for job_id in unseen_ids:
                with session.begin():
                    job = session.get(Job, job_id)
                    if job is None or job.match_score is not None:
                        continue
                    score = self.ranker.rank_job(
                        job, personal_info=self.personal_info.to_prompt()
                    )
                    repository.save_match_score(job.id, score)
                    logger.info(
                        "Ranked job %s | %s | score: %.2f", job.id, job.title, score
                    )
                ranked_ids.append(job_id)
                time.sleep(self.request_delay)
        return {"ranked_ids": ranked_ids}

    def adopt_existing_cv(self, job: Job, output: Path) -> bool:
        """Reuse completed files, including the previous numeric-folder layout."""
        if output.is_file() and output.with_suffix(".tex").is_file():
            return True
        legacy = self.output_dir / str(job.id) / cv_filename(job.title)
        if legacy.is_file() and legacy.with_suffix(".tex").is_file():
            # Move the whole job folder so a completed CV is never regenerated.
            if output.parent.exists():
                raise FileExistsError(f"Cannot migrate CV folder: {output.parent} already exists")
            legacy.parent.rename(output.parent)
            return True
        return False

    def generate_cvs(self, state: WorkflowState) -> dict:
        generated_paths = []
        failed_cv_ids = []
        with self.sessions() as session:
            job_ids = SQLiteJobRepository(session).get_jobs_pending_cv_ids(min_score=0.6)
        generator = None
        for job_id in job_ids:
            try:
                # Commit each successful CV independently, preserving progress on failures.
                with self.sessions.begin() as session:
                    job = session.get(Job, job_id)
                    if job is None or job.cv_generated:
                        continue
                    output = self.output_dir / cv_folder_name(job) / cv_filename(job.title)
                    existing = self.adopt_existing_cv(job, output)
                    if not existing:
                        if generator is None:
                            generator = self.cv_generator_factory()
                        generator.generate_pdf(self.personal_info, job, output)
                    if not output.is_file() or not output.with_suffix(".tex").is_file():
                        raise RuntimeError("CV generation did not produce both PDF and LaTeX files")
                    SQLiteJobRepository(session).mark_cv_generated(job.id, str(output.resolve()))
                if not existing:
                    generated_paths.append(str(output))
                logger.info("Recorded %s CV for job %s | %s", "existing" if existing else "generated", job_id, output)
            except Exception:
                failed_cv_ids.append(job_id)
                logger.exception("CV generation failed for job %s", job_id)
            time.sleep(self.request_delay)
        return {"generated_paths": generated_paths, "failed_cv_ids": failed_cv_ids}

    def compile(self) -> CompiledStateGraph:
        graph = StateGraph(WorkflowState)
        graph.add_node("collect_jobs", self.collect_jobs)
        graph.add_node("store_jobs", self.store_jobs)
        graph.add_node("rank_jobs", self.rank_jobs)
        graph.add_node("generate_cvs", self.generate_cvs)
        graph.add_edge(START, "collect_jobs")
        graph.add_edge("collect_jobs", "store_jobs")
        graph.add_edge("store_jobs", "rank_jobs")
        graph.add_edge("rank_jobs", "generate_cvs")
        graph.add_edge("generate_cvs", END)
        return graph.compile()
