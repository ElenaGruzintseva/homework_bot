class RequestError(Exception):
    """Error class handling errors: server unavailability."""

    pass


class UnexpectedStatusErorr(Exception):
    """An error class that handles message sending errors."""

    pass
