from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.exception import FinishedException
from nonebot_plugin_alconna import UniMessage

from nonebot_plugin_fishspeech_tts import matcher
from nonebot_plugin_fishspeech_tts.exception import APIException
from nonebot_plugin_fishspeech_tts.request_params import ServeTTSRequest


@pytest.mark.parametrize("text", [None, "", "   "])
async def test_empty_input_finishes_with_text(monkeypatch, text):
    finish = AsyncMock(side_effect=FinishedException)
    synthesize = AsyncMock()
    monkeypatch.setattr(matcher.tts_handler, "finish", finish)
    monkeypatch.setattr(matcher.FishAudioAPI, "generate_tts", synthesize)
    with pytest.raises(FinishedException):
        await matcher.tts_handle(UniMessage.text(f"/角色说{text or ''}"))
    assert "请输入" in finish.call_args.args[0]
    synthesize.assert_not_awaited()


@pytest.mark.parametrize(
    "text", ["[轻声]你好", "[激情]咕咕嘎嘎！", "[excited]你好 & &#91;原文&#93;"]
)
async def test_synthesis_sends_voice_with_directions(monkeypatch, text):
    request = ServeTTSRequest(text=text, reference_id="voice-id")
    prepare = AsyncMock(return_value=request)
    synthesize = AsyncMock(return_value=b"audio-result")
    voice_finish = AsyncMock(side_effect=FinishedException)
    monkeypatch.setattr(matcher, "is_online", True)
    monkeypatch.setattr(matcher.tts_handler, "send", AsyncMock())
    monkeypatch.setattr(matcher.FishAudioAPI, "generate_servettsrequest", prepare)
    monkeypatch.setattr(matcher.FishAudioAPI, "generate_tts", synthesize)
    monkeypatch.setattr(
        matcher.UniMessage,
        "voice",
        lambda **kwargs: SimpleNamespace(finish=voice_finish)
        if kwargs["raw"] == b"audio-result"
        else None,
    )
    incoming = Message(MessageSegment.text(f"/角色说{text}"))
    assert "&#91;" in str(incoming)
    message = UniMessage.generate_sync(message=incoming, adapter="OneBot V11")
    with pytest.raises(FinishedException):
        await matcher.tts_handle(message)
    assert prepare.call_args.args[:2] == (text, "角色")
    synthesize.assert_awaited_once_with(request)
    voice_finish.assert_awaited_once()


async def test_api_error_finishes_with_text(monkeypatch):
    finish = AsyncMock(side_effect=FinishedException)
    monkeypatch.setattr(matcher, "is_online", True)
    monkeypatch.setattr(matcher.tts_handler, "send", AsyncMock())
    monkeypatch.setattr(matcher.tts_handler, "finish", finish)
    monkeypatch.setattr(
        matcher.FishAudioAPI,
        "generate_servettsrequest",
        AsyncMock(side_effect=APIException("API 余额不足")),
    )
    with pytest.raises(FinishedException):
        await matcher.tts_handle(UniMessage.text("/角色说你好"))
    finish.assert_awaited_once_with("API 余额不足")
