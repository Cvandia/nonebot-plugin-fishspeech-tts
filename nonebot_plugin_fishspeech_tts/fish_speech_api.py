from pathlib import Path

from httpx import AsyncClient

from .config import config
from .exception import APIException, FileHandleException
from .files import get_path_speaker_list, load_references
from .request_params import ChunkLength, ServeTTSRequest
from .transport import request_audio


class FishSpeechAPI:
    """自建服务的模型在启动时选择，不发送云端 model 请求头。"""

    api_url: str = config.offline_api_url.rstrip("/") + "/v1/tts"
    path_audio: Path = Path(config.tts_audio_path)

    @classmethod
    def generate_servettsrequest(
        cls,
        text: str,
        speaker_name: str,
        chunk_length: ChunkLength = ChunkLength.NORMAL,
    ) -> ServeTTSRequest:
        reference_id = config.offline_reference_ids.get(speaker_name)
        references = []
        if not reference_id:
            try:
                references = load_references(cls.path_audio, speaker_name)
            except FileHandleException as exc:
                raise APIException(str(exc)) from exc
        return ServeTTSRequest(
            text=text,
            reference_id=reference_id,
            references=references,
            chunk_length=chunk_length.value,
            max_new_tokens=config.tts_max_new_tokens,
            streaming=config.tts_is_stream,
            single_chunk=config.offline_single_chunk,
        )

    @classmethod
    async def generate_tts(cls, request: ServeTTSRequest) -> bytes:
        headers = {}
        if config.offline_authorization:
            headers["Authorization"] = f"Bearer {config.offline_authorization}"
        async with AsyncClient(timeout=60) as client:
            return await request_audio(
                client, cls.api_url, request, headers, online=False
            )

    @classmethod
    def get_speaker_list(cls) -> list[str]:
        speakers = list(config.offline_reference_ids)
        try:
            speakers.extend(get_path_speaker_list(cls.path_audio))
        except FileHandleException as exc:
            if not speakers:
                raise APIException(str(exc)) from exc
        return list(dict.fromkeys(speakers))
