class APIException(Exception):
    """API异常类"""

    pass


class AuthorizationException(APIException):
    """授权异常类"""

    pass
