from decimal import Decimal, InvalidOperation
from pathlib import Path

from httpx import AsyncClient
from nonebot.log import logger

from .config import config
from .exception import APIException, AuthorizationException, FileHandleException
from .files import get_path_speaker_list, load_references
from .request_params import ChunkLength, ServeTTSRequest
from .transport import request_audio, request_json


class FishAudioAPI:
    """Fish Audio 云端 API；基础模型通过 model 请求头选择。"""

    api_url: str = config.online_api_url
    path_audio: Path = Path(config.tts_audio_path)
    proxy = config.online_api_proxy

    @classmethod
    def _get_headers(cls) -> dict[str, str]:
        token = (config.online_authorization or "").strip()
        if not token or token == "xxxxx":  # noqa: S105 - 旧配置中的占位符
            raise AuthorizationException("请先填写 online_authorization 或使用离线 API")
        return {"Authorization": f"Bearer {token}"}

    @classmethod
    async def _get_reference_id_by_speaker(cls, speaker: str) -> str:
        if reference_id := config.online_reference_ids.get(speaker):
            return reference_id
        headers = cls._get_headers()
        async with AsyncClient(proxy=cls.proxy, timeout=60) as client:
            for sort_by in ("score", "task_count", "created_at"):
                data = await request_json(
                    client,
                    "GET",
                    cls.api_url.rstrip("/") + "/model",
                    params={"title": speaker, "sort_by": sort_by},
                    headers=headers,
                )
                items = data.get("items")
                if not isinstance(items, list):
                    raise APIException("API 语音角色列表格式无效")
                for item in items:
                    if (
                        isinstance(item, dict)
                        and isinstance(item.get("title"), str)
                        and speaker in item["title"]
                        and isinstance(item.get("_id"), str)
                        and item["_id"]
                    ):
                        return item["_id"]
        raise APIException("未找到对应的角色，可通过 online_reference_ids 配置音色 ID")

    @classmethod
    async def generate_servettsrequest(
        cls,
        text: str,
        speaker_name: str,
        chunk_length: ChunkLength = ChunkLength.NORMAL,
    ) -> ServeTTSRequest:
        cls._get_headers()
        reference_id = None
        references = []
        if config.online_model_first:
            reference_id = await cls._get_reference_id_by_speaker(speaker_name)
        else:
            try:
                references = load_references(cls.path_audio, speaker_name)
            except FileHandleException:
                logger.warning("未找到可用参考音频，尝试搜索云端音色")
                reference_id = await cls._get_reference_id_by_speaker(speaker_name)
        return ServeTTSRequest(
            text=text,
            reference_id=reference_id,
            references=references,
            language=config.online_language,
            chunk_length=chunk_length.value,
            max_new_tokens=config.tts_max_new_tokens,
            streaming=config.tts_is_stream,
        )

    @classmethod
    async def generate_tts(cls, request: ServeTTSRequest) -> bytes:
        headers = {**cls._get_headers(), "model": config.online_model}
        async with AsyncClient(proxy=cls.proxy, timeout=60) as client:
            return await request_audio(
                client,
                cls.api_url.rstrip("/") + "/v1/tts",
                request,
                headers,
                online=True,
            )

    @classmethod
    async def get_balance(cls) -> Decimal:
        headers = cls._get_headers()
        async with AsyncClient(proxy=cls.proxy, timeout=60) as client:
            data = await request_json(
                client,
                "GET",
                cls.api_url.rstrip("/") + "/wallet/self/api-credit",
                headers=headers,
            )
        try:
            credit = Decimal(str(data["credit"]))
        except (KeyError, InvalidOperation) as exc:
            raise APIException("API 返回的余额格式无效") from exc
        if not credit.is_finite():
            raise APIException("API 返回的余额格式无效")
        return credit

    @classmethod
    def get_speaker_list(cls) -> list[str]:
        speakers = list(config.online_reference_ids)
        if not config.online_model_first:
            try:
                speakers.extend(get_path_speaker_list(cls.path_audio))
            except FileHandleException:
                logger.warning("参考音频目录不存在或没有可用音频")
        return [*dict.fromkeys(speakers), "更多云端音色: https://fish.audio/"]
