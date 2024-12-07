from pathlib import Path

import ormsgpack
from httpx import (
    AsyncClient,
    HTTPStatusError,
    RequestError,
)
from nonebot.log import logger

from .config import config
from .exception import APIException, FileHandleException, HTTPException
from .files import (
    extract_text_by_filename,
    get_path_speaker_list,
    get_speaker_audio_path,
)
from .request_params import ChunkLength, ServeReferenceAudio, ServeTTSRequest

API_URL = config.offline_api_url + "/v1/tts"
PATH_AUDIO = Path(config.tts_audio_path)
MAX_NEW_TOKENS = config.tts_max_new_tokens
IS_STREAM = config.tts_is_stream


class FishSpeechAPI:
    def __init__(self):
        self.api_url: str = API_URL
        self.path_audio: Path = PATH_AUDIO
        self.headers = {
            "content-type": "application/msgpack",
        }

        # 如果音频文件夹不存在, 则创建音频文件夹
        if not self.path_audio.exists():
            self.path_audio.mkdir(parents=True)
            logger.warning(f"音频文件夹{self.path_audio.name}不存在, 已创建")
        elif not self.path_audio.is_dir():
            raise NotADirectoryError(f"{self.path_audio.name}不是一个文件夹")

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
        try:
            speaker_audio_path = get_speaker_audio_path(self.path_audio, speaker_name)
        except FileHandleException as e:
            raise APIException(str(e)) from e
        for audio in speaker_audio_path:
            audio_bytes = audio.read_bytes()
            ref_text = extract_text_by_filename(audio.name)
            references.append(ServeReferenceAudio(audio=audio_bytes, text=ref_text))
        return ServeTTSRequest(
            text=text,
            chunk_length=chunk_length.value,
            format="wav",
            references=references,
            normalize=True,
            opus_bitrate=64,
            latency="normal",
            max_new_tokens=MAX_NEW_TOKENS,
            top_p=0.7,
            repetition_penalty=1.2,
            temperature=0.7,
            streaming=IS_STREAM,
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
            async with AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    content=ormsgpack.packb(
                        request.dict(),
                    ),
                    timeout=120,
                )
                return response.content
        except (
            HTTPStatusError,
            RequestError,
        ) as e:
            logger.error(f"获取TTS音频失败: {e}")
            raise HTTPException(
                f"{e}\n获取TTS音频超时, 你的接口配置错误或者文本过长"
            ) from e
        except Exception as e:
            raise APIException(f"{e}\n获取TTS音频失败, 检查API后端") from e

    def get_speaker_list(self) -> list[str]:
        """
        获取说话人列表

        Returns:
            list[str]: 说话人列表
        """
        try:
            return get_path_speaker_list(self.path_audio)
        except FileHandleException as e:
            raise APIException(str(e)) from e
