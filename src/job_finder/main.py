"""Search public LinkedIn job listings using BeautifulSoup."""

import sys
from urllib.error import HTTPError, URLError

from .collectors.base_collector import JobSearch
from .collectors.linkedin_collector import LinkedInCollector


def main() -> None:
    search = JobSearch(query="computer vision", location="Spain", limit=10)
    try:
        jobs = LinkedInCollector().collect(search)
    except HTTPError as exc:
        message = (
            "LinkedIn rate limited the request. Try again later."
            if exc.code == 429
            else f"LinkedIn returned HTTP {exc.code}."
        )
        print(f"Error: {message}", file=sys.stderr)
        raise SystemExit(1) from exc
    except (URLError, TimeoutError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    if not jobs:
        print("No jobs found.")
    else:
        for job in jobs:
            print(f"{job.title} — {job.company}")
            print(f"  {job.description:.100}...")
            print(f"  {job.location} | Posted: {job.posted or 'unknown'}")
            print(f"  {job.url}\n")


if __name__ == "__main__":
    main()
