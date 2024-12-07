from httpx import AsyncClient, HTTPStatusError
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
                response.raise_for_status()
            except HTTPStatusError as e:
                logger.warning(f"在线API不可用: {e}\n请尝试更换API地址或配置代理")
