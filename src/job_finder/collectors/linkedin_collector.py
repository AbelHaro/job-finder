"""Collect public LinkedIn job listings using BeautifulSoup."""

import time
from urllib.error import URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup, Tag

from job_finder.collectors.base_collector import BaseCollector
from job_finder.models.job import Job, JobSearch

SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"


def parse_description(html: str) -> str:
    """Extract the full description, excluding surrounding page controls."""
    soup = BeautifulSoup(html, "html.parser")
    description = soup.select_one(".show-more-less-html__markup")
    if description is None:
        description = soup.select_one(".description__text")
    if description is None:
        raise ValueError(
            "LinkedIn job detail page has no description; access may be blocked or its HTML may have changed."
        )
    for element in description.select("script, style, button"):
        element.decompose()
    for br in description.select("br"):
        br.replace_with("\n")
    for block in description.select("p, li, div, h1, h2, h3, h4"):
        block.insert_before("\n")
        block.insert_after("\n")
    text = "\n".join(
        " ".join(line.split())
        for line in description.get_text().splitlines()
        if line.strip()
    )
    if not text:
        raise ValueError("LinkedIn returned an empty job description.")
    return text


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_jobs(html: str) -> list[Job]:
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for card in soup.select(".base-search-card"):
        link = card.select_one("a.base-card__full-link[href]")
        title = card.select_one(".base-search-card__title")
        if link is None or title is None:
            continue
        url = urlsplit(str(link["href"]))
        hostname = url.hostname or ""
        if url.scheme != "https" or not (
            hostname == "linkedin.com" or hostname.endswith(".linkedin.com")
        ):
            continue

        def text(selector: str, card: Tag) -> str:
            element = card.select_one(selector)
            return element.get_text(" ", strip=True) if element else ""

        date = card.select_one("time")
        jobs.append(
            Job(
                title=title.get_text(" ", strip=True),
                company=text(".base-search-card__subtitle", card),
                location=text(".job-search-card__location", card),
                description="",  # Populated from the individual job page.
                posted=(date.get("datetime") or None) if date else None,
                url=urlunsplit((url.scheme, url.netloc, url.path, "", "")),
            )
        )
    return jobs


class LinkedInCollector(BaseCollector):
    def collect(self, search: JobSearch) -> list[Job]:
        """Fetch public listings with pagination and deduplication.

        Raises HTTPError/URLError for request failures and ValueError for
        invalid queries or unexpected response HTML.
        """
        if not search.query.strip():
            raise ValueError("Query must not be empty.")
        jobs = []
        seen = set()
        start = 0
        while len(jobs) < search.limit:
            params = urlencode(
                {"keywords": search.query, "location": search.location, "start": start}
            )
            html = fetch_html(f"{SEARCH_URL}?{params}")
            page = parse_jobs(html)
            if not page:
                if BeautifulSoup(html, "html.parser").get_text(strip=True):
                    raise ValueError(
                        "LinkedIn returned an unexpected page; access may be blocked or its HTML may have changed."
                    )
                break
            added = 0
            for job in page:
                if job.url not in seen:
                    seen.add(job.url)
                    jobs.append(job)
                    added += 1
                    if len(jobs) == search.limit:
                        break
            if not added or len(jobs) >= search.limit:
                break
            start += len(page)
            time.sleep(1)
        for job in jobs:
            retry_count = 3
            for attempt in range(retry_count):
                try:
                    print(
                        f"Trying to fetch description for {job.url} (attempt {attempt + 1})..."
                    )
                    job.description = parse_description(fetch_html(job.url))
                    break  # Successfully fetched and parsed the description
                except (URLError, ValueError) as exc:
                    if attempt < retry_count - 1:
                        time.sleep(2)  # Wait before retrying
                    else:
                        print(f"Failed to fetch description for {job.url}: {exc}")
        return jobs
