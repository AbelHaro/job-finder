"""Groq backend for CV generation."""

import os

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq

from job_finder.services.langchain_cv_generator_service import (
    LangChainCVGeneratorService,
)
from job_finder.services.latex_cv_renderer import LatexCVRenderer


class GroqCVGeneratorService(LangChainCVGeneratorService):
    def __init__(
        self,
        model_name: str = "openai/gpt-oss-120b",
        *,
        model: BaseChatModel | None = None,
        renderer: LatexCVRenderer | None = None,
    ):
        if model is None:
            if not os.getenv("GROQ_API_KEY"):
                raise ValueError("GROQ_API_KEY environment variable is not set.")
            model = ChatGroq(
                model=model_name,
                temperature=0,
                reasoning_format="hidden",
                max_retries=4,
            )
        super().__init__(model=model, renderer=renderer)
