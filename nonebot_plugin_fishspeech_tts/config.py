from typing import Literal

from nonebot import get_plugin_config
from pydantic import BaseModel, Field


class Config(BaseModel):
    # 基础配置
    tts_is_online: bool = True
    tts_chunk_length: Literal["normal", "short", "long"] = "normal"
    tts_max_new_tokens: int | None = None  # 留空时使用服务端默认值
    tts_audio_path: str = "./data/参考音频"
    tts_prefix: str | None = None
    tts_is_stream: bool = False  # 是否流式传输

    # 区分配置
    online_api_url: str = "https://api.fish.audio"
    online_authorization: str | None = None
    online_model: Literal["s1", "s2-pro", "s2.1-pro", "s2.1-pro-free", "drama-3"] = (
        "s2.1-pro"
    )
    online_language: str | None = Field(
        default=None, max_length=35, pattern=r"^[A-Za-z0-9_-]*$"
    )
    online_reference_ids: dict[str, str] = Field(default_factory=dict)
    online_model_first: bool = True
    # 设置代理地址
    online_api_proxy: str | None = None

    offline_api_url: str = "http://127.0.0.1:8080"
    offline_authorization: str | None = None
    offline_reference_ids: dict[str, str] = Field(default_factory=dict)
    offline_single_chunk: bool = False  # 仅 Drama 3 使用


config = get_plugin_config(Config)
