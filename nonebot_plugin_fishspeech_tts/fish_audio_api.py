from .config import config
from httpx import AsyncClient
from .exception import APIException, AuthorizationException
import enum


class ChunkLength(enum.Enum):
    SHORT = 800
    NORMAL = 1000
    LONG = 1500
    EXTRA_LONG = 3000

    def __str__(self):
        return str(self.value)


class FishAudioAPI:
    """
    FishAudioAPI类, 用于调用FishAudio的API接口
    """

    def __init__(self):
        self.url = "https://api.fish.audio/v1/tts"
        if not config.online_authorization and config.tts_is_online:
            raise APIException("请先在配置文件中填写在线授权码或使用离线api")
        else:
            self.headers = {
                "Authorization": f"Bearer {config.online_authorization}",
            }

    async def get_reference_id_by_speaker(self, speaker: str) -> str:
        """
        通过说话人姓名获取说话人的reference_id

        Args:
            speaker: 说话人姓名

        Returns:
            reference_id: 说话人的reference_id
        """
        request_api = "https://api.fish.audio/model"
        async with AsyncClient() as client:
            params = {"title": speaker}
            response = await client.get(
                request_api, params=params, headers=self.headers
            )
            resp_data = response.json()
            if resp_data["total"] == 0:
                raise APIException("获取语音角色列表为空")
            else:
                return resp_data["items"][0]["_id"]

    async def generate_tts(
        self, text: str, speaker: str, chunk_length: ChunkLength = ChunkLength.NORMAL
    ) -> bytes:
        """
        生成TTS音频

        Args:
            text: 待合成文本
            speaker: 说话人姓名

        Returns:
            bytes: TTS音频的二进制数据
        """
        reference_id = await self.get_reference_id_by_speaker(speaker)
        payload = {
            "reference_id": reference_id,
            "text": text,
            "format": "wav",
            "mp3_bitrate": 64,
            "latency": "normal",
            "opus_bitrate": 24,
            "normalize": True,
            "chunk_length": chunk_length.value,
        }
        async with AsyncClient() as client:
            response = await client.post(self.url, json=payload, headers=self.headers)
            if response.headers["Content-Type"] == "application/json":
                raise APIException(response.json())
            else:
                return response.content

    async def get_balance(self) -> float:
        """
        获取账户余额
        """
        balance_url = "https://api.fish.audio/wallet/self/api-credit"
        async with AsyncClient() as client:
            response = await client.get(balance_url, headers=self.headers)
            try:
                return response.json()["credit"]
            except KeyError:
                raise AuthorizationException("授权码错误或已失效")


fish_audio_api = FishAudioAPI()
