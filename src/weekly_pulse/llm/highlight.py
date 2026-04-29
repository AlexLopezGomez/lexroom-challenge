import logging

from openai import APIConnectionError, APIError, APITimeoutError, OpenAI, RateLimitError

from weekly_pulse.config import Config
from weekly_pulse.models import PulseReport

logger = logging.getLogger(__name__)


class LLMHighlightGenerator:
    """Generates a one-sentence highlight via OpenAI Responses API."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._client = (
            OpenAI(api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None
        )

    def generate(self, report: PulseReport) -> str | None:
        """Return a single-sentence highlight, or None on any failure."""
        if self._client is None:
            logger.warning("OPENAI_API_KEY not set; skipping LLM highlight.")
            return None

        prompt = self._build_prompt(report)
        try:
            response = self._client.responses.create(
                model=self._config.LLM_MODEL,
                instructions="You are a concise engineering analyst. Output exactly one sentence. No preamble.",
                input=prompt,
                max_output_tokens=120,
                timeout=self._config.LLM_TIMEOUT_SECONDS,
            )
        except (APITimeoutError, APIConnectionError, RateLimitError, APIError) as exc:
            logger.warning("LLM call failed: %s", exc)
            return None

        text = (response.output_text or "").strip()
        return text or None

    @staticmethod
    def _build_prompt(report: PulseReport) -> str:
        """Build the prompt string from report data."""
        top = ", ".join(f"{m.name} ({m.artifacts:,})" for m in report.top_modules)
        flags = (
            ", ".join(f"{f.name} ({f.error_rate:.1%})" for f in report.error_flags)
            if report.error_flags
            else "none"
        )
        return (
            f"Week: {report.week}\n"
            f"Avg DAU: {report.dau.avg_current:.0f}"
            f" ({report.dau.pct_change:+.1f}% vs last week)\n"
            f"Top modules by volume: {top}\n"
            f"High error rate modules: {flags}\n"
            "Write one sentence summarizing the most important signal."
        )
