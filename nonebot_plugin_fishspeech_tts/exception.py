from httpx import (
    ReadTimeout,
    ConnectTimeout,
    ConnectError,
    RequestError,
    HTTPStatusError,
)


class APIException(Exception):
    """API异常类"""

    pass


class AuthorizationException(APIException):
    """授权异常类"""

    pass


class FileHandleException(Exception):
    """文件处理异常类"""

    pass


class HTTPException(
    ReadTimeout, ConnectTimeout, ConnectError, RequestError, HTTPStatusError
):
    """HTTP异常类"""

    pass
