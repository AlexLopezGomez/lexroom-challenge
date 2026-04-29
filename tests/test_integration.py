import pytest
from openai import APITimeoutError

from weekly_pulse.config import Config
from weekly_pulse.delivery.webhook import WebhookDelivery
from weekly_pulse.llm.highlight import LLMHighlightGenerator
from weekly_pulse.main import _build_delivery, run


def test_full_pipeline_console_output(tmp_data_dir, capsys, monkeypatch):
    monkeypatch.setattr(
        LLMHighlightGenerator, "generate", lambda self, r: "Strong week across all modules."
    )
    config = Config(DATA_DIR=tmp_data_dir, OPENAI_API_KEY="fake", DELIVERY_MODE="console")
    run(config)
    out = capsys.readouterr().out
    assert "Weekly Pulse" in out
    assert "Strong week across all modules." in out
    assert "✅" not in out  # Document Analysis triggers error flag; the "no flags" fallback is absent


def test_full_pipeline_no_api_key(tmp_data_dir, capsys, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = Config(DATA_DIR=tmp_data_dir, OPENAI_API_KEY=None, DELIVERY_MODE="console")
    run(config)
    out = capsys.readouterr().out
    assert "_LLM highlight unavailable._" in out


def test_llm_api_failure_returns_none(sample_pulse_report, mocker):
    mock_client = mocker.Mock(
        responses=mocker.Mock(
            create=mocker.Mock(side_effect=APITimeoutError(request=mocker.Mock()))
        )
    )
    mocker.patch("weekly_pulse.llm.highlight.OpenAI", return_value=mock_client)
    generator = LLMHighlightGenerator(Config(OPENAI_API_KEY="fake"))
    assert generator.generate(sample_pulse_report) is None


def test_webhook_delivery_success(mocker):
    mocker.patch(
        "weekly_pulse.delivery.webhook.httpx.post",
        return_value=mocker.Mock(status_code=200),
    )
    WebhookDelivery("https://hooks.example.com/test", timeout=5.0).deliver("hello")


def test_webhook_delivery_non_2xx_raises(mocker):
    mocker.patch(
        "weekly_pulse.delivery.webhook.httpx.post",
        return_value=mocker.Mock(status_code=500),
    )
    with pytest.raises(RuntimeError, match="500"):
        WebhookDelivery("https://hooks.example.com/test", timeout=5.0).deliver("hello")


def test_build_delivery_webhook_missing_url():
    config = Config(DELIVERY_MODE="webhook", SLACK_WEBHOOK_URL=None)
    with pytest.raises(ValueError, match="SLACK_WEBHOOK_URL"):
        _build_delivery(config)
