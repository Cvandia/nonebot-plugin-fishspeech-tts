from arclet.alconna import Alconna, Arparma, CommandMeta
from nonebot import get_driver
from nonebot.adapters import Message
from nonebot.rule import to_me
from nonebot_plugin_alconna import OriginalUniMsg, Reply, UniMessage, on_alconna

from .config import config
from .exception import APIException
from .fish_audio_api import FishAudioAPI
from .fish_speech_api import FishSpeechAPI
from .request_params import ChunkLength

is_online = config.tts_is_online  # True 为在线模式，False 为本地模式
prefixes = (
    [config.tts_prefix]
    if config.tts_prefix is not None
    else sorted(get_driver().config.command_start)
)

CHUNKLENGTH_MAP = {
    "normal": ChunkLength.NORMAL,
    "short": ChunkLength.SHORT,
    "long": ChunkLength.LONG,
}

chunk_length = CHUNKLENGTH_MAP.get(
    config.tts_chunk_length, ChunkLength.NORMAL
)  # 请求语音长度

tts_handler = on_alconna(
    Alconna(
        prefixes,
        r"re:(?P<speaker>.+?)说(?P<text>[\s\S]*)",
        # Treat the entire script as text, preserving spaces, quotes and cues.
        separators=("\0",),
        meta=CommandMeta(description="角色语音合成", keep_crlf=True),
    ),
    use_cmd_start=False,
    use_cmd_sep=False,
    auto_send_output=False,
    priority=15,
)
speaker_list = on_alconna(
    "语音列表",
    aliases={"语音角色列表"},
    use_cmd_start=True,
    auto_send_output=False,
    block=True,
    rule=to_me(),
)
balance = on_alconna(
    "语音余额",
    aliases={"我的余额"},
    use_cmd_start=True,
    auto_send_output=False,
    block=True,
    rule=to_me(),
)


@tts_handler.handle()
async def tts_handle(result: Arparma, message: OriginalUniMsg):
    speaker = result.header["speaker"]
    text = result.header["text"]
    if message.has(Reply):
        front_reply = message[Reply, 0].msg
        if isinstance(front_reply, Message):
            text = front_reply.extract_plain_text()
        elif isinstance(front_reply, str):
            text = front_reply
        else:
            text = None

    if not text or not text.strip():
        await tts_handler.finish("请输入需要合成的文本，或回复包含文本的消息")

    try:
        if is_online:
            await tts_handler.send("正在通过在线api合成语音, 请稍等")
            request = await FishAudioAPI.generate_servettsrequest(
                text, speaker, chunk_length
            )
            audio = await FishAudioAPI.generate_tts(request)
        else:
            await tts_handler.send("正在通过本地api合成语音, 请稍等")
            request = FishSpeechAPI.generate_servettsrequest(
                text, speaker, chunk_length
            )
            audio = await FishSpeechAPI.generate_tts(request)
        await UniMessage.voice(raw=audio).finish()

    except APIException as e:
        await tts_handler.finish(str(e))


@speaker_list.handle()
async def speaker_list_handle():
    try:
        if is_online:
            _list = FishAudioAPI.get_speaker_list()
            await speaker_list.finish("语音角色列表: " + ", ".join(_list))
        else:
            _list = FishSpeechAPI.get_speaker_list()
            await speaker_list.finish("语音角色列表: " + ", ".join(_list))
    except APIException as e:
        await speaker_list.finish(str(e))


@balance.handle()
async def balance_handle():
    try:
        if is_online:
            await balance.send("正在查询在线语音余额, 请稍等")
            balance_float = await FishAudioAPI.get_balance()
            await balance.finish(f"语音余额为: {balance_float}")
        else:
            await balance.finish("本地api无需查询余额")
    except APIException as e:
        await balance.finish(str(e))
