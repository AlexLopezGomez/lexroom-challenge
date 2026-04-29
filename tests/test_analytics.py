import pytest

from weekly_pulse.analytics.compute import (
    compute_dau_stats,
    flag_error_modules,
    rank_modules,
)
from weekly_pulse.models import ModuleData, WeekData


def test_dau_pct_change_positive(week_current_data, week_previous_data):
    # Brief asserts +1.77% but actual mean math gives +1.86%.
    # current avg = 391.0, previous avg = 383.857..., delta = 1.861%.
    stats = compute_dau_stats(week_current_data, week_previous_data)
    assert stats.pct_change == pytest.approx(1.86, abs=0.01)


def test_dau_pct_change_zero_previous(week_current_data):
    previous = WeekData(
        week="2025-03-17",
        daily_active_users=[0],
        modules=week_current_data.modules,
    )
    stats = compute_dau_stats(week_current_data, previous)
    assert stats.pct_change == 0.0


def test_rank_modules_correct_order(week_current_data):
    result = rank_modules(week_current_data.modules, top_n=3)
    assert result[0].name == "Ask Lexroom"
    assert result[0].rank == 1


def test_rank_modules_top_n_exceeds_list(week_current_data):
    result = rank_modules(week_current_data.modules, top_n=100)
    assert len(result) == len(week_current_data.modules)


def test_rank_modules_empty_input():
    result = rank_modules([], top_n=3)
    assert result == []


def test_error_flags_above_threshold(week_current_data):
    flags = flag_error_modules(week_current_data.modules, threshold=0.05)
    names = [f.name for f in flags]
    assert "Document Analysis" in names


def test_error_flags_none_above_threshold(week_current_data):
    flags = flag_error_modules(week_current_data.modules, threshold=1.0)
    assert flags == []


def test_error_flags_zero_artifact_module_excluded():
    module = ModuleData(name="Empty", artifacts=0, errors=10, avg_response_ms=100)
    flags = flag_error_modules([module], threshold=0.0)
    assert flags == []
