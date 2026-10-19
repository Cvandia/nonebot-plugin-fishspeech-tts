import enum
from typing import Literal

from pydantic import BaseModel, Field


class ChunkLength(enum.Enum):
    SHORT = 100
    NORMAL = 200
    LONG = 300
    EXTRA_LONG = 500

    def __str__(self):
        return str(self.value)


class ServeReferenceAudio(BaseModel):
    """MessagePack 中直接使用音频字节，无需 Base64。"""

    audio: bytes
    text: str
    speaker: int | None = Field(default=None, ge=0, le=15)


class ServeTTSRequest(BaseModel):
    """公共参数；按目标服务剔除不支持的字段。"""

    text: str = Field(min_length=1)
    chunk_length: int = Field(default=200, ge=100, le=1000)
    format: Literal["wav", "pcm", "mp3", "opus"] = "wav"
    mp3_bitrate: Literal[64, 128, 192] = 128
    opus_bitrate: Literal[-1000, 24000, 32000, 48000, 64000] = -1000
    references: list[ServeReferenceAudio] = Field(default_factory=list)
    reference_id: str | None = None
    normalize: bool = True
    language: str | None = None
    latency: Literal["normal", "balanced", "low"] = "normal"
    max_new_tokens: int | None = None
    top_p: float | None = Field(default=None, ge=0.1, le=1)
    repetition_penalty: float | None = Field(default=None, ge=0.9, le=2)
    temperature: float | None = Field(default=None, ge=0.1, le=1)
    streaming: bool = False
    seed: int | None = None
    use_memory_cache: Literal["on", "off"] = "off"
    single_chunk: bool = False

    def to_payload(self, *, online: bool) -> dict:
        # 不发送 null，使旧版本服务端也能使用自己的默认采样参数。
        if online:
            if self.chunk_length > ChunkLength.LONG.value:
                raise ValueError("云端 chunk_length 不能超过 300")
            excluded = {"streaming", "seed", "use_memory_cache", "single_chunk"}
        else:
            excluded = {"language", "mp3_bitrate", "opus_bitrate"}
            if self.latency == "low":
                excluded.add("latency")
            if not self.single_chunk:
                excluded.add("single_chunk")
        return self.model_dump(exclude_none=True, exclude=excluded)
