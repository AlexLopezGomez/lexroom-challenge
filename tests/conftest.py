import json
from pathlib import Path

import pytest

from weekly_pulse.models import DAUStats, ErrorFlag, ModuleData, ModuleRank, PulseReport, WeekData

CURRENT_PAYLOAD = {
    "week": "2025-03-24",
    "daily_active_users": [482, 510, 498, 523, 501, 165, 58],
    "modules": [
        {"name": "Ask Lexroom", "artifacts": 12350, "errors": 187, "avg_response_ms": 2840},
        {"name": "Drafting", "artifacts": 5820, "errors": 95, "avg_response_ms": 4120},
        {"name": "Document Analysis", "artifacts": 3200, "errors": 410, "avg_response_ms": 3500},
        {"name": "Legal Research", "artifacts": 2100, "errors": 42, "avg_response_ms": 1950},
        {"name": "Contract Review", "artifacts": 1580, "errors": 23, "avg_response_ms": 5200},
        {"name": "Summarization", "artifacts": 980, "errors": 8, "avg_response_ms": 1200},
    ],
}

PREVIOUS_PAYLOAD = {
    "week": "2025-03-17",
    "daily_active_users": [470, 495, 488, 510, 492, 170, 62],
    "modules": [
        {"name": "Ask Lexroom", "artifacts": 11900, "errors": 210, "avg_response_ms": 2950},
        {"name": "Drafting", "artifacts": 5600, "errors": 102, "avg_response_ms": 4300},
        {"name": "Document Analysis", "artifacts": 3400, "errors": 390, "avg_response_ms": 3600},
        {"name": "Legal Research", "artifacts": 2050, "errors": 55, "avg_response_ms": 2100},
        {"name": "Contract Review", "artifacts": 1450, "errors": 35, "avg_response_ms": 5400},
        {"name": "Summarization", "artifacts": 920, "errors": 12, "avg_response_ms": 1250},
    ],
}


@pytest.fixture
def week_current_data() -> WeekData:
    return WeekData.model_validate(CURRENT_PAYLOAD)


@pytest.fixture
def week_previous_data() -> WeekData:
    return WeekData.model_validate(PREVIOUS_PAYLOAD)


@pytest.fixture
def sample_pulse_report() -> PulseReport:
    return PulseReport(
        week="2025-03-24",
        dau=DAUStats(avg_current=391.0, avg_previous=383.86, pct_change=1.86),
        top_modules=[
            ModuleRank(name="Ask Lexroom", artifacts=12350, rank=1),
            ModuleRank(name="Drafting", artifacts=5820, rank=2),
            ModuleRank(name="Document Analysis", artifacts=3200, rank=3),
        ],
        error_flags=[
            ErrorFlag(name="Document Analysis", error_rate=0.128125, errors=410, artifacts=3200),
        ],
        highlight=None,
    )


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    (tmp_path / "week_current.json").write_text(
        json.dumps(CURRENT_PAYLOAD), encoding="utf-8"
    )
    (tmp_path / "week_previous.json").write_text(
        json.dumps(PREVIOUS_PAYLOAD), encoding="utf-8"
    )
    return tmp_path
