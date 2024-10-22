from pydantic import BaseModel
from pydantic.fields import Field
from typing import Annotated
from typing import Literal
import enum


class ChunkLength(enum.Enum):
    SHORT = 100
    NORMAL = 200
    LONG = 300
    EXTRA_LONG = 500

    def __str__(self):
        return str(self.value)


class ServeReferenceAudio(BaseModel):
    """参考音频"""

    audio: bytes
    text: str


class ServeTTSRequest(BaseModel):
    """TTS请求"""

    text: str = ""  # 待合成文本
    chunk_length: Annotated[int, Field(ge=100, le=300, strict=True)] = 200  # 分片长度
    format: Literal["wav", "pcm", "mp3"] = "mp3"  # 音频格式
    mp3_bitrate: Literal[64, 128, 192] = 64  # mp3比特率
    references: list[ServeReferenceAudio] = []  # 参考音频
    reference_id: str | None = None  # 参考音频id
    normalize: bool = True  # 是否归一化
    opus_bitrate: int = 24  # opus比特率
    latency: Literal["normal", "balanced"] = "normal"  # 延迟
    max_new_tokens: int = 500  # 最大新令牌数
    top_p: float = 0.7  # top_p
    repetition_penalty: float = 1.0  # 重复惩罚
    temperature: float = 0.7  # 温度
    streaming: bool = False  # 是否流式传输
