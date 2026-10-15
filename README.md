# Job finder

A small LinkedIn job search scraper using BeautifulSoup4 and Python's standard
HTTP library. No login or API key is needed for public listings.

```bash
uv sync
uv run job-finder
```

Edit the hardcoded `JobSearch` in `src/job_finder/main.py` to change the query,
location, or result limit. It currently searches for "computer vision" in Spain
with a limit of 10.

Results include title, company, location, posting date, and a job link. Location
is optional; LinkedIn determines the default geography when omitted. The scraper
fetches additional pages as needed, pauses one second between requests, and
removes duplicate links. The limit is a maximum, not a guaranteed result count.

LinkedIn can block public requests or return HTTP 429 (rate limited). The command
reports these errors and exits with status 1; try again later. Public page markup
can change, requiring updates to the selectors in `src/job_finder/collectors/linkedin_collector.py`.

Parser reference: [Beautiful Soup documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/).

Use the collector directly:

```python
from job_finder.collectors.base_collector import JobSearch
from job_finder.collectors.linkedin_collector import LinkedInCollector

jobs = LinkedInCollector().collect(
    JobSearch(query="computer vision", location="Spain", limit=10)
)
for job in jobs:
    print(job.title, job.url)
```

The collector returns `Job` models, with `posted` as a date or `None`.
