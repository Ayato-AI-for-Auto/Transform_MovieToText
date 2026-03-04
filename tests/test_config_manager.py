import os
import json
import pytest
from src.config_manager import ConfigManager


def test_config_manager_save_load(tmp_path):
    config_file = tmp_path / "test_config.json"
    mgr = ConfigManager(config_path=str(config_file))

    # Initial state
    assert mgr.get_api_key() == ""

    # Set and save
    mgr.set_api_key("test_key")
    mgr.set_last_model("gemini-1.5-flash")

    # Reload from new instance
    mgr2 = ConfigManager(config_path=str(config_file))
    assert mgr2.get_api_key() == "test_key"
    assert mgr2.get_last_model() == "gemini-1.5-flash"


def test_config_manager_invalid_json(tmp_path):
    config_file = tmp_path / "invalid.json"
    config_file.write_text("invalid json content")

    mgr = ConfigManager(config_path=str(config_file))
    # Should handle error and return empty dict/settings
    assert mgr.get_api_key() == ""
