class ApiError(Exception):
    def __init__(
        self,
        message,
        status_code=400,
        code="bad_request",
        details=None,
        headers=None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        self.headers = headers or {}


class UpstreamError(ApiError):
    def __init__(
        self,
        message,
        status_code=502,
        code="x_api_error",
        details=None,
        headers=None,
    ):
        super().__init__(message, status_code, code, details, headers)
