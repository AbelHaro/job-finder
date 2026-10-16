"""Search public LinkedIn job listings using BeautifulSoup."""

import sys
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv

from job_finder.collectors.base_collector import JobSearch
from job_finder.collectors.linkedin_collector import LinkedInCollector
from job_finder.database.sqlite import session_factory
from job_finder.repository import JobRepository

load_dotenv()


def main() -> None:

    job_repo = JobRepository(session_factory()())

    search = JobSearch(query="computer vision", location="Spain", limit=10)

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
            print(f"Try number {retries} | Error: {message}", file=sys.stderr)
            retries -= 1
        except (URLError, TimeoutError, ValueError) as exc:
            print(f"Try number {retries} | Error: {exc}", file=sys.stderr)
            retries -= 1
    if not jobs:
        print("No jobs found.")
        sys.exit(1)

    with job_repo.session.begin():
        for job in jobs:
            saved_job = job_repo.save_job(job)
            print(f"Saved job {saved_job.id} | {saved_job.title} | {saved_job.company}")


if __name__ == "__main__":
    main()
