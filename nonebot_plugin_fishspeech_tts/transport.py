"""统一 HTTP 错误处理，避免把错误响应当作语音发送。"""

import httpx
import ormsgpack

from .exception import APIException, AuthorizationException, HTTPException
from .request_params import ServeTTSRequest

AUTH_STATUS = {401, 403}
STATUS_MESSAGES = {
    400: "请求参数无效，请检查模型及参考音频配置",
    402: "API 余额不足，请充值或检查套餐",
    404: "API 地址、模型或参考音色不存在",
    422: "API 参数校验失败，请检查服务端版本与配置",
    429: "API 请求频率或并发超限，请稍后重试",
}


def check_status(response: httpx.Response) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        status = response.status_code
        if status in AUTH_STATUS:
            raise AuthorizationException("API 授权码错误、已失效或无访问权限") from exc
        message = STATUS_MESSAGES.get(status, "API 服务暂不可用，请稍后重试")
        raise APIException(f"{message} (HTTP {status})") from exc


async def request_json(
    client: httpx.AsyncClient, method: str, url: str, **kwargs
) -> dict:
    try:
        response = await client.request(method, url, **kwargs)
    except httpx.RequestError as exc:
        raise HTTPException("API 网络连接失败或超时，请检查地址、代理及网络") from exc
    check_status(response)
    try:
        data = response.json()
    except ValueError as exc:
        raise APIException("API 返回的不是有效 JSON") from exc
    if not isinstance(data, dict):
        raise APIException("API 返回的数据格式无效")
    return data


async def request_audio(
    client: httpx.AsyncClient,
    url: str,
    request: ServeTTSRequest,
    headers: dict[str, str],
    *,
    online: bool,
) -> bytes:
    try:
        payload = request.to_payload(online=online)
    except ValueError as exc:
        raise APIException(str(exc)) from exc
    # 带参考音频时使用 MessagePack，纯文本/音色 ID 请求使用真正的 JSON 对象。
    if online and not request.references:
        headers = {**headers, "Content-Type": "application/json"}
        body = {"json": payload}
    else:
        headers = {**headers, "Content-Type": "application/msgpack"}
        body = {"content": ormsgpack.packb(payload)}
    try:
        async with client.stream("POST", url, headers=headers, **body) as response:
            check_status(response)
            content_type = response.headers.get("content-type", "").split(";")[0]
            if content_type and not (
                content_type.startswith("audio/")
                or content_type == "application/octet-stream"
            ):
                raise APIException("API 未返回音频，请检查模型及服务端配置")
            audio = await response.aread()
    except httpx.RequestError as exc:
        raise HTTPException(
            "语音合成连接失败或超时，请检查地址、代理及文本长度"
        ) from exc
    if not audio:
        raise APIException("API 返回了空音频")
    return audio
