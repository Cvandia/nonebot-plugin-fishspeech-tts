import asyncio
import io
import json
import wave
from decimal import Decimal

import httpx
import ormsgpack
import pytest

from nonebot_plugin_fishspeech_tts import fish_audio_api, fish_speech_api
from nonebot_plugin_fishspeech_tts.config import Config, config
from nonebot_plugin_fishspeech_tts.exception import (
    APIException,
    AuthorizationException,
    HTTPException,
)
from nonebot_plugin_fishspeech_tts.fish_audio_api import FishAudioAPI
from nonebot_plugin_fishspeech_tts.fish_speech_api import FishSpeechAPI
from nonebot_plugin_fishspeech_tts.request_params import (
    ChunkLength,
    ServeReferenceAudio,
    ServeTTSRequest,
)


def make_wav():
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(44100)
        audio.writeframes(b"\x00\x00" * 100)
    return buffer.getvalue()


WAV = make_wav()


async def audio_chunks():
    yield WAV[:20]
    yield WAV[20:]


@pytest.fixture
def mock_api(monkeypatch):
    requests = []

    def install(handler):
        async def respond(request):
            requests.append(request)
            return handler(request)

        def client(**kwargs):
            kwargs.pop("proxy", None)
            return httpx.AsyncClient(transport=httpx.MockTransport(respond), **kwargs)

        monkeypatch.setattr(fish_audio_api, "AsyncClient", client)
        monkeypatch.setattr(fish_speech_api, "AsyncClient", client)
        return requests

    return install


@pytest.mark.parametrize(
    "model", ["s1", "s2-pro", "s2.1-pro", "s2.1-pro-free", "drama-3"]
)
@pytest.mark.parametrize("streaming", [False, True])
async def test_cloud_json_model_and_language(mock_api, monkeypatch, model, streaming):
    monkeypatch.setattr(config, "online_model", model)
    monkeypatch.setattr(config, "online_language", "zh-CN")
    monkeypatch.setattr(config, "online_reference_ids", {"角色": "voice-id"})
    monkeypatch.setattr(config, "tts_is_stream", streaming)
    requests = mock_api(
        lambda _: httpx.Response(
            200, headers={"Content-Type": "audio/wav"}, content=audio_chunks()
        )
    )
    request = await FishAudioAPI.generate_servettsrequest("[轻声]你好", "角色")
    assert await FishAudioAPI.generate_tts(request) == WAV
    assert len(requests) == 1
    sent = requests[0]
    assert sent.url.path == "/v1/tts"
    assert sent.headers["authorization"] == "Bearer test-token"
    assert sent.headers["model"] == model
    assert sent.headers["content-type"] == "application/json"
    payload = json.loads(sent.content)
    assert payload["text"] == "[轻声]你好"
    assert payload["reference_id"] == "voice-id"
    assert payload["language"] == "zh-CN"
    assert "streaming" not in payload
    assert "max_new_tokens" not in payload
    assert "temperature" not in payload
    assert "single_chunk" not in payload


async def test_msgpack_reference_and_concurrent_json(mock_api):
    requests = mock_api(
        lambda _: httpx.Response(
            200, content=WAV, headers={"Content-Type": "audio/wav"}
        )
    )
    reference = ServeReferenceAudio(audio=b"\x80\xffvoice", text="参考文本")
    results = await asyncio.gather(
        FishAudioAPI.generate_tts(ServeTTSRequest(text="克隆", references=[reference])),
        FishAudioAPI.generate_tts(
            ServeTTSRequest(text="音色", reference_id="voice-id")
        ),
    )
    assert results == [WAV, WAV]
    binary, json_request = requests
    assert binary.headers["content-type"] == "application/msgpack"
    assert ormsgpack.unpackb(binary.content)["references"] == [
        {"audio": b"\x80\xffvoice", "text": "参考文本"}
    ]
    assert json_request.headers["content-type"] == "application/json"
    assert json.loads(json_request.content)["reference_id"] == "voice-id"


@pytest.mark.parametrize("streaming", [False, True])
async def test_offline_auth_reference_and_payload(mock_api, monkeypatch, streaming):
    monkeypatch.setattr(config, "offline_authorization", "local-token")
    monkeypatch.setattr(
        config, "offline_reference_ids", {"本地角色": "saved-reference"}
    )
    monkeypatch.setattr(config, "offline_single_chunk", True)
    monkeypatch.setattr(config, "tts_is_stream", streaming)
    requests = mock_api(
        lambda _: httpx.Response(
            200, content=WAV, headers={"Content-Type": "audio/wav"}
        )
    )
    request = FishSpeechAPI.generate_servettsrequest("本地合成", "本地角色")
    assert await FishSpeechAPI.generate_tts(request) == WAV
    sent = requests[0]
    assert sent.headers["authorization"] == "Bearer local-token"
    assert "model" not in sent.headers
    payload = ormsgpack.unpackb(sent.content)
    assert payload["reference_id"] == "saved-reference"
    assert payload["streaming"] is streaming
    assert payload["single_chunk"] is True
    assert "max_new_tokens" not in payload
    assert "mp3_bitrate" not in payload
    assert "language" not in payload


async def test_offline_without_auth(mock_api):
    requests = mock_api(lambda _: httpx.Response(200, content=WAV))
    await FishSpeechAPI.generate_tts(ServeTTSRequest(text="本地"))
    assert "authorization" not in requests[0].headers


@pytest.mark.parametrize("api", [FishAudioAPI, FishSpeechAPI])
@pytest.mark.parametrize("status", [301, 400, 401, 402, 403, 404, 422, 429, 500, 503])
async def test_errors_never_become_audio(mock_api, api, status):
    mock_api(lambda _: httpx.Response(status, json={"message": "error"}))
    expected = AuthorizationException if status in {401, 403} else APIException
    with pytest.raises(expected):
        await api.generate_tts(
            ServeTTSRequest(text="错误测试", reference_id="voice-id")
        )


@pytest.mark.parametrize("api", [FishAudioAPI, FishSpeechAPI])
@pytest.mark.parametrize(
    ("content_type", "content"),
    [("application/json", b"{}"), ("text/html", b"error"), ("audio/wav", b"")],
)
async def test_invalid_success_response(mock_api, api, content_type, content):
    mock_api(
        lambda _: httpx.Response(
            200, content=content, headers={"Content-Type": content_type}
        )
    )
    with pytest.raises(APIException):
        await api.generate_tts(ServeTTSRequest(text="测试"))


@pytest.mark.parametrize("api", [FishAudioAPI, FishSpeechAPI])
@pytest.mark.parametrize(
    "error", [httpx.ConnectError, httpx.ReadTimeout, httpx.ProxyError]
)
async def test_network_errors(mock_api, api, error):
    def fail(request):
        raise error("mock network failure", request=request)

    mock_api(fail)
    with pytest.raises(HTTPException):
        await api.generate_tts(ServeTTSRequest(text="网络测试"))


@pytest.mark.parametrize("token", [None, "", "  ", "xxxxx"])
async def test_missing_auth(token, monkeypatch):
    monkeypatch.setattr(config, "online_authorization", token)
    with pytest.raises(AuthorizationException):
        await FishAudioAPI.generate_tts(ServeTTSRequest(text="未鉴权"))


async def test_model_search_fallback(mock_api):
    def respond(request):
        if request.url.params["sort_by"] == "created_at":
            return httpx.Response(
                200,
                json={"total": 1, "items": [{"title": "角色音色", "_id": "matched"}]},
            )
        return httpx.Response(200, json={"total": 0, "items": []})

    requests = mock_api(respond)
    request = await FishAudioAPI.generate_servettsrequest("你好", "角色")
    assert request.reference_id == "matched"
    assert len(requests) == 3
    assert all(item.url.path == "/model" for item in requests)


async def test_search_and_balance_auth_errors(mock_api):
    requests = mock_api(lambda _: httpx.Response(401, json={"message": "unauthorized"}))
    with pytest.raises(AuthorizationException):
        await FishAudioAPI._get_reference_id_by_speaker("角色")
    with pytest.raises(AuthorizationException):
        await FishAudioAPI.get_balance()
    assert len(requests) == 2


@pytest.mark.parametrize("payload", [{}, {"items": None}, {"items": []}])
async def test_model_search_invalid_or_empty(mock_api, payload):
    mock_api(lambda _: httpx.Response(200, json=payload))
    with pytest.raises(APIException):
        await FishAudioAPI._get_reference_id_by_speaker("不存在")


async def test_balance_decimal_string(mock_api):
    requests = mock_api(
        lambda _: httpx.Response(200, json={"credit": "12.34567890123456789"})
    )
    assert await FishAudioAPI.get_balance() == Decimal("12.34567890123456789")
    assert requests[0].url.path == "/wallet/self/api-credit"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"credit": "invalid"},
        {"credit": None},
        {"credit": "NaN"},
        {"credit": "Infinity"},
    ],
)
async def test_invalid_balance(mock_api, payload):
    mock_api(lambda _: httpx.Response(200, json=payload))
    with pytest.raises(APIException):
        await FishAudioAPI.get_balance()


@pytest.mark.parametrize("content", [b"not-json", b"[]"])
async def test_invalid_json_response(mock_api, content):
    mock_api(lambda _: httpx.Response(200, content=content))
    with pytest.raises(APIException):
        await FishAudioAPI.get_balance()


def test_defaults_and_server_specific_fields():
    defaults = Config()
    assert defaults.online_api_url == "https://api.fish.audio"
    assert defaults.offline_api_url == "http://127.0.0.1:8080"
    request = ServeTTSRequest(text="测试", language="zh-CN", max_new_tokens=800)
    assert request.to_payload(online=True)["max_new_tokens"] == 800
    local = request.to_payload(online=False)
    assert "language" not in local
    assert "single_chunk" not in local
    assert "temperature" not in local


def test_cloud_chunk_limit():
    request = ServeTTSRequest(text="长分片", chunk_length=ChunkLength.EXTRA_LONG.value)
    with pytest.raises(ValueError, match="300"):
        request.to_payload(online=True)
    assert request.to_payload(online=False)["chunk_length"] == 500


@pytest.mark.parametrize("api", [FishAudioAPI, FishSpeechAPI])
async def test_local_reference_files(tmp_path, monkeypatch, api):
    monkeypatch.setattr(api, "path_audio", tmp_path)
    monkeypatch.setattr(config, "online_model_first", False)
    (tmp_path / "[角色]你好.WAV").write_bytes(WAV)
    if api is FishAudioAPI:
        request = await api.generate_servettsrequest("测试", "角色")
    else:
        request = api.generate_servettsrequest("测试", "角色")
    assert request.references[0].audio == WAV
    assert request.references[0].text == "你好"


async def test_cloud_missing_directory_falls_back(tmp_path, monkeypatch, mock_api):
    monkeypatch.setattr(FishAudioAPI, "path_audio", tmp_path / "missing")
    monkeypatch.setattr(config, "online_model_first", False)
    mock_api(
        lambda _: httpx.Response(
            200, json={"items": [{"title": "角色", "_id": "fallback"}]}
        )
    )
    request = await FishAudioAPI.generate_servettsrequest("测试", "角色")
    assert request.reference_id == "fallback"


def test_offline_missing_directory_is_api_error(tmp_path, monkeypatch):
    monkeypatch.setattr(FishSpeechAPI, "path_audio", tmp_path / "missing")
    with pytest.raises(APIException):
        FishSpeechAPI.generate_servettsrequest("测试", "角色")


def test_mapped_speakers_without_local_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(FishSpeechAPI, "path_audio", tmp_path / "missing")
    monkeypatch.setattr(config, "offline_reference_ids", {"本地": "local-id"})
    monkeypatch.setattr(config, "online_reference_ids", {"云端": "cloud-id"})
    assert FishSpeechAPI.get_speaker_list() == ["本地"]
    assert "云端" in FishAudioAPI.get_speaker_list()
