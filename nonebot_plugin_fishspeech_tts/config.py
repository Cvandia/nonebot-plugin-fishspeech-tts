from typing import Literal, Optional

from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    # 基础配置
    tts_is_online: bool = True
    tts_chunk_length: Literal["normal", "short", "long"] = "normal"
    tts_audio_path: str = "./data/参考音频"
    tts_prefix: Optional[str] = None

    # 区分配置
    online_authorization: Optional[str] = "xxxxx"
    online_model_first: bool = True
    # 设置代理地址
    online_api_proxy: Optional[str] = None

    offline_api_url: str = "http://127.0.0.1:8080"


config = get_plugin_config(Config)
