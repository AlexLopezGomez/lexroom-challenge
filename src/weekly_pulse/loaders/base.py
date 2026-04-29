from abc import ABC, abstractmethod
from typing import Any

from weekly_pulse.models import WeekData


class DataLoader(ABC):
    """Abstract base for all data loaders."""

    @abstractmethod
    def load(self, source: Any) -> tuple[WeekData, WeekData]:
        """Load and return (current, previous) week data."""
