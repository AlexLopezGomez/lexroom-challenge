import json
from pathlib import Path
from typing import Any

from weekly_pulse.loaders.base import DataLoader
from weekly_pulse.models import WeekData


class JSONFileLoader(DataLoader):
    """Loads week data from a directory containing JSON files."""

    def load(self, source: Any) -> tuple[WeekData, WeekData]:
        """Load current and previous week data from JSON files in source directory."""
        source = Path(source)
        current_path = source / "week_current.json"
        previous_path = source / "week_previous.json"

        for path in (current_path, previous_path):
            if not path.exists():
                raise FileNotFoundError(f"Required data file missing: {path}")

        current = WeekData.model_validate(
            json.loads(current_path.read_text(encoding="utf-8"))
        )
        previous = WeekData.model_validate(
            json.loads(previous_path.read_text(encoding="utf-8"))
        )
        return current, previous
