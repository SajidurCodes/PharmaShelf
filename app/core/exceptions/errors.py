class ConflictError(Exception):
    """An operation conflicts with an existing record."""


class UnauthorizedError(Exception):
    """Authentication is required or the supplied credentials are invalid."""

class ForbiddenError(Exception):
    """The signed-in user lacks permission for this action."""