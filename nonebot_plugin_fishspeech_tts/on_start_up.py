from httpx import AsyncClient, TimeoutException
from nonebot import get_driver
from nonebot.log import logger

from .config import config

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
                    logger.warning("在线API可用")
            except TimeoutException as e:
                logger.warning(f"在线API不可用: {e}\n请尝试更换API地址或配置代理")
