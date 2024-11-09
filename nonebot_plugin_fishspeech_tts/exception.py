"""
自定义异常类
"""


class APIException(Exception):
    """API异常类"""

    pass


class AuthorizationException(APIException):
    """授权异常类"""

    pass


class FileHandleException(Exception):
    """文件处理异常类"""

    pass


class HTTPException(APIException):
    """HTTP异常类"""

    pass
