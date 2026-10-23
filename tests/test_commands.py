import nonebot
import pytest
from arclet.alconna import command_manager
from nonebot.adapters.onebot.v11 import (
    Adapter,
    Bot,
    Message,
    MessageSegment,
    PrivateMessageEvent,
)
from nonebot_plugin_alconna import UniMessage
from nonebot_plugin_alconna.consts import ALCONNA_RESULT

from nonebot_plugin_fishspeech_tts import matcher


@pytest.mark.parametrize(
    ("handler", "command", "to_me", "expected"),
    [
        (matcher.tts_handler, "/臭企鹅说[激情]咕咕嘎嘎！", False, True),
        (matcher.tts_handler, "!可莉说[whispering] hello  world", False, True),
        (matcher.tts_handler, "/可莉说[轻声]第一行\n第二行", False, True),
        (matcher.tts_handler, "可莉说你好", False, False),
        (matcher.speaker_list, "/语音列表", True, True),
        (matcher.speaker_list, "!语音角色列表", True, True),
        (matcher.speaker_list, "/语音列表", False, False),
        (matcher.balance, "/语音余额", True, True),
        (matcher.balance, "!我的余额", True, True),
        (matcher.balance, "/语音余额", False, False),
    ],
)
async def test_real_onebot_event_rules(handler, command, to_me, expected):
    event = PrivateMessageEvent(
        time=0,
        self_id=100000,
        post_type="message",
        message_type="private",
        sub_type="friend",
        user_id=100001,
        message_id=hash((command, to_me)),
        message=Message(MessageSegment.text(command)),
        raw_message=command,
        font=0,
        sender={"user_id": 100001},
        to_me=to_me,
    )
    bot = Bot(nonebot.get_adapter(Adapter), "100000")
    state = {}
    assert await handler.rule(bot, event, state) is expected
    if expected and handler is matcher.tts_handler:
        # Verify the Alconna dependency result contains literal model cues.
        text = state[ALCONNA_RESULT].result.header["text"]
        assert text == command.split("说", 1)[1]


@pytest.mark.parametrize("prefix", ["", ".*", "[tts]"])
def test_literal_and_empty_synthesis_prefixes(prefix):
    command = matcher.tts_handler.command()
    original = command.prefixes
    try:
        with command_manager.update(command):
            command.prefixes = [prefix]
        result = command.parse(UniMessage.text(f"{prefix}可莉说[激情]你好"))
        assert result.matched
        assert result.header == {"speaker": "可莉", "text": "[激情]你好"}
    finally:
        with command_manager.update(command):
            command.prefixes = original
