import traceback
from apistar.http import JSONResponse


class ErrorHook(object):
    """
    处理assert异常
    """
    default_error_code = {999: "Unknown error"}

    def on_error(self, error: Exception) -> JSONResponse:
        """
        Handle error
        """
        code = 999
        message = None
        if not isinstance(error.args[0], (tuple, list)) \
                or len(error.args[0]) < 2:
            if isinstance(error.args[0], int):
                code = error.args[0]
            else:
                message = error.args[0]
        else:
            code, message = error.args[0][:2]

        code = int(code)

        if message is None:
            message = self.default_error_code.get(code, "Not configured error")

        payload = {
            "code": code,
            "value": None,
            "errcode": code,
            "message": message,
            "detail": traceback.format_exc()
        }
        return JSONResponse(payload)
