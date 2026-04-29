from statistics import mean

from weekly_pulse.models import DAUStats, ErrorFlag, ModuleData, ModuleRank, WeekData


def compute_dau_stats(current: WeekData, previous: WeekData) -> DAUStats:
    """Compute average DAU and week-over-week percentage change."""
    avg_current = mean(current.daily_active_users)
    avg_previous = mean(previous.daily_active_users)
    pct_change = (
        0.0
        if avg_previous == 0
        else ((avg_current - avg_previous) / avg_previous) * 100
    )
    return DAUStats(
        avg_current=avg_current, avg_previous=avg_previous, pct_change=pct_change
    )


def rank_modules(modules: list[ModuleData], top_n: int) -> list[ModuleRank]:
    """Return the top_n modules sorted by artifact volume descending."""
    sorted_modules = sorted(modules, key=lambda m: m.artifacts, reverse=True)
    return [
        ModuleRank(name=m.name, artifacts=m.artifacts, rank=i + 1)
        for i, m in enumerate(sorted_modules[:top_n])
    ]


def flag_error_modules(
    modules: list[ModuleData], threshold: float
) -> list[ErrorFlag]:
    """Return modules whose error rate exceeds threshold, sorted by rate descending."""
    flags = [
        ErrorFlag(
            name=m.name,
            error_rate=m.error_rate,
            errors=m.errors,
            artifacts=m.artifacts,
        )
        for m in modules
        if m.artifacts > 0 and m.error_rate > threshold
    ]
    flags.sort(key=lambda f: f.error_rate, reverse=True)
    return flags
