class ResponseNotFoundError(Exception):
    """Исключение при отсутствии отклика"""
    def __init__(self, message="Response not found"):
        self.message = message
        super().__init__(self.message)

class DuplicateResponseError(Exception):
    """Исключение при дублировании отклика"""
    def __init__(self, message="Duplicate response detected"):
        self.message = message
        super().__init__(self.message)

class InvalidResponseActionError(Exception):
    """Недопустимое действие с откликом"""
    def __init__(self, message="Invalid response action"):
        self.message = message
        super().__init__(self.message)