"""Search public LinkedIn job listings using BeautifulSoup."""

import logging
import time
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv

from job_finder.collectors.base_collector import JobSearch
from job_finder.collectors.linkedin_collector import LinkedInCollector
from job_finder.database.sqlite import session_factory
from job_finder.models.stored_job import Job
from job_finder.personal_info import PERSNAL_INFO
from job_finder.repositories.job_repository import JobRepository
from job_finder.repositories.sqlite_job_repository import SQLiteJobRepository
from job_finder.services.groq_job_ranking_service import GroqJobRankingService
from job_finder.services.job_ranking_service import JobRankingService

load_dotenv()
logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    sessions = session_factory()

    job_ranking_service: JobRankingService = GroqJobRankingService(
        model_name="openai/gpt-oss-20b"
    )

    search = JobSearch(query="computer vision", location="Spain", limit=5)

    jobs = []
    retries = 10
    while retries > 0:
        try:
            jobs = LinkedInCollector().collect(search)
            break
        except HTTPError as exc:
            message = (
                f"LinkedIn rate limited the request. Try number {retries}."
                if exc.code == 429
                else f"LinkedIn returned HTTP {exc.code}."
            )
            logger.warning("Try number %s | Error: %s", retries, message)
            retries -= 1
        except (URLError, TimeoutError, ValueError) as exc:
            logger.warning("Try number %s | Error: %s", retries, exc)
            retries -= 1
    if not jobs:
        logger.warning("No jobs collected; processing previously saved jobs.")

    with sessions.begin() as session:
        job_repo: JobRepository = SQLiteJobRepository(session)
        job_repo.save_jobs(jobs)

    # Each score commits separately so a later API failure preserves progress.
    with sessions() as session:
        job_repo = SQLiteJobRepository(session)
        with session.begin():
            unseen_ids = [job.id for job in job_repo.get_unseen_jobs()]
            logger.info("Found %s unseen jobs to rank.", len(unseen_ids))
        for job_id in unseen_ids:
            with session.begin():
                job = session.get(Job, job_id)
                if job is None or job.match_score is not None:
                    continue
                score = job_ranking_service.rank_job(job, personal_info=PERSNAL_INFO)
                job_repo.save_match_score(job.id, score)
                logger.info(
                    "Ranked job %s | %s | score: %.2f", job.id, job.title, score
                )
            time.sleep(4)


if __name__ == "__main__":
    main()
