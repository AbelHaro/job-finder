"""Run the LangGraph job collection, ranking and CV workflow."""

import logging
import os

from dotenv import load_dotenv

from job_finder.collectors.base_collector import JobSearch
from job_finder.collectors.linkedin_collector import LinkedInCollector
from job_finder.database.sqlite import session_factory
from job_finder.personal_info import PERSONAL_INFO
from job_finder.services.codex_chat_model import CodexChatModel
from job_finder.services.langchain_cv_generator_service import (
    LangChainCVGeneratorService,
)
from job_finder.services.langchain_job_ranking_service import LangChainJobRankingService
from job_finder.services.telegram_notification_service import (
    TelegramNotificationService,
)
from job_finder.workflow import JobFinderWorkflow


def main() -> None:
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    model = CodexChatModel(
        model_name=os.getenv("CODEX_MODEL") or None,
        executable=os.getenv("CODEX_EXECUTABLE", "codex"),
        timeout=float(os.getenv("CODEX_TIMEOUT", "300")),
    )
    notifier = TelegramNotificationService()
    runner = JobFinderWorkflow(
        sessions=session_factory(),
        collector=LinkedInCollector(),
        ranker=LangChainJobRankingService(model),
        personal_info=PERSONAL_INFO,
        cv_generator=LangChainCVGeneratorService(model),
        notification_service=notifier,
    )
    workflow = runner.compile()
    searchs = [
        JobSearch(
            query="junior computer vision",
            location="Spain",
            posted_within_days=1,
            limit=20,
        ),
        JobSearch(
            query="junior software engineer",
            location="Spain",
            posted_within_days=1,
            limit=20,
        ),
        JobSearch(
            query="junior embedded systems",
            location="Spain",
            posted_within_days=1,
            limit=20,
        ),
        JobSearch(
            query="junior IoT",
            location="Spain",
            posted_within_days=1,
            limit=20,
        ),
        JobSearch(
            query="entry level python",
            location="Spain",
            posted_within_days=1,
            limit=20,
        ),
    ]
    for search in searchs:
        workflow.invoke({"search": search})


if __name__ == "__main__":
    main()
