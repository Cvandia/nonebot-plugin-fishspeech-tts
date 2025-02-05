from httpx import AsyncClient, TimeoutException
from nonebot import get_driver
from nonebot.log import logger

from .config import config
from .fish_audio_api import FishAudioAPI

IS_ONLINE = config.tts_is_online
API = config.online_api_url

driver = get_driver()
if IS_ONLINE:

    @driver.on_startup
    async def check_online_api():
        """检查在线API是否可用"""
        async with AsyncClient() as client:
            try:
                response = await client.get(API)
                rsp_text = response.text
                if "Nothing" in rsp_text:
                    logger.success("在线API可用")
            except TimeoutException as e:
                logger.warning(f"在线API不可用: {e}\n请尝试更换API地址或配置代理")

    @driver.on_startup
    async def check_files():
        """检查音频文件夹是否存在"""
        path_audio = FishAudioAPI.path_audio
        if not path_audio.exists():
            path_audio.mkdir(parents=True)
            logger.warning(f"音频文件夹{path_audio.name}不存在, 已创建")
        elif not path_audio.is_dir():
            logger.error(f"音频文件夹{path_audio.name}存在, 但不是文件夹")
