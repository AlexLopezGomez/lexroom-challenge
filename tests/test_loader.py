import json

import pytest
from pydantic import ValidationError

from weekly_pulse.loaders.json_loader import JSONFileLoader


def test_load_valid_files(tmp_data_dir):
    loader = JSONFileLoader()
    current, previous = loader.load(tmp_data_dir)
    assert current.week == "2025-03-24"
    assert previous.week == "2025-03-17"


def test_load_missing_current_file(tmp_data_dir):
    (tmp_data_dir / "week_current.json").unlink()
    loader = JSONFileLoader()
    with pytest.raises(FileNotFoundError):
        loader.load(tmp_data_dir)


def test_load_missing_previous_file(tmp_data_dir):
    (tmp_data_dir / "week_previous.json").unlink()
    loader = JSONFileLoader()
    with pytest.raises(FileNotFoundError):
        loader.load(tmp_data_dir)


def test_load_malformed_json(tmp_data_dir):
    (tmp_data_dir / "week_current.json").write_text("{not json", encoding="utf-8")
    loader = JSONFileLoader()
    with pytest.raises(ValueError):
        loader.load(tmp_data_dir)


def test_load_negative_dau_rejected(tmp_data_dir):
    data = json.loads(
        (tmp_data_dir / "week_current.json").read_text(encoding="utf-8")
    )
    data["daily_active_users"][0] = -1
    (tmp_data_dir / "week_current.json").write_text(
        json.dumps(data), encoding="utf-8"
    )
    loader = JSONFileLoader()
    with pytest.raises(ValidationError):
        loader.load(tmp_data_dir)
