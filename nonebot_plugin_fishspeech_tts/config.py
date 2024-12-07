from typing import Literal, Optional

from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    # 基础配置
    tts_is_online: bool = True
    tts_chunk_length: Literal["normal", "short", "long"] = "normal"
    tts_max_new_tokens: int = 800  # 大约6秒
    tts_audio_path: str = "./data/参考音频"
    tts_prefix: Optional[str] = None
    tts_is_stream: bool = False  # 是否流式传输

    # 区分配置
    online_api_url: str = "https://api.fish-audio.cn"
    online_authorization: Optional[str] = "xxxxx"
    online_model_first: bool = True
    # 设置代理地址
    online_api_proxy: Optional[str] = None

    offline_api_url: str = "http://127.0.0.1:8000"


config = get_plugin_config(Config)
