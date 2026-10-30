import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from urllib.error import URLError

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from job_finder.models.job import Job as CollectedJob
from job_finder.models.job import JobSearch
from job_finder.models.personal_info import PersonalInfo
from job_finder.models.stored_job import Base, Job
from job_finder.personal_info import PERSONAL_INFO
from job_finder.repositories.sqlite_job_repository import SQLiteJobRepository
from job_finder.workflow import JobFinderWorkflow, cv_filename, cv_folder_name


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(self.engine)
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(self.engine.dispose)
        self.collector = Mock()
        self.collector.collect.return_value = []
        self.ranker = Mock()
        self.generator = Mock()
        self.generated_job_ids: list[int] = []
        self.generator.generate_pdf.side_effect = self.write_cv
        self.workflow = JobFinderWorkflow(
            sessions=self.sessions,
            collector=self.collector,
            ranker=self.ranker,
            personal_info=PERSONAL_INFO,
            cv_generator=self.generator,
            output_dir=Path(self.directory.name),
            request_delay=0,
            collection_attempts=2,
            cv_generation_enabled=True,
            match_threshold=0.6,
        )
        self.search = JobSearch(query="Python", limit=5)

    def write_cv(self, personal_info: PersonalInfo, job: Job, output: Path) -> Path:
        self.generated_job_ids.append(job.id)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"%PDF-example")
        output.with_suffix(".tex").write_text("example")
        return output

    def test_paused_cvs_notify_new_matches_without_generating(self) -> None:
        self.workflow.cv_generation_enabled = False
        self.workflow.match_threshold = 0.5
        self.save([None, None, 0.9])
        self.ranker.rank_job.side_effect = [0.5, 0.49]
        notifier = Mock()
        self.workflow.notification_service = notifier
        result = self.workflow.compile().invoke({"search": self.search})
        self.assertEqual(result["notified_job_ids"], [1])
        self.assertEqual(result["generated_paths"], [])
        self.generator.generate_pdf.assert_not_called()
        jobs = notifier.send_jobs.call_args.args[0]
        self.assertEqual([job.id for job in jobs], [1])
        self.assertFalse(jobs[0].cv_generated)
        result = self.workflow.compile().invoke({"search": self.search})
        self.assertEqual(result["notified_job_ids"], [])
        self.assertEqual(notifier.send_jobs.call_count, 1)
        duplicate = self.workflow.notify_job(1, require_cv=False)
        self.assertEqual(duplicate["notified_job_ids"], [])
        self.assertEqual(notifier.send_jobs.call_count, 1)

    def get_job(self, session: Session, job_id: int) -> Job:
        job = session.get(Job, job_id)
        if job is None:
            raise AssertionError(f"Expected job {job_id} to exist")
        return job

    def save(self, scores: list[float | None]) -> None:
        with self.sessions.begin() as session:
            for job_id, score in enumerate(scores, 1):
                session.add(
                    Job(
                        id=job_id,
                        title="Python Engineer",
                        company="Company",
                        location="Spain",
                        description="Python development",
                        url=f"https://example.com/{job_id}",
                        content_hash=str(job_id),
                        match_score=score,
                    )
                )

    def test_graph_order_threshold_existing_cv_and_failure_continuation(self) -> None:
        self.save([0.59, 0.6, 0.8, 0.9, None])
        self.ranker.rank_job.return_value = 0.6
        existing = self.workflow.output_dir / "3" / cv_filename("Python Engineer")
        existing.parent.mkdir()
        existing.write_bytes(b"existing")
        existing.with_suffix(".tex").write_text("existing")

        def fail_first(personal_info: PersonalInfo, job: Job, output: Path) -> Path:
            if job.id == 2:
                self.generated_job_ids.append(job.id)
                raise RuntimeError("model failed")
            return self.write_cv(personal_info, job, output)

        self.generator.generate_pdf.side_effect = fail_first
        with self.assertLogs("job_finder.workflow", level="INFO"):
            updates = list(
                self.workflow.compile().stream(
                    {"search": self.search}, stream_mode="updates"
                )
            )
        self.assertEqual(
            [next(iter(update)) for update in updates],
            ["collect_jobs", "store_jobs", "rank_jobs", "generate_cvs"],
        )
        self.assertEqual(updates[2]["rank_jobs"]["ranked_ids"], [5])
        self.assertEqual(updates[3]["generate_cvs"]["failed_cv_ids"], [2])
        self.assertEqual(len(updates[3]["generate_cvs"]["generated_paths"]), 2)
        calls = self.generator.generate_pdf.call_args_list
        self.assertEqual(self.generated_job_ids, [2, 4, 5])
        self.assertTrue(all(call.args[0] is PERSONAL_INFO for call in calls))
        self.assertEqual(len({call.args[2] for call in calls}), 3)
        with self.sessions() as session:
            self.assertEqual(self.get_job(session, 5).match_score, 0.6)
            adopted = self.get_job(session, 3)
            self.assertTrue(adopted.cv_generated)
            self.assertIsNotNone(adopted.cv_generated_at)
            assert adopted.cv_path is not None
            self.assertEqual(Path(adopted.cv_path).read_bytes(), b"existing")
            self.assertIn("company_python_engineer", Path(adopted.cv_path).parent.name)
            self.assertTrue(self.get_job(session, 4).cv_generated)
            self.assertFalse(self.get_job(session, 2).cv_generated)
        self.assertFalse(existing.parent.exists())

    def test_collection_retries_then_processes_saved_jobs(self) -> None:
        self.save([0.6])
        self.collector.collect.side_effect = URLError("offline")
        with self.assertLogs("job_finder.workflow", level="WARNING"):
            result = self.workflow.compile().invoke({"search": self.search})
        self.assertEqual(self.collector.collect.call_count, 2)
        self.assertEqual(result["ranked_ids"], [])
        self.assertEqual(len(result["generated_paths"]), 1)

    def test_collected_job_is_stored_and_ranked(self) -> None:
        self.collector.collect.return_value = [
            CollectedJob(
                title="Engineer",
                company="Company",
                location="Spain",
                description="Python",
                url="https://example.com/new",
            )
        ]
        self.ranker.rank_job.return_value = 0.59
        result = self.workflow.compile().invoke({"search": self.search})
        self.assertEqual(len(result["ranked_ids"]), 1)
        self.assertEqual(result["generated_paths"], [])
        self.generator.generate_pdf.assert_not_called()
        call = self.ranker.rank_job.call_args
        assert call is not None
        self.assertEqual(
            call.kwargs["personal_info"],
            PERSONAL_INFO.to_prompt(),
        )

    def test_promotional_companies_are_not_stored_or_ranked(self) -> None:
        self.collector.collect.return_value = [
            CollectedJob(
                title="Engineer", company=company, location="Spain",
                description="Python", url=f"https://example.com/filter/{index}",
            )
            for index, company in enumerate([
                "Evolve", "EVOLVE", " Bending  Spoons ", "JOINRS", "Joinrs",
                "Evolve Technologies", "Company",
            ])
        ]
        self.ranker.rank_job.return_value = 0.1
        result = self.workflow.compile().invoke({"search": self.search})
        with self.sessions() as session:
            from sqlalchemy import select

            companies = list(session.scalars(select(Job.company).order_by(Job.id)))
        self.assertEqual(companies, ["Evolve Technologies", "Company"])
        self.assertEqual(len(result["ranked_ids"]), 2)
        self.assertEqual(self.ranker.rank_job.call_count, 2)

    def test_database_tracking_skips_completed_job_even_if_files_are_removed(
        self,
    ) -> None:
        self.save([0.6])
        graph = self.workflow.compile()
        graph.invoke({"search": self.search})
        self.assertEqual(self.generator.generate_pdf.call_count, 1)
        with self.sessions() as session:
            job = self.get_job(session, 1)
            self.assertTrue(job.cv_generated)
            self.assertIsNotNone(job.cv_generated_at)
            assert job.cv_path is not None
            path = Path(job.cv_path)
            self.assertEqual(path.parent.name, cv_folder_name(job))
        path.unlink()
        path.with_suffix(".tex").unlink()
        result = graph.invoke({"search": self.search})
        self.assertEqual(result["generated_paths"], [])
        self.assertEqual(self.generator.generate_pdf.call_count, 1)

    def test_failed_cv_is_retried(self) -> None:
        self.save([0.6])
        self.generator.generate_pdf.side_effect = RuntimeError("failure")
        graph = self.workflow.compile()
        with self.assertLogs("job_finder.workflow", level="ERROR"):
            result = graph.invoke({"search": self.search})
        self.assertEqual(result["failed_cv_ids"], [1])
        with self.sessions() as session:
            self.assertFalse(self.get_job(session, 1).cv_generated)
            self.assertIsNone(self.get_job(session, 1).cv_path)
        self.generator.generate_pdf.side_effect = self.write_cv
        result = graph.invoke({"search": self.search})
        self.assertEqual(len(result["generated_paths"]), 1)
        with self.sessions() as session:
            self.assertTrue(self.get_job(session, 1).cv_generated)

    def test_upsert_preserves_generation_tracking(self) -> None:
        collected = CollectedJob(
            title="Engineer",
            company="Company",
            location="Spain",
            description="Python",
            url="https://example.com/upsert",
        )
        with self.sessions.begin() as session:
            repo = SQLiteJobRepository(session)
            job = repo.save_job(collected)
            job_id = job.id
            repo.mark_cv_generated(job_id, "/tmp/cv.pdf")
        with self.sessions.begin() as session:
            updated = collected.model_copy(
                update={"description": "Updated Python role"}
            )
            job = SQLiteJobRepository(session).save_job(updated)
            self.assertTrue(job.cv_generated)
            self.assertEqual(job.cv_path, "/tmp/cv.pdf")
            self.assertIsNotNone(job.cv_generated_at)

    def test_each_cv_is_committed_and_notified_before_generating_the_next(self) -> None:
        self.save([0.59, 0.6, 0.9])
        notifier = Mock()
        self.workflow.notification_service = notifier
        events = []

        def generate(personal_info, job, output):
            events.append(("generate", job.id))
            return self.write_cv(personal_info, job, output)

        self.generator.generate_pdf.side_effect = generate

        def check_jobs(jobs, min_score):
            self.assertEqual(len(jobs), 1)
            events.append(("notify", jobs[0].id))
            self.assertEqual(min_score, 0.6)
            for job in jobs:
                self.assertTrue(job.cv_generated)
                assert job.cv_path is not None
                self.assertTrue(Path(job.cv_path).is_file())
                with self.sessions() as session:
                    self.assertTrue(self.get_job(session, job.id).cv_generated)

        notifier.send_jobs.side_effect = check_jobs
        updates = list(
            self.workflow.compile().stream(
                {"search": self.search}, stream_mode="updates"
            )
        )
        self.assertEqual(events, [
            ("generate", 2), ("notify", 2), ("generate", 3), ("notify", 3),
        ])
        self.assertEqual(updates[-1]["generate_cvs"]["notified_job_ids"], [2, 3])
        self.assertEqual(notifier.send_jobs.call_count, 2)
        self.assertEqual(updates[-1]["generate_cvs"]["generated_job_ids"], [2, 3])
        result = self.workflow.compile().invoke({"search": self.search})
        self.assertEqual(result["generated_job_ids"], [])
        self.assertEqual(result["notified_job_ids"], [])
        self.assertEqual(notifier.send_jobs.call_count, 2)

    def test_notifications_exclude_existing_adopted_and_failed_cvs(self) -> None:
        self.save([0.6, 0.8, 0.9, 0.7])
        with self.sessions.begin() as session:
            SQLiteJobRepository(session).mark_cv_generated(2, "/tmp/old_cv.pdf")
        legacy = self.workflow.output_dir / "3" / cv_filename("Python Engineer")
        legacy.parent.mkdir()
        legacy.write_bytes(b"existing")
        legacy.with_suffix(".tex").write_text("existing")

        def generate(personal_info: PersonalInfo, job: Job, output: Path) -> Path:
            if job.id == 4:
                raise RuntimeError("Generation failed")
            return self.write_cv(personal_info, job, output)

        self.generator.generate_pdf.side_effect = generate
        notifier = Mock()
        self.workflow.notification_service = notifier
        with self.assertLogs("job_finder.workflow", level="ERROR"):
            result = self.workflow.compile().invoke({"search": self.search})
        self.assertEqual(result["generated_job_ids"], [1])
        self.assertEqual(result["notified_job_ids"], [1])
        self.assertEqual(result["failed_cv_ids"], [4])
        call = notifier.send_jobs.call_args
        assert call is not None
        self.assertEqual([job.id for job in call.args[0]], [1])

    def test_notification_failure_preserves_successful_cvs(self) -> None:
        self.save([0.6, 0.8])
        notifier = Mock()
        notifier.send_jobs.side_effect = [RuntimeError("Telegram unavailable"), None]
        self.workflow.notification_service = notifier
        with self.assertLogs("job_finder.workflow", level="ERROR"):
            result = self.workflow.compile().invoke({"search": self.search})
        self.assertTrue(result["notification_failed"])
        self.assertEqual(len(result["generated_paths"]), 2)
        self.assertEqual(result["notified_job_ids"], [2])
        self.assertEqual(result["failed_cv_ids"], [])
        self.assertEqual(notifier.send_jobs.call_count, 2)
        with self.sessions() as session:
            self.assertTrue(self.get_job(session, 1).cv_generated)
            self.assertTrue(self.get_job(session, 2).cv_generated)

    def test_ranking_timeout_continues_and_is_retried_next_run(self) -> None:
        self.save([None, None, None])
        self.ranker.rank_job.side_effect = [0.6, TimeoutError("timeout"), 0.7]
        graph = self.workflow.compile()
        with self.assertLogs("job_finder.workflow", level="WARNING"):
            result = graph.invoke({"search": self.search})
        self.assertEqual(result["ranked_ids"], [1, 3])
        self.assertEqual(result["failed_ranking_ids"], [2])
        self.assertEqual(self.generated_job_ids, [1, 3])
        with self.sessions() as session:
            self.assertEqual(self.get_job(session, 1).match_score, 0.6)
            self.assertIsNone(self.get_job(session, 2).match_score)
            self.assertEqual(self.get_job(session, 3).match_score, 0.7)
        self.ranker.rank_job.side_effect = [0.8]
        result = graph.invoke({"search": self.search})
        self.assertEqual(result["ranked_ids"], [2])
        self.assertEqual(result["failed_ranking_ids"], [])

    def test_ranking_failure_preserves_previously_committed_score(self) -> None:
        self.save([None, None])
        self.ranker.rank_job.side_effect = [0.6, RuntimeError("ranking failed")]
        with self.assertRaisesRegex(RuntimeError, "ranking failed"):
            self.workflow.compile().invoke({"search": self.search})
        with self.sessions() as session:
            self.assertEqual(self.get_job(session, 1).match_score, 0.6)
            self.assertIsNone(self.get_job(session, 2).match_score)
        self.generator.generate_pdf.assert_not_called()


if __name__ == "__main__":
    unittest.main()
