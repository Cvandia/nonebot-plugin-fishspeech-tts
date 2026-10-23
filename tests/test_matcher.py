from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.exception import FinishedException
from nonebot_plugin_alconna import AlconnaMatcher, Reply, UniMessage

from nonebot_plugin_fishspeech_tts import matcher
from nonebot_plugin_fishspeech_tts.exception import APIException
from nonebot_plugin_fishspeech_tts.request_params import ServeTTSRequest


def parse_tts(message):
    result = matcher.tts_handler.command().parse(message)
    assert result.matched, result.error_info
    return result


@pytest.mark.parametrize("text", [None, "", "   "])
async def test_empty_input_finishes_with_text(monkeypatch, text):
    finish = AsyncMock(side_effect=FinishedException)
    synthesize = AsyncMock()
    monkeypatch.setattr(matcher.tts_handler, "finish", finish)
    monkeypatch.setattr(matcher.FishAudioAPI, "generate_tts", synthesize)
    message = UniMessage.text(f"/角色说{text or ''}")
    with pytest.raises(FinishedException):
        await matcher.tts_handle(parse_tts(message), message)
    assert "请输入" in finish.call_args.args[0]
    synthesize.assert_not_awaited()


@pytest.mark.parametrize(
    "text",
    [
        "[轻声]你好",
        "[激情]咕咕嘎嘎！",
        "[excited]你好 & &#91;原文&#93;",
        '[whispering] hello  world "quoted"',
        "[轻声]第一行\n[激情]第二行",
        "[excited]我说你说他说",
        "[happy] {name} $(name) --help -s 2",
    ],
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
    message = UniMessage.of(message=incoming, adapter="OneBot V11")
    with pytest.raises(FinishedException):
        await matcher.tts_handle(parse_tts(message), message)
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
    message = UniMessage.text("/角色说你好")
    with pytest.raises(FinishedException):
        await matcher.tts_handle(parse_tts(message), message)
    finish.assert_awaited_once_with("API 余额不足")


@pytest.mark.parametrize("prefix", ["/", "!"])
def test_all_command_start_prefixes(prefix):
    result = parse_tts(UniMessage.text(f"{prefix}臭企鹅说[激情]咕咕嘎嘎！"))
    assert result.header == {"speaker": "臭企鹅", "text": "[激情]咕咕嘎嘎！"}


@pytest.mark.parametrize("command", ["可莉说你好", "/说你好", "/你好", "/语音列表"])
def test_unrelated_or_unprefixed_messages_do_not_match(command):
    assert not matcher.tts_handler.command().parse(UniMessage.text(command)).matched


@pytest.mark.parametrize(
    ("handler", "name"),
    [
        (matcher.speaker_list, "语音列表"),
        (matcher.speaker_list, "语音角色列表"),
        (matcher.balance, "语音余额"),
        (matcher.balance, "我的余额"),
    ],
)
@pytest.mark.parametrize("prefix", ["/", "!"])
def test_list_and_balance_alconna_commands(handler, name, prefix):
    assert issubclass(handler, AlconnaMatcher)
    assert handler.command().parse(UniMessage.text(prefix + name)).matched


@pytest.mark.parametrize(
    "reply", ["[轻声]回复正文", Message(MessageSegment.text("[激情]回复正文"))]
)
async def test_reply_text_takes_precedence(monkeypatch, reply):
    prepare = AsyncMock(side_effect=FinishedException)
    monkeypatch.setattr(matcher, "is_online", True)
    monkeypatch.setattr(matcher.tts_handler, "send", AsyncMock())
    monkeypatch.setattr(matcher.FishAudioAPI, "generate_servettsrequest", prepare)
    command = UniMessage.text("/可莉说忽略这段正文")
    original = UniMessage(Reply("123", reply)) + command
    with pytest.raises(FinishedException):
        await matcher.tts_handle(parse_tts(command), original)
    expected = reply.extract_plain_text() if isinstance(reply, Message) else reply
    assert prepare.call_args.args[:2] == (expected, "可莉")


async def test_offline_synthesis_uses_alconna_result(monkeypatch):
    prepare = Mock(side_effect=FinishedException)
    monkeypatch.setattr(matcher, "is_online", False)
    monkeypatch.setattr(matcher.tts_handler, "send", AsyncMock())
    monkeypatch.setattr(matcher.FishSpeechAPI, "generate_servettsrequest", prepare)
    message = UniMessage.text("/可莉说[轻声]你好")
    with pytest.raises(FinishedException):
        await matcher.tts_handle(parse_tts(message), message)
    assert prepare.call_args.args[:2] == ("[轻声]你好", "可莉")
