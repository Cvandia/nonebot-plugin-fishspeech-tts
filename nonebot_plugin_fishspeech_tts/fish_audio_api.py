from pathlib import Path

import ormsgpack
from httpx import (
    AsyncClient,
    ConnectError,
    ConnectTimeout,
    HTTPStatusError,
    ReadTimeout,
)
from nonebot.log import logger

from .config import config
from .exception import (
    APIException,
    AuthorizationException,
    FileHandleException,
    HTTPException,
)
from .files import (
    extract_text_by_filename,
    get_path_speaker_list,
    get_speaker_audio_path,
)
from .request_params import ChunkLength, ServeReferenceAudio, ServeTTSRequest

is_reference_id_first = config.online_model_first
API_URL = config.online_api_url
API_PROXY = config.online_api_proxy
IS_STREAM = config.tts_is_stream
MAX_NEW_TOKENS = config.tts_max_new_tokens


class FishAudioAPI:
    """
    FishAudioAPI类, 用于调用FishAudio的API接口
    """

    api_url: str = API_URL
    path_audio: Path = Path(config.tts_audio_path)
    proxy = API_PROXY
    from typing import ClassVar

    _headers: ClassVar[dict] = {
        "Authorization": f"Bearer {config.online_authorization}",
    }

    @classmethod
    async def _get_reference_id_by_speaker(cls, speaker: str) -> str:
        """
        通过说话人姓名获取说话人的reference_id

        Args:
            speaker: 说话人姓名

        Returns:
            reference_id: 说话人的reference_id

        exception:
            APIException: 获取语音角色列表为空
        """
        request_api = cls.api_url + "/model"
        sort_options = ["score", "task_count", "created_at"]
        async with AsyncClient(proxy=cls.proxy) as client:
            for sort_by in sort_options:
                params = {"title": speaker, "sort_by": sort_by}
                response = await client.get(
                    request_api, params=params, headers=cls._headers
                )
                resp_data = response.json()
                if resp_data["total"] == 0:
                    continue
                for item in resp_data["items"]:
                    if speaker in item["title"]:
                        return item["_id"]
        raise APIException("未找到对应的角色")

    @classmethod
    async def generate_servettsrequest(
        cls,
        text: str,
        speaker_name: str,
        chunk_length: ChunkLength = ChunkLength.NORMAL,
        # TODO: speed: int = 0,
    ) -> ServeTTSRequest:
        """
        生成TTS请求

        Args:
            text: 待合成文本
            speaker_name: 说话人姓名
            chunk_length: 分片长度
            TODO:speed: 语速

        Returns:
            ServeTTSRequest: TTS请求
        """
        if not config.online_authorization and config.tts_is_online:
            raise AuthorizationException("请先在配置文件中填写在线授权码或使用离线api")

        reference_id = None
        references = []
        try:
            if is_reference_id_first:
                reference_id = await cls._get_reference_id_by_speaker(speaker_name)
            else:
                try:
                    speaker_audio_path = get_speaker_audio_path(
                        cls.path_audio, speaker_name
                    )
                    for audio in speaker_audio_path:
                        audio_bytes = audio.read_bytes()
                        ref_text = extract_text_by_filename(audio.name)
                        references.append(
                            ServeReferenceAudio(audio=audio_bytes, text=ref_text)
                        )
                except FileHandleException:
                    logger.warning("音频文件夹不存在, 已转为在线模型优先模式")
                    reference_id = await cls._get_reference_id_by_speaker(speaker_name)
        except APIException as e:
            raise e from e
        return ServeTTSRequest(
            text=text,
            reference_id=reference_id,
            format="wav",
            mp3_bitrate=64,
            latency="normal",
            opus_bitrate=24,
            normalize=True,
            chunk_length=chunk_length.value,
            max_new_tokens=MAX_NEW_TOKENS,
            streaming=IS_STREAM,
            references=references,
        )

    @classmethod
    async def generate_tts(cls, request: ServeTTSRequest) -> bytes:
        """
        获取TTS音频

        Args:
            request: TTS请求

        Returns:
            bytes: TTS音频二进制数据
        """
        if request.references:
            cls._headers["content-type"] = "application/msgpack"
            try:
                async with (
                    AsyncClient(proxy=cls.proxy) as client,
                    client.stream(
                        "POST",
                        cls.api_url + "/v1/tts",
                        headers=cls._headers,
                        content=ormsgpack.packb(
                            request, option=ormsgpack.OPT_SERIALIZE_PYDANTIC
                        ),
                        timeout=60,
                    ) as resp,
                ):
                    return await resp.aread()
            except (
                ConnectError,
                HTTPStatusError,
            ) as e:
                logger.error(f"获取TTS音频失败: {e}")
                if cls.proxy:
                    raise HTTPException("代理地址错误, 请检查代理地址是否正确") from e
                raise HTTPException("网络错误, 请检查网络连接") from e
        else:
            cls._headers["content-type"] = "application/json"
            try:
                async with AsyncClient(proxy=cls.proxy) as client:
                    response = await client.post(
                        cls.api_url + "/v1/tts",
                        headers=cls._headers,
                        json=ormsgpack.packb(
                            request, option=ormsgpack.OPT_SERIALIZE_PYDANTIC
                        ),
                        timeout=60,
                    )
                    return response.content
            except (
                ReadTimeout,
                ConnectTimeout,
                ConnectError,
                HTTPStatusError,
            ) as e:
                logger.error(f"获取TTS音频失败: {e}")
                if cls.proxy:
                    raise HTTPException("代理地址错误, 请检查代理地址是否正确") from e
                raise HTTPException("网络错误, 请检查网络连接") from e

    @classmethod
    async def get_balance(cls) -> float:
        """
        获取账户余额
        """
        balance_url = cls.api_url + "/wallet/self/api-credit"
        async with AsyncClient(proxy=cls.proxy) as client:
            response = await client.get(balance_url, headers=cls._headers)
            try:
                return response.json()["credit"]
            except KeyError:
                raise AuthorizationException("授权码错误或已失效") from KeyError

    @classmethod
    def get_speaker_list(cls) -> list[str]:
        """
        获取语音角色列表
        """
        return_list = ["请查看官网了解更多: https://fish.audio/zh-CN/"]
        if not is_reference_id_first:
            try:
                return_list.extend(get_path_speaker_list(cls.path_audio))
            except FileHandleException:
                logger.warning("音频文件夹不存在或无法读取")
        return return_list
