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
        timeout=float(os.getenv("CODEX_TIMEOUT", "30")),
    )
    notifier = TelegramNotificationService()
    runner = JobFinderWorkflow(
        sessions=session_factory(),
        collector=LinkedInCollector(),
        ranker=LangChainJobRankingService(model),
        personal_info=PERSONAL_INFO,
        cv_generator=LangChainCVGeneratorService(model),
        notification_service=notifier,
        cv_generation_enabled=False,
    )
    workflow = runner.compile()
    queries = [
        # Software development and backend.
        "junior software engineer",
        "graduate software engineer",
        "desarrollador software junior",
        "entry level python",
        "junior python developer",
        "junior backend developer",
        "desarrollador backend junior",
        "junior golang developer",
        "junior C++ developer",
        "junior typescript developer",
        # Computer vision and applied machine learning.
        "junior computer vision",
        "computer vision engineer",
        "ingeniero visión artificial junior",
        "junior machine learning engineer",
        "graduate machine learning engineer",
        # Embedded software, connected devices and industrial systems.
        "junior embedded systems",
        "junior embedded software engineer",
        "junior firmware engineer",
        "ingeniero software embebido junior",
        "junior IoT",
        "IoT software engineer",
        "ingeniero IoT junior",
        "junior robotics software engineer",
        # Infrastructure roles using Linux, containers and cloud platforms.
        "junior cloud engineer",
        "junior devops engineer",
    ]
    searches = [
        JobSearch(
            query=query,
            location="Spain",
            posted_within_days=1,
            limit=20,
        )
        for query in queries
    ]
    for search in searches:
        workflow.invoke({"search": search})


if __name__ == "__main__":
    main()
