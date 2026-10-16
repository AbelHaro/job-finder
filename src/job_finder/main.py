"""Search public LinkedIn job listings using BeautifulSoup."""

import logging
import sys
import time
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv

from job_finder.collectors.base_collector import JobSearch
from job_finder.collectors.linkedin_collector import LinkedInCollector
from job_finder.database.sqlite import session_factory
from job_finder.personal_info import PERSNAL_INFO
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

    job_repo = SQLiteJobRepository(session_factory()())

    job_ranking_service: JobRankingService = GroqJobRankingService(
        model_name="openai/gpt-oss-20b"
    )

    search = JobSearch(query="computer vision", location="Spain", limit=5)

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
        logger.warning("No jobs found.")
        sys.exit(1)

    with job_repo.session.begin():
        for job in jobs:
            saved_job = job_repo.save_job(job)
            logger.info("Saved job %s | %s | %s", saved_job.id, saved_job.title, saved_job.company)

            score = job_ranking_service.rank_job(saved_job, personal_info=PERSNAL_INFO)
            logger.info("Job score: %.2f", score)

            time.sleep(4)  # Sleep for 4 seconds to avoid hitting rate limits


if __name__ == "__main__":
    main()
