"""Run the LangGraph job collection, ranking and CV workflow."""

import logging

from dotenv import load_dotenv

from job_finder.collectors.base_collector import JobSearch
from job_finder.collectors.linkedin_collector import LinkedInCollector
from job_finder.database.sqlite import session_factory
from job_finder.personal_info import PERSONAL_INFO
from job_finder.services.groq_job_ranking_service import GroqJobRankingService
from job_finder.workflow import JobFinderWorkflow


def main() -> None:
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    workflow = JobFinderWorkflow(
        sessions=session_factory(),
        collector=LinkedInCollector(),
        ranker=GroqJobRankingService(model_name="openai/gpt-oss-120b"),
        personal_info=PERSONAL_INFO,
    ).compile()
    search = JobSearch(query="junior computer vision", location="Spain", limit=5)
    workflow.invoke({"search": search})


if __name__ == "__main__":
    main()
