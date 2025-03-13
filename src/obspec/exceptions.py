"""Exceptions."""


class BaseError(Exception):
    """The base Python-facing exception from which all other errors subclass."""


class GenericError(BaseError):
    """A fallback error type when no variant matches."""


class NotFoundError(FileNotFoundError, BaseError):
    """Error when the object is not found at given location."""


class InvalidPathError(BaseError):
    """Error for invalid path."""


class JoinError(BaseError):
    """Error when tokio::spawn failed."""


class NotSupportedError(BaseError):
    """Error when the attempted operation is not supported."""


class AlreadyExistsError(BaseError):
    """Error when the object already exists."""


class PreconditionError(BaseError):
    """Error when the required conditions failed for the operation."""


class NotModifiedError(BaseError):
    """Error when the object at the location isn't modified."""


class NotImplementedError(BaseError, NotImplementedError):  # noqa: A001
    """Error when an operation is not implemented.

    Subclasses from the built-in [NotImplementedError][].
    """


class PermissionDeniedError(BaseError):
    """Error when the used credentials don't have enough permission to perform the requested operation."""  # noqa: E501


class UnauthenticatedError(BaseError):
    """Error when the used credentials lack valid authentication."""


class UnknownConfigurationKeyError(BaseError):
    """Error when a configuration key is invalid for the store used."""
