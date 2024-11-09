from nonebot import require

require("nonebot_plugin_alconna")

from .config import Config
from . import matcher

import contextlib


usage: str = (
    """
指令：
    发送:[角色名]说[文本]即可发送TTS语音。
    发送:[语音列表]以查看支持的发音人。
    发送:[语音余额]以查看在线api余额。
""".strip()
)

with contextlib.suppress(Exception):
    from nonebot.plugin import PluginMetadata, inherit_supported_adapters

    __plugin_meta__ = PluginMetadata(
        name="FishSpeechTTS",
        description="小样本TTS,通过fish-speech调用本地或在线api发送语音",
        usage=usage,
        homepage="https://github.com/Cvandia/nonebot-plugin-fishspeech-tts",
        config=Config,
        type="application",
        supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
        extra={"author": "Cvandia", "email": "1141538825@qq.com"},
    )
