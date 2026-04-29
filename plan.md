# Weekly Pulse Bot — Implementation Plan

This plan is the **authoritative source** for implementation. It supersedes any conflicting instructions in the original brief. The implementing agent should read this end-to-end before touching code.

---

## MANDATORY: `SOLUTION.md` — AI usage documentation

**This is a hard deliverable, not optional.** The project brief explicitly requires:

> "If you use AI tools to write code, explicitly state this: it's not a problem — in fact, we want to understand how you use them, not whether you use them."

You (the implementing agent) **must create `SOLUTION.md`** at the project root (`weekly-pulse-bot/SOLUTION.md`) as a final step, after all code and tests are working. Do not write it first and forget to update it — write it last so it accurately reflects what actually happened.

### What `SOLUTION.md` must contain

1. **AI tools used**: list every tool by name (e.g. Claude Code, Claude claude-opus-4-7, etc.).
2. **How they were used — be specific and honest**:
   - Was the plan provided to you, or did you derive it yourself?
   - Which files did you write entirely via AI generation vs. manually adjusted?
   - Where did you use AI to look up API shapes, catch bugs, or resolve ambiguity?
   - Did any AI-suggested code need correction? If so, what and why?
3. **What you would have done differently without AI**: mention which parts — the boilerplate, the research on OpenAI Responses API, the Pydantic v2 patterns — would have taken longer or required external docs.
4. **Honest assessment**: if any part of the code is AI-generated and you are not fully confident in it, say so. The evaluator values transparency.

### Format guidance

- Plain prose. No bullet-soup. 3–6 paragraphs is the right length.
- Do not write marketing copy about AI. Write a factual engineering retrospective.
- First person ("I used...", "The agent generated...", "I verified by...").

### Non-negotiable: add it to the project structure

`SOLUTION.md` must appear in the file tree at project root alongside `README.md`. It must be tracked in the final deliverable.

---

## 0. Top-Level Overrides (read first)

These are deliberate deviations from the original brief. They are non-negotiable.

### 0.1 LLM provider switch: OpenAI, not Anthropic

The original brief specifies the Anthropic SDK and a Claude model. **Use OpenAI instead.**

| Brief said | Use |
|---|---|
| `anthropic>=0.30` dependency | `openai>=2.0` |
| `ANTHROPIC_API_KEY` env var | `OPENAI_API_KEY` |
| `LLM_MODEL = "claude-sonnet-4-20250514"` | `LLM_MODEL = "gpt-5.4-nano-2026-03-17"` |
| `client.messages.create(...)` with `system=` | `client.responses.create(...)` with `instructions=` |
| Catch `anthropic.APIError`, etc. | Catch `openai.APIError`, `openai.APITimeoutError`, `openai.APIConnectionError`, `openai.RateLimitError` |
| `max_tokens=120` | `max_output_tokens=120` |

`gpt-5.4-nano-2026-03-17` is a **non-reasoning** GPT-5.4 family model released 2026-03-17. It's chosen specifically because:
- No reasoning-token tax — `max_output_tokens=120` is fully available for visible output.
- Lower latency (matters under the 10s timeout).
- No `reasoning={"effort": ...}` parameter needed — simpler call.

### 0.2 DAU pct_change test value correction

The original brief asserts `pct_change ≈ +1.77%` in `test_dau_pct_change_positive`. **This is wrong.** Correct calculation with the spec'd fixture data:

```
current  = [482, 510, 498, 523, 501, 165, 58]   sum = 2737   avg = 391.0
previous = [470, 495, 488, 510, 492, 170, 62]   sum = 2687   avg = 383.857142857...
pct_change = (391.0 - 383.857142857) / 383.857142857 * 100 = 1.8609...%
```

Implement `compute_dau_stats` correctly. The test asserts `pytest.approx(1.86, abs=0.01)`. Add a one-line comment in the test referencing this correction so the discrepancy with the brief is auditable.

### 0.3 Other plan-level decisions

1. **hatchling needs explicit package discovery** for src layout. Add `[tool.hatch.build.targets.wheel] packages = ["src/weekly_pulse"]` to `pyproject.toml`. Without this, `uv build`/`uv sync` will fail or produce an empty wheel.
2. **Enforce zero-warning pytest** via `[tool.pytest.ini_options] filterwarnings = ["error"]`. Brief requires "no warnings"; this is the only way to actually catch them.
3. **DELIVERY_MODE=webhook + SLACK_WEBHOOK_URL=None** is unspecified in the brief. Raise `ValueError("SLACK_WEBHOOK_URL is required when DELIVERY_MODE='webhook'")` at orchestrator dispatch time before any work is done.
4. **Logging**: call `logging.basicConfig(level=logging.INFO)` once inside `main()` only. Never at module import. Otherwise warnings (e.g. "LLM unavailable") vanish silently.
5. **Date validation for `WeekData.week`**: keep field as `str`. Add a `field_validator("week")` that calls `datetime.date.fromisoformat(v)` and returns the str unchanged. This validates ISO-8601 shape without changing the type contract.

---

## 1. Project structure

Create at the working directory root:

```
weekly-pulse-bot/
├── src/
│   └── weekly_pulse/
│       ├── __init__.py
│       ├── main.py
│       ├── models.py
│       ├── config.py
│       ├── loaders/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   └── json_loader.py
│       ├── analytics/
│       │   ├── __init__.py
│       │   └── compute.py
│       ├── llm/
│       │   ├── __init__.py
│       │   └── highlight.py
│       ├── formatters/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   └── slack.py
│       └── delivery/
│           ├── __init__.py
│           ├── base.py
│           ├── console.py
│           └── webhook.py
├── data/
│   ├── week_current.json
│   └── week_previous.json
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_analytics.py
│   ├── test_loader.py
│   ├── test_formatter.py
│   └── test_integration.py
├── .env.example
├── pyproject.toml
├── README.md
└── SOLUTION.md
```

All `__init__.py` files are empty unless re-exports demonstrably help (they don't here).

---

## 2. `pyproject.toml`

```toml
[project]
name = "weekly-pulse-bot"
version = "0.1.0"
description = "Weekly product usage pulse bot with LLM-generated highlight."
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "pydantic>=2.0",
  "pydantic-settings>=2.0",
  "openai>=2.0",
  "httpx>=0.27",
]

[project.scripts]
weekly-pulse = "weekly_pulse.main:main"

[dependency-groups]
dev = [
  "pytest>=8.0",
  "pytest-mock>=3.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/weekly_pulse"]

[tool.pytest.ini_options]
filterwarnings = ["error"]
testpaths = ["tests"]
```

Notes:
- `openai>=2.0` is required for the Responses API surface used here.
- `httpx` is technically transitive (openai depends on it) but pin it explicitly because `webhook.py` uses it directly.
- `filterwarnings = ["error"]` will fail the build on any DeprecationWarning. Avoid `min_items=` (use `min_length=`), avoid bare datetime usage.

---

## 3. Data files

### `data/week_current.json`
```json
{
  "week": "2025-03-24",
  "daily_active_users": [482, 510, 498, 523, 501, 165, 58],
  "modules": [
    {"name": "Ask Lexroom", "artifacts": 12350, "errors": 187, "avg_response_ms": 2840},
    {"name": "Drafting", "artifacts": 5820, "errors": 95, "avg_response_ms": 4120},
    {"name": "Document Analysis", "artifacts": 3200, "errors": 410, "avg_response_ms": 3500},
    {"name": "Legal Research", "artifacts": 2100, "errors": 42, "avg_response_ms": 1950},
    {"name": "Contract Review", "artifacts": 1580, "errors": 23, "avg_response_ms": 5200},
    {"name": "Summarization", "artifacts": 980, "errors": 8, "avg_response_ms": 1200}
  ]
}
```

### `data/week_previous.json`
```json
{
  "week": "2025-03-17",
  "daily_active_users": [470, 495, 488, 510, 492, 170, 62],
  "modules": [
    {"name": "Ask Lexroom", "artifacts": 11900, "errors": 210, "avg_response_ms": 2950},
    {"name": "Drafting", "artifacts": 5600, "errors": 102, "avg_response_ms": 4300},
    {"name": "Document Analysis", "artifacts": 3400, "errors": 390, "avg_response_ms": 3600},
    {"name": "Legal Research", "artifacts": 2050, "errors": 55, "avg_response_ms": 2100},
    {"name": "Contract Review", "artifacts": 1450, "errors": 35, "avg_response_ms": 5400},
    {"name": "Summarization", "artifacts": 920, "errors": 12, "avg_response_ms": 1250}
  ]
}
```

---

## 4. `src/weekly_pulse/models.py`

Pydantic v2. All fields explicitly typed (no `Any`). Every public class has a one-line docstring.

- **`ModuleData`**:
  - `name: str`
  - `artifacts: int = Field(ge=0)`
  - `errors: int = Field(ge=0)`
  - `avg_response_ms: int = Field(ge=0)`
  - Computed property `error_rate` using `@computed_field` + `@property`. Returns `errors / artifacts` if `artifacts > 0`, else `0.0`. Return type `float`.

- **`WeekData`**:
  - `week: str` with `@field_validator("week")` calling `datetime.date.fromisoformat(v)` (raises `ValueError` if malformed) — return `v` unchanged.
  - `daily_active_users: list[int] = Field(min_length=1)` with `@field_validator("daily_active_users")` rejecting any `< 0` element.
  - `modules: list[ModuleData] = Field(min_length=1)`.

- **`DAUStats`**: `avg_current: float`, `avg_previous: float`, `pct_change: float`.

- **`ModuleRank`**: `name: str`, `artifacts: int`, `rank: int`.

- **`ErrorFlag`**: `name: str`, `error_rate: float`, `errors: int`, `artifacts: int`.

- **`PulseReport`**: `week: str`, `dau: DAUStats`, `top_modules: list[ModuleRank]`, `error_flags: list[ErrorFlag]`, `highlight: str | None = None`.

Use `from __future__ import annotations` at the top of the file.

---

## 5. `src/weekly_pulse/config.py`

```python
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    """Runtime configuration loaded from environment variables / .env."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    OPENAI_API_KEY: str | None = None
    SLACK_WEBHOOK_URL: str | None = None
    DELIVERY_MODE: Literal["console", "webhook"] = "console"
    ERROR_RATE_THRESHOLD: float = 0.05
    TOP_N_MODULES: int = 3
    LLM_MODEL: str = "gpt-5.4-nano-2026-03-17"
    LLM_TIMEOUT_SECONDS: float = 10.0
    DATA_DIR: Path = Path("data")
```

---

## 6. Loader layer

### `loaders/base.py`
Abstract `DataLoader` with `@abstractmethod load(source: Any) -> tuple[WeekData, WeekData]`. Returns `(current, previous)`. Use `from abc import ABC, abstractmethod`.

### `loaders/json_loader.py`
`JSONFileLoader(DataLoader)`:
- `load(source: Path | str) -> tuple[WeekData, WeekData]`:
  1. Coerce `source` to `Path`.
  2. Build `current_path = source / "week_current.json"`, `previous_path = source / "week_previous.json"`.
  3. If either file missing: `raise FileNotFoundError(f"Required data file missing: {path}")`.
  4. For each: `json.loads(path.read_text(encoding="utf-8"))` then `WeekData.model_validate(...)`.
  5. Pydantic `ValidationError` is already a `ValueError` subclass — let it propagate (the brief asks for `ValueError with field path`; Pydantic's default error message includes the path).
  6. `json.JSONDecodeError` should also propagate unwrapped. It's also a `ValueError` subclass.

No silent failures. No bare `except`.

---

## 7. Analytics layer (`analytics/compute.py`)

Pure functions. No I/O. No global state. Use `from statistics import mean`.

```python
def compute_dau_stats(current: WeekData, previous: WeekData) -> DAUStats:
    avg_current = mean(current.daily_active_users)
    avg_previous = mean(previous.daily_active_users)
    pct_change = 0.0 if avg_previous == 0 else ((avg_current - avg_previous) / avg_previous) * 100
    return DAUStats(avg_current=avg_current, avg_previous=avg_previous, pct_change=pct_change)

def rank_modules(modules: list[ModuleData], top_n: int) -> list[ModuleRank]:
    sorted_modules = sorted(modules, key=lambda m: m.artifacts, reverse=True)
    return [ModuleRank(name=m.name, artifacts=m.artifacts, rank=i + 1)
            for i, m in enumerate(sorted_modules[:top_n])]

def flag_error_modules(modules: list[ModuleData], threshold: float) -> list[ErrorFlag]:
    flags = [
        ErrorFlag(name=m.name, error_rate=m.error_rate, errors=m.errors, artifacts=m.artifacts)
        for m in modules
        if m.artifacts > 0 and m.error_rate > threshold
    ]
    flags.sort(key=lambda f: f.error_rate, reverse=True)
    return flags
```

Edge cases handled:
- Empty `modules` → `[]` from both rank and flag.
- `top_n > len(modules)` → slicing gives all modules (no error).
- `modules with artifacts=0` → excluded from flags via `m.artifacts > 0` guard.
- `avg_previous == 0` → returns 0.0 instead of dividing.

---

## 8. LLM layer (`llm/highlight.py`)

```python
import logging
from openai import OpenAI, APIError, APITimeoutError, APIConnectionError, RateLimitError
from weekly_pulse.config import Config
from weekly_pulse.models import PulseReport

logger = logging.getLogger(__name__)

class LLMHighlightGenerator:
    """Generates a one-sentence highlight via OpenAI Responses API."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._client = OpenAI(api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None

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
                text={"verbosity": "low"},
                timeout=self._config.LLM_TIMEOUT_SECONDS,
            )
        except (APITimeoutError, APIConnectionError, RateLimitError, APIError) as exc:
            logger.warning("LLM call failed: %s", exc)
            return None

        text = (response.output_text or "").strip()
        return text or None

    @staticmethod
    def _build_prompt(report: PulseReport) -> str:
        top = ", ".join(f"{m.name} ({m.artifacts:,})" for m in report.top_modules)
        flags = (", ".join(f"{f.name} ({f.error_rate:.1%})" for f in report.error_flags)
                 if report.error_flags else "none")
        return (
            f"Week: {report.week}\n"
            f"Avg DAU: {report.dau.avg_current:.0f} ({report.dau.pct_change:+.1f}% vs last week)\n"
            f"Top modules by volume: {top}\n"
            f"High error rate modules: {flags}\n"
            "Write one sentence summarizing the most important signal."
        )
```

Notes:
- Catch concrete exception types in narrowing-to-broadening order. `APIError` is the umbrella; the specific subclasses are listed first for clarity in logs but the broad catch ensures *any* SDK-side failure returns `None` (per brief: "never raise").
- Don't catch `Exception` — that's a bare-catch antipattern and the brief forbids it.
- `httpx.TimeoutException` is wrapped by `openai.APITimeoutError` in modern openai SDK, so no need to catch it separately.
- Test integration will monkeypatch `LLMHighlightGenerator.generate` directly — no real network call.

---

## 9. Formatter layer

### `formatters/base.py`
Abstract `ReportFormatter` with `@abstractmethod format(report: PulseReport) -> str`.

### `formatters/slack.py` — `SlackMarkdownFormatter`

Output (exact, no trailing whitespace on any line):

```
*📊 Weekly Pulse — {week}*

*👥 Daily Active Users*
- Avg DAU: {avg_current:.0f} ({pct_change:+.1f}% vs last week)

*🏆 Top Modules by Volume*
1. {name} — {artifacts:,} artifacts
2. {name} — {artifacts:,} artifacts
3. {name} — {artifacts:,} artifacts

*⚠️ High Error Rate Modules*
- {name} — {error_rate:.1%} error rate ({errors} errors / {artifacts:,} artifacts)
[OR: ✅ No modules above error threshold this week.]

*✨ Highlight*
{highlight}
[OR: _LLM highlight unavailable._]

---
_Generated by Weekly Pulse Bot_
```

Implementation tips:
- Build with a list of lines, `"\n".join(lines)`. Don't use `+=` string concatenation in a loop.
- Use `f"{n:,}"` for thousands separators (locale-independent — uses comma).
- Use `f"{n:+.1f}%"` for pct_change to always show sign.
- Use `f"{r:.1%}"` for error_rate (gives e.g. "12.8%").
- For the top-modules section: iterate over `report.top_modules` using each item's `rank` (don't compute index — the model already has rank).

---

## 10. Delivery layer

### `delivery/base.py`
Abstract `DeliveryChannel` with `@abstractmethod deliver(message: str) -> None`.

### `delivery/console.py`
```python
class ConsoleDelivery(DeliveryChannel):
    """Writes the formatted message to stdout."""
    def deliver(self, message: str) -> None:
        print(message)
```
This is the **only** allowed `print()` call outside tests.

### `delivery/webhook.py`
```python
import httpx

class WebhookDelivery(DeliveryChannel):
    """Posts the formatted message as JSON to a Slack-compatible webhook."""
    def __init__(self, webhook_url: str) -> None:
        self._webhook_url = webhook_url

    def deliver(self, message: str) -> None:
        response = httpx.post(self._webhook_url, json={"text": message}, timeout=5.0)
        if not (200 <= response.status_code < 300):
            raise RuntimeError(f"Webhook delivery failed with status {response.status_code}")
```

No retry logic. Brief explicitly says no retry needed for prototype.

---

## 11. Orchestrator (`main.py`)

```python
import logging
from weekly_pulse.config import Config
from weekly_pulse.loaders.json_loader import JSONFileLoader
from weekly_pulse.analytics.compute import compute_dau_stats, rank_modules, flag_error_modules
from weekly_pulse.llm.highlight import LLMHighlightGenerator
from weekly_pulse.formatters.slack import SlackMarkdownFormatter
from weekly_pulse.delivery.base import DeliveryChannel
from weekly_pulse.delivery.console import ConsoleDelivery
from weekly_pulse.delivery.webhook import WebhookDelivery
from weekly_pulse.models import PulseReport

logger = logging.getLogger(__name__)

def _build_delivery(config: Config) -> DeliveryChannel:
    if config.DELIVERY_MODE == "console":
        return ConsoleDelivery()
    if not config.SLACK_WEBHOOK_URL:
        raise ValueError("SLACK_WEBHOOK_URL is required when DELIVERY_MODE='webhook'")
    return WebhookDelivery(config.SLACK_WEBHOOK_URL)

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
    report.highlight = generator.generate(report)

    formatted = SlackMarkdownFormatter().format(report)
    delivery = _build_delivery(config)
    delivery.deliver(formatted)

def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run(Config())

if __name__ == "__main__":
    main()
```

Note `report.highlight = generator.generate(report)` requires `PulseReport` to allow assignment — Pydantic v2 defaults to immutable. Add `model_config = ConfigDict(validate_assignment=False)` to `PulseReport`, OR re-construct with `model_copy(update={"highlight": ...})`. **Prefer the latter** — it's cleaner and avoids fiddling with model config:

```python
report = report.model_copy(update={"highlight": generator.generate(report)})
```

Update the orchestrator to use `model_copy` instead of attribute assignment.

---

## 12. Tests

### `tests/conftest.py`

Fixtures:
- `week_current_data() -> WeekData`: built directly from the JSON payload values.
- `week_previous_data() -> WeekData`: same.
- `sample_pulse_report() -> PulseReport`: known-value report for formatter tests. Use stable values, e.g. week="2025-03-24", `dau=DAUStats(avg_current=391.0, avg_previous=383.86, pct_change=1.86)`, two top modules, one error flag, `highlight=None`.
- `tmp_data_dir(tmp_path) -> Path`: writes both JSON files into `tmp_path` using the spec'd content. Return `tmp_path`.

### `tests/test_analytics.py`

```python
def test_dau_pct_change_positive(week_current_data, week_previous_data):
    # Brief asserts +1.77% but actual mean math gives +1.86%.
    # current avg = 391.0, previous avg = 383.857..., delta = 1.861%.
    stats = compute_dau_stats(week_current_data, week_previous_data)
    assert stats.pct_change == pytest.approx(1.86, abs=0.01)
```

Other tests as in the brief — all unambiguous:
- `test_dau_pct_change_zero_previous`: build a `WeekData` with `daily_active_users=[0]` for previous → pct_change == 0.0.
- `test_rank_modules_correct_order`: result[0].name == "Ask Lexroom", result[0].rank == 1.
- `test_rank_modules_top_n_exceeds_list`: `top_n=100` with 6 modules → len == 6.
- `test_rank_modules_empty_input`: `[]` → `[]`.
- `test_error_flags_above_threshold`: with default threshold 0.05, "Document Analysis" present (410/3200 ≈ 12.8%).
- `test_error_flags_none_above_threshold`: threshold=1.0 → `[]`.
- `test_error_flags_zero_artifact_module_excluded`: build a `ModuleData(name="Empty", artifacts=0, errors=10, avg_response_ms=100)` and confirm it's excluded even with low threshold.

### `tests/test_loader.py`

- `test_load_valid_files(tmp_data_dir)`: both `WeekData` objects parse, `current.week == "2025-03-24"`.
- `test_load_missing_current_file(tmp_data_dir)`: delete `week_current.json`, expect `FileNotFoundError`.
- `test_load_missing_previous_file(tmp_data_dir)`: delete `week_previous.json`, expect `FileNotFoundError`.
- `test_load_malformed_json(tmp_data_dir)`: overwrite `week_current.json` with `"{not json"`, use `pytest.raises(ValueError)` — `JSONDecodeError` is a `ValueError` subclass and Pydantic's `ValidationError` is too, so this assertion works for either failure mode.
- `test_load_negative_dau_rejected(tmp_data_dir)`: overwrite `week_current.json` with `daily_active_users` containing `-1`, expect `pydantic.ValidationError`.

### `tests/test_formatter.py`

- `test_output_contains_week_date(sample_pulse_report)`: `"2025-03-24"` in output.
- `test_output_contains_dau_section`: `"Daily Active Users"` in output.
- `test_output_contains_top_modules_section`: build a report with 3 known module names, assert all 3 appear.
- `test_output_no_error_flags_shows_checkmark`: `error_flags=[]` → `"✅"` in output.
- `test_output_error_flags_shows_warning`: non-empty error_flags → `"⚠️"` in output.
- `test_output_highlight_shown_when_present`: `highlight="Strong week."` → that string in output.
- `test_output_highlight_unavailable_when_none`: `highlight=None` → `"_LLM highlight unavailable._"` in output.
- `test_pct_change_shows_sign`: positive → `"+"` prefix in DAU line; build a second report with negative pct_change, assert `"-"` prefix.

### `tests/test_integration.py`

- `test_full_pipeline_console_output(tmp_data_dir, capsys, monkeypatch)`:
  ```python
  monkeypatch.setattr(LLMHighlightGenerator, "generate", lambda self, r: "Strong week across all modules.")
  config = Config(DATA_DIR=tmp_data_dir, OPENAI_API_KEY="fake", DELIVERY_MODE="console")
  run(config)
  out = capsys.readouterr().out
  assert "Weekly Pulse" in out and "Strong week across all modules." in out and "✅" not in out  # error flag exists
  ```
  (Adjust the `✅`/`⚠️` assertion to match what the spec'd data produces — Document Analysis will trigger a flag, so `⚠️` should be present.)

- `test_full_pipeline_no_api_key(tmp_data_dir, capsys, monkeypatch)`:
  ```python
  monkeypatch.delenv("OPENAI_API_KEY", raising=False)
  config = Config(DATA_DIR=tmp_data_dir, OPENAI_API_KEY=None, DELIVERY_MODE="console")
  run(config)
  out = capsys.readouterr().out
  assert "_LLM highlight unavailable._" in out
  ```

---

## 13. `.env.example`

```
OPENAI_API_KEY=your_key_here
SLACK_WEBHOOK_URL=
DELIVERY_MODE=console
ERROR_RATE_THRESHOLD=0.05
TOP_N_MODULES=3
```

---

## 14. `README.md` — required content

1. **Quick start (≤4 commands):**
   ```
   git clone <repo>
   cd weekly-pulse-bot
   uv sync
   cp .env.example .env
   uv run weekly-pulse
   ```
2. **Environment variables table** mirroring `.env.example`. Columns: name, default, purpose.
3. **How to run tests**: `uv run pytest`.
4. **Architecture section**: describe the 4-layer pipeline (Ingestion → Computation → LLM → Formatting/Delivery). Explain why each layer is isolated:
   - Loader is swappable (JSON today, BigQuery later — same `DataLoader` interface).
   - Analytics is pure → trivially testable, deterministic.
   - LLM is best-effort with graceful fallback; the report is fully readable without it.
   - Formatter and Delivery are orthogonal: same report can render to multiple targets.
5. **What I'd do with more time**: BigQuery loader, async pipeline, Monday morning cron via GitHub Actions, multi-workspace config, structured logging with structlog.
6. **AI usage disclosure**: state Claude Code was used to scaffold this project.
7. **Note on the LLM provider switch**: explicitly mention that the LLM is OpenAI's `gpt-5.4-nano-2026-03-17` (chosen as a non-reasoning model for low-latency one-sentence summaries).

---

## 15. Hard constraints (verbatim from brief — must hold)

- **Zero `print()` calls outside `ConsoleDelivery` and tests.** Use `logging.getLogger(__name__)` everywhere else.
- **No global mutable state.**
- **No bare `except:` clauses.** Always catch specific exception types.
- **Every public function and class has a one-line docstring.**
- **All model fields explicitly typed.** No `Any` in `models.py`.
- **End-to-end runnable with only**: `uv sync && uv run weekly-pulse`.
- **`uv run pytest` passes with no warnings.** (Enforced via `filterwarnings = ["error"]`.)

---

## 16. Suggested implementation order

1. `pyproject.toml` + `.env.example` + empty package skeleton (verifies build before any logic).
2. `models.py` (everything else depends on it).
3. `config.py`.
4. `loaders/base.py` + `loaders/json_loader.py`.
5. `analytics/compute.py`.
6. `formatters/base.py` + `formatters/slack.py`.
7. `delivery/base.py` + `delivery/console.py` + `delivery/webhook.py`.
8. `llm/highlight.py`.
9. `main.py` (orchestrator wiring).
10. `data/week_current.json` + `data/week_previous.json`.
11. Tests in order: `conftest.py` → `test_analytics.py` → `test_loader.py` → `test_formatter.py` → `test_integration.py`.
12. `README.md`.
13. Final verification: `uv sync && uv run weekly-pulse` (without `OPENAI_API_KEY` — should print report with "_LLM highlight unavailable._"), then `uv run pytest` — must pass with zero warnings.
14. **`SOLUTION.md`** — write this last, after all code is working. See the mandatory section at the top of this plan.

---

## 17. Sanity-check arithmetic (for the implementer)

Use these to self-verify the analytics layer before running tests:

- `current.daily_active_users` sum = 2737, mean = 391.0
- `previous.daily_active_users` sum = 2687, mean ≈ 383.857
- `pct_change` ≈ +1.861%
- `Document Analysis` error_rate = 410/3200 = 0.128125 (12.81%) — only module above default 5% threshold
- `Ask Lexroom` artifacts = 12350 — rank 1 in current week
- Top 3 by artifacts: Ask Lexroom (12350), Drafting (5820), Document Analysis (3200)

If any of these don't match what your code computes, fix the code — not the plan.
