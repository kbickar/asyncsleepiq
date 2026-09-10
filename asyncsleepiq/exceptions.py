"""SleepIQ Exceptions."""


class SleepIQLoginException(Exception):
    """Bad credentials or rejected login (non-retryable)."""


class SleepIQConnectionException(SleepIQLoginException):
    """Transient connection or transport failure during login (retryable).

    Subclasses SleepIQLoginException for backward compatibility: callers
    that catch SleepIQLoginException continue to work, while callers that
    need to distinguish transient failures can catch this subclass first.
    """


class SleepIQTimeoutException(Exception):
    """Timeout during an API or login call."""


class SleepIQAPIException(Exception):
    """Exception in API call."""

    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)
