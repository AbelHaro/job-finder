"""Verify that CLI saves survive closing its database session."""
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from job_finder.database.models import Base, Job
from job_finder.main import main
from job_finder.models import Job as CollectedJob


class CLIStorageTest(unittest.TestCase):
    def test_collected_jobs_are_committed_and_updated(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'jobs.sqlite3'}")
            Base.metadata.create_all(engine)
            sessions = sessionmaker(engine)
            job = CollectedJob(
                title='Engineer', company='ACME', location='Spain',
                description='Build things', url='https://example.com/job',
            )
            try:
                for description in ('Build things', 'Updated description'):
                    collected = job.model_copy(update={'description': description})
                    with patch('job_finder.main.session_factory', return_value=sessions), \
                         patch('job_finder.main.LinkedInCollector.collect', return_value=[collected]), \
                         redirect_stdout(io.StringIO()):
                        main()
                    with Session(engine) as session:
                        rows = session.scalars(select(Job)).all()
                        self.assertEqual(len(rows), 1)
                        self.assertEqual(rows[0].description, description)
            finally:
                engine.dispose()


if __name__ == '__main__':
    unittest.main()
