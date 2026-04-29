import pytest

from weekly_pulse.formatters.slack import SlackMarkdownFormatter
from weekly_pulse.models import DAUStats, ErrorFlag, ModuleRank, PulseReport


def _make_report(**kwargs) -> PulseReport:
    defaults = dict(
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
    defaults.update(kwargs)
    return PulseReport(**defaults)


def test_output_contains_week_date(sample_pulse_report):
    out = SlackMarkdownFormatter().format(sample_pulse_report)
    assert "2025-03-24" in out


def test_output_contains_dau_section(sample_pulse_report):
    out = SlackMarkdownFormatter().format(sample_pulse_report)
    assert "Daily Active Users" in out


def test_output_contains_top_modules_section():
    report = _make_report()
    out = SlackMarkdownFormatter().format(report)
    for name in ("Ask Lexroom", "Drafting", "Document Analysis"):
        assert name in out


def test_output_no_error_flags_shows_checkmark():
    report = _make_report(error_flags=[])
    out = SlackMarkdownFormatter().format(report)
    assert "✅" in out


def test_output_error_flags_shows_warning():
    report = _make_report()
    out = SlackMarkdownFormatter().format(report)
    assert "⚠️" in out


def test_output_highlight_shown_when_present():
    report = _make_report(highlight="Strong week.")
    out = SlackMarkdownFormatter().format(report)
    assert "Strong week." in out


def test_output_highlight_unavailable_when_none():
    report = _make_report(highlight=None)
    out = SlackMarkdownFormatter().format(report)
    assert "_LLM highlight unavailable._" in out


def test_pct_change_shows_sign():
    positive = _make_report(dau=DAUStats(avg_current=391.0, avg_previous=383.86, pct_change=1.86))
    out_pos = SlackMarkdownFormatter().format(positive)
    assert "+" in out_pos

    negative = _make_report(dau=DAUStats(avg_current=380.0, avg_previous=391.0, pct_change=-2.81))
    out_neg = SlackMarkdownFormatter().format(negative)
    assert "-" in out_neg
