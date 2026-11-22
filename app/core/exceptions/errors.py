class ConflictError(Exception):
    """An operation conflicts with an existing record."""


class UnauthorizedError(Exception):
    """Authentication is required or the supplied credentials are invalid."""