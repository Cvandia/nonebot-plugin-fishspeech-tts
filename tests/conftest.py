import nonebot
import pytest

nonebot.init(driver="~fastapi", command_start={"/"})
plugin = nonebot.load_plugin("nonebot_plugin_fishspeech_tts")
if plugin is None:
    raise RuntimeError("Fish Speech plugin failed to load")

from nonebot_plugin_fishspeech_tts.config import config


@pytest.fixture(autouse=True)
def reset_config(monkeypatch):
    monkeypatch.setattr(config, "online_authorization", "test-token")
    monkeypatch.setattr(config, "online_model", "s2.1-pro")
    monkeypatch.setattr(config, "online_language", None)
    monkeypatch.setattr(config, "online_model_first", True)
    monkeypatch.setattr(config, "online_reference_ids", {})
    monkeypatch.setattr(config, "offline_reference_ids", {})
    monkeypatch.setattr(config, "offline_authorization", None)
    monkeypatch.setattr(config, "offline_single_chunk", False)
    monkeypatch.setattr(config, "tts_max_new_tokens", None)
    monkeypatch.setattr(config, "tts_is_stream", False)
