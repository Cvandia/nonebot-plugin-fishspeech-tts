from nonebot import get_driver
from nonebot.log import logger

from .config import config
from .fish_audio_api import FishAudioAPI

driver = get_driver()


@driver.on_startup
async def check_files():
    """检查本地目录；不依赖云端根路径的响应正文判断 API 状态。"""
    path_audio = FishAudioAPI.path_audio
    try:
        path_audio.mkdir(parents=True, exist_ok=True)
    except OSError:
        logger.warning("无法创建参考音频目录，请检查路径及权限")
    if config.tts_is_online:
        if not config.online_authorization or config.online_authorization == "xxxxx":
            logger.warning("请配置 online_authorization 后使用在线语音合成")
        if config.online_model == "s1":
            logger.warning("S1 将于 2026-12-31 退役，建议迁移到 s2.1-pro")
