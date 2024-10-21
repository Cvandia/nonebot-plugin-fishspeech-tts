from nonebot.log import logger
from pathlib import Path
from pydantic import BaseModel
from httpx import TimeoutException
from .fish_audio_api import ChunkLength
from .config import config
from .exception import APIException
import ormsgpack
import httpx
import re


class ServeReferenceAudio(BaseModel):
    """参考音频"""

    audio: bytes
    text: str


class ServeTTSRequest(BaseModel):
    """TTS请求"""

    text: str = ""
    chunk_length: int = 50
    format: str = "wav"
    mp3_bitrate: int = 64
    references: list[ServeReferenceAudio] = []
    normalize: bool = True
    opus_bitrate: int = 24
    latency: str = "normal"
    max_new_tokens: int = 50
    top_p: float = 0.7
    repetition_penalty: float = 1.0
    temperature: float = 0.7
    streaming: bool = False


class FishSpeechAPI:
    def __init__(self):
        self.api_url: str = config.tts_api_url + "/v1/tts"
        self.audio_path: str = config.tts_audio_path
        self.path_audio: Path = Path(self.audio_path)
        self.headers = {
            "content-type": "application/msgpack",
        }
        if not self.path_audio.exists():
            self.path_audio.mkdir(parents=True)
            logger.warning(f"音频文件夹{self.audio_path}不存在, 已创建")
        elif not self.path_audio.is_dir():
            raise NotADirectoryError(f"{self.audio_path}不是一个文件夹")

    def _extract_text_by_filename(self, file_name: str) -> str:
        """
        从文件名中提取文本标签

        Args:
            file_name: 文件名
        Returns:
            ref_text: 提取的文本标签
        """

        ref_text = re.sub(r"\[.*\]", "", file_name)
        ref_text = Path(ref_text).stem
        if not ref_text:
            raise ValueError(f"未能从文件名{file_name}中提取文本标签")
        return ref_text

    def _get_speaker_audio_path(self, speaker_name: str) -> list[Path]:
        """
        获取指定说话人的音频文件路径

        Args:
            speaker_name: 说话人姓名
        Returns:
            speaker_audio_path: 说话人音频文件路径列表
        """

        speaker_audio_path = []
        for audio in self.path_audio.iterdir():
            if speaker_name in audio.name and audio.suffix == ".wav":
                speaker_audio_path.append(audio)
        logger.debug(f"获取到角色的语音路劲: {speaker_audio_path}")
        if not speaker_audio_path:
            raise FileNotFoundError(f"未找到角色:{speaker_name}的音频文件")
        return speaker_audio_path

    async def generate_servettsrequest(
        self,
        text: str,
        speaker_name: str,
        chunk_length: ChunkLength = ChunkLength.NORMAL,
    ) -> ServeTTSRequest:
        """
        生成TTS请求

        Args:
            text: 文本
            speaker_name: 说话人姓名
        Returns:
            ServeTTSRequest: TTS请求
        """

        references = []
        speaker_audio_path = self._get_speaker_audio_path(speaker_name)
        for audio in speaker_audio_path:
            audio_bytes = audio.read_bytes()
            ref_text = self._extract_text_by_filename(audio.name)
            references.append(ServeReferenceAudio(audio=audio_bytes, text=ref_text))
        return ServeTTSRequest(
            text=text,
            chunk_length=chunk_length.value,
            format="wav",
            references=references,
            normalize=True,
            opus_bitrate=64,
            latency="normal",
            max_new_tokens=chunk_length.value,
            top_p=0.7,
            repetition_penalty=1.2,
            temperature=0.7,
            streaming=False,
            mp3_bitrate=64,
        )

    async def generate_tts(self, request: ServeTTSRequest) -> bytes:
        """
        获取TTS音频

        Args:
            request: TTS请求
        Returns:
            bytes: TTS音频二进制数据
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    content=ormsgpack.packb(
                        request, option=ormsgpack.OPT_SERIALIZE_PYDANTIC
                    ),  # type: ignore
                    timeout=120,
                )
                return response.content
        except TimeoutException as e:
            logger.error(f"获取TTS音频失败: {e}")
            raise APIException("获取TTS音频超时, 你的文本太长啦！")
        except Exception:
            raise APIException("获取TTS音频失败, 检查API后端")

    def get_speaker_list(self) -> list[str]:
        """
        获取说话人列表

        Returns:
            list[str]: 说话人列表
        """
        speaker_list = []
        path_audio = self.path_audio
        for audio in path_audio.iterdir():
            if audio.suffix == ".wav":
                speaker_name = re.search(r"\[(.*)\]", audio.stem)
                if speaker_name:
                    speaker_list.append(speaker_name.group(1))
        # 去重
        speaker_list = list(set(speaker_list))
        if not speaker_list:
            raise FileNotFoundError("未找到说话人音频文件")
        return speaker_list


fish_speech_api = FishSpeechAPI()
