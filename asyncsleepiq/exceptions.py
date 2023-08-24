"""SleepIQ Exceptions."""


class SleepIQLoginException(Exception):
    """Exception in Login process."""


class SleepIQTimeoutException(Exception):
    """Timeout in Login process."""


class SleepIQAPIException(Exception):
    """Exception in API call."""

    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)
