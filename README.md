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

## SQLite storage

Storage uses SQLAlchemy, SQLite, Alembic, and python-dotenv. No database server
or Docker container is needed. Initialize the local database with:

```bash
uv sync
uv run alembic upgrade head
uv run job-finder
```

The default file is `jobs.sqlite3` in the project root. Optionally set
`DATABASE_URL=sqlite:///another.sqlite3` in `.env`; relative paths resolve from
the current working directory. Environment variables take precedence over `.env`.
Remove any old PostgreSQL `DATABASE_URL` setting before running.

The collector returns Pydantic `Job` objects. Store them explicitly:

```python
from job_finder.database.sqlite import session_factory
from job_finder.repositories.sqlite_job_repository import SQLiteJobRepository

Session = session_factory()
with Session.begin() as session:
    repository = SQLiteJobRepository(session)
    for job in jobs:
        stored = repository.save_job(job)
```

Each URL has one row. Upserts preserve `first_seen_at`, refresh `last_seen_at`,
and hash title, company, and description with SHA-256. Changes to those fields
clear the embedding and model. Embeddings are nullable JSON arrays; SQLite
storage does not provide vector similarity operators. Timestamps are stored as
UTC without a timezone offset. The scraper command saves collected jobs in one transaction and prints the results.

The initial migration creates a new SQLite database; existing PostgreSQL data
is not copied. Create later migrations with
`uv run alembic revision --autogenerate -m "change"`.
