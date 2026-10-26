"""Send job digests using pyTelegramBotAPI's synchronous client."""

import os
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from telebot import TeleBot
from telebot.apihelper import ApiException, ApiTelegramException
from telebot.types import LinkPreviewOptions

from job_finder.models.stored_job import Job
from job_finder.services.notification_service import (
    NotificationError,
    NotificationService,
)


def split_message(text: str, limit: int = 4000) -> list[str]:
    """Split below Telegram's limit, including characters using UTF-16 surrogate pairs."""
    if limit < 2:
        raise ValueError("Message limit must allow at least two UTF-16 units.")
    parts = []
    while text:
        chunk = text[:limit]
        while len(chunk.encode("utf-16-le")) > limit * 2:
            chunk = chunk[:-1]
        parts.append(chunk)
        text = text[len(chunk) :]
    return parts


def format_job(job: Job) -> str:
    if job.cv_generated and job.cv_path:
        cv = job.cv_path
        if not Path(job.cv_path).is_file():
            cv += " (file unavailable on this machine)"
    else:
        cv = "Not generated yet (pending or generation failed)"
    description = " ".join(job.description.split())
    if len(description) > 600:
        description = description[:600].rstrip() + "…"
    score = f"{job.match_score:.0%}" if job.match_score is not None else "Unranked"
    return "\n".join(
        [
            f"{job.title} — {job.company}",
            f"Location: {job.location or 'Not specified'}",
            f"Match: {score}",
            f"Posted: {job.posted.isoformat() if job.posted else 'Not specified'}",
            f"Job: {job.url}",
            f"CV: {cv}",
            f"Description: {description or 'Not available'}",
        ]
    )


@dataclass
class TelegramNotificationService(NotificationService):
    bot_token: str = field(repr=False)
    chat_id: str
    bot: TeleBot = field(repr=False)
    request_delay: float = 1.1

    def __init__(self, *, request_delay: float = 1.1) -> None:
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        if not self.bot_token:
            raise ValueError("env variable TELEGRAM_BOT_TOKEN is not set")

        if not self.chat_id:
            raise ValueError("env variable TELEGRAM_CHAT_ID is not set")

        self.bot = TeleBot(self.bot_token, threaded=False)
        self.request_delay = request_delay

    def send_jobs(self, jobs: Sequence[Job], min_score: float) -> None:
        messages = []
        for job in jobs:
            messages.extend(split_message(format_job(job)))
        for index, message in enumerate(messages):
            if index:
                time.sleep(self.request_delay)
            self.send_message(message)

    def send_message(self, text: str) -> None:
        for attempt in range(3):
            try:
                self.bot.send_message(
                    chat_id=self.chat_id,
                    text=text,
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                    timeout=30,
                )
                return
            except ApiTelegramException as exc:
                parameters = exc.result_json.get("parameters")
                retry_after = (
                    parameters.get("retry_after")
                    if isinstance(parameters, dict)
                    else None
                )
                if (
                    exc.error_code == 429
                    and isinstance(retry_after, int)
                    and 0 <= retry_after <= 60
                    and attempt < 2
                ):
                    time.sleep(retry_after)
                    continue
                raise NotificationError(
                    f"Telegram rejected the message (code {exc.error_code})."
                ) from None
            except ApiException, OSError:
                # Client exceptions may contain the request URL and secret bot token.
                raise NotificationError(
                    "Could not deliver the Telegram message."
                ) from None
