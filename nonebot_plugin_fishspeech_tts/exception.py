"""
自定义异常类
"""


class APIException(Exception):
    """API异常类"""


class AuthorizationException(APIException):
    """授权异常类"""


class FileHandleException(Exception):
    """文件处理异常类"""


class HTTPException(APIException):
    """HTTP异常类"""
