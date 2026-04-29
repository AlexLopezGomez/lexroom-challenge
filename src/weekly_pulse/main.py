import logging
import sys

from weekly_pulse.analytics.compute import (
    compute_dau_stats,
    flag_error_modules,
    rank_modules,
)
from weekly_pulse.config import Config
from weekly_pulse.delivery.base import DeliveryChannel
from weekly_pulse.delivery.console import ConsoleDelivery
from weekly_pulse.delivery.webhook import WebhookDelivery
from weekly_pulse.formatters.slack import SlackMarkdownFormatter
from weekly_pulse.llm.highlight import LLMHighlightGenerator
from weekly_pulse.loaders.json_loader import JSONFileLoader
from weekly_pulse.models import PulseReport

logger = logging.getLogger(__name__)


def _build_delivery(config: Config) -> DeliveryChannel:
    """Instantiate the correct delivery channel from config."""
    if config.DELIVERY_MODE == "console":
        return ConsoleDelivery()
    if not config.SLACK_WEBHOOK_URL:
        raise ValueError(
            "SLACK_WEBHOOK_URL is required when DELIVERY_MODE='webhook'"
        )
    return WebhookDelivery(config.SLACK_WEBHOOK_URL, config.WEBHOOK_TIMEOUT_SECONDS)


def run(config: Config) -> None:
    """Run the full pulse pipeline: load → compute → enrich → format → deliver."""
    loader = JSONFileLoader()
    current, previous = loader.load(config.DATA_DIR)

    dau = compute_dau_stats(current, previous)
    top_modules = rank_modules(current.modules, config.TOP_N_MODULES)
    error_flags = flag_error_modules(current.modules, config.ERROR_RATE_THRESHOLD)

    report = PulseReport(
        week=current.week,
        dau=dau,
        top_modules=top_modules,
        error_flags=error_flags,
        highlight=None,
    )

    generator = LLMHighlightGenerator(config)
    report = report.model_copy(update={"highlight": generator.generate(report)})

    formatted = SlackMarkdownFormatter().format(report)
    delivery = _build_delivery(config)
    delivery.deliver(formatted)


def main() -> None:
    """CLI entry point."""
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run(Config())


if __name__ == "__main__":
    main()
