"""SleepIQ Exceptions."""


class SleepIQLoginException(Exception):
    """Exception in Login process."""


class SleepIQTimeoutException(Exception):
    """Timeout in Login process."""


class SleepIQAPIException(Exception):
    """Exception in API call."""
