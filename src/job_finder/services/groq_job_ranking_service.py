"""Groq backend for job ranking."""

import os

from langchain_groq import ChatGroq

from job_finder.services.langchain_job_ranking_service import LangChainJobRankingService


class GroqJobRankingService(LangChainJobRankingService):
    def __init__(self, model_name: str = "openai/gpt-oss-120b"):
        if not os.getenv("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY environment variable is not set.")
        super().__init__(
            model=ChatGroq(
                model=model_name,
                temperature=0,
                reasoning_format="hidden",
                max_retries=4,
            )
        )
