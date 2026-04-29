from abc import ABC, abstractmethod

from weekly_pulse.models import PulseReport


class ReportFormatter(ABC):
    """Abstract base for all report formatters."""

    @abstractmethod
    def format(self, report: PulseReport) -> str:
        """Format a PulseReport into a deliverable string."""
