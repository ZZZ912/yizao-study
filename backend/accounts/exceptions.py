from rest_framework.exceptions import APIException


class InvalidCredentials(APIException):
    status_code = 400
    default_detail = "邮箱或密码不正确。"
    default_code = "invalid_credentials"


class LoginRateLimited(APIException):
    status_code = 429
    default_detail = "登录尝试过多，请稍后再试。"
    default_code = "login_rate_limited"

    def __init__(self, retry_after: int):
        self.retry_after = max(1, retry_after)
        super().__init__()
