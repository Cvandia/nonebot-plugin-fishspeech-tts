from nonebot import get_driver, on_command, on_regex
from nonebot.adapters import Message
from nonebot.rule import to_me
from nonebot_plugin_alconna import Reply, Text, UniMessage, UniMsg

from .config import config
from .exception import APIException
from .fish_audio_api import FishAudioAPI
from .fish_speech_api import FishSpeechAPI
from .request_params import ChunkLength

is_online = config.tts_is_online  # True 为在线模式，False 为本地模式
prefix = (
    config.tts_prefix
    if config.tts_prefix
    else next(iter(get_driver().config.command_start))
)  # 命令前缀

CHUNKLENGTH_MAP = {
    "normal": ChunkLength.NORMAL,
    "short": ChunkLength.SHORT,
    "long": ChunkLength.LONG,
}

chunk_length = CHUNKLENGTH_MAP.get(
    config.tts_chunk_length, ChunkLength.NORMAL
)  # 请求语音长度


tts_handler = on_regex(rf"^{prefix}(.+?)说([\s\S]*)", block=False)
speaker_list = on_command(
    "语音列表", aliases={"语音角色列表"}, block=True, rule=to_me()
)
balance = on_command("语音余额", block=True, rule=to_me())


@tts_handler.handle()
async def tts_handle(message: UniMsg):
    if message.has(Reply):
        front_reply = message[Reply, 0].msg
        if isinstance(front_reply, Message):
            text = front_reply.extract_plain_text()
        elif isinstance(front_reply, str):
            text = front_reply
        else:
            text = str(front_reply)
        reply_msg = message[Text, 0].text
        speaker = reply_msg.split("说", 1)[0]
    else:
        speaker, text = (message[Text, 0].text).split("说", 1)
        speaker = speaker.replace(prefix, "").strip()  # 去除前缀

    try:
        fish_audio_api = FishAudioAPI()
        fish_speech_api = FishSpeechAPI()
        if is_online:
            await tts_handler.send("正在通过在线api合成语音, 请稍等")
            request = await fish_audio_api.generate_servettsrequest(
                text, speaker, chunk_length
            )
            audio = await fish_audio_api.generate_tts(request)
        else:
            await tts_handler.send("正在通过本地api合成语音, 请稍等")
            request = await fish_speech_api.generate_servettsrequest(
                text, speaker, chunk_length
            )
            audio = await fish_speech_api.generate_tts(request)
        await UniMessage.voice(raw=audio).finish()

    except APIException as e:
        await tts_handler.finish(str(e))


@speaker_list.handle()
async def speaker_list_handle():
    try:
        fish_audio_api = FishAudioAPI()
        fish_speech_api = FishSpeechAPI()
        if is_online:
            _list = fish_audio_api.get_speaker_list()
            await speaker_list.finish("语音角色列表: " + ", ".join(_list))
        else:
            _list = fish_speech_api.get_speaker_list()
            await speaker_list.finish("语音角色列表: " + ", ".join(_list))
    except APIException as e:
        await speaker_list.finish(str(e))


@balance.handle()
async def balance_handle():
    try:
        fish_audio_api = FishAudioAPI()
        if is_online:
            await balance.send("正在查询在线语音余额, 请稍等")
            balance_float = await fish_audio_api.get_balance()
            await balance.finish(f"语音余额为: {balance_float}")
        else:
            await balance.finish("本地api无法查询余额")
    except APIException as e:
        await balance.finish(str(e))
