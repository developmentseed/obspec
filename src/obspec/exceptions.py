"""Common exceptions.

Users writing generic code with obspec may wish to catch common exceptions. For example,
a user might wish to perform a head request but allow for the case where the object does
not exist.

Common exceptions pose a challenge for obspec. In general obspec strives to use
[structural subtyping (protocols) rather than nominal subtyping
(subclassing)][mypy_subtyping]. This is because protocols allow for implementations to
have no knowledge of or dependency on a shared base library (obspec) while still being
able to use the same interface.

[mypy_subtyping]: https://mypy.readthedocs.io/en/stable/protocols.html

However, structural subtyping does not work for exceptions: when you use `except
Exception`, that uses an `isinstance` check under the hood.

As a workaround, we **define well-known names** for exceptions and expect external
implementations to use the same names.

# Obspec users

Use the [`map_exception`][obspec.exceptions.map_exception] function in this module to
convert from an implementation-defined exception to an obspec-defined exception.

```py
from obspec import Head
from obspec.exceptions import NotFoundError, map_exception


def check_if_exists(client: Head, path: str) -> bool:
    \"\"\"Check if a file exists at the given location.

    Returns True if the file exists, False otherwise.
    \"\"\"
    try:
        client.head(path)
    except Exception as e:
        if isinstance(map_exception(e), NotFoundError):
            return False

        raise

    return True
```

!!! note
    If you don't care about catching exceptions, you can ignore this module entirely.

# Obspec implementors

Create your own exceptions but ensure you use the **same names** for your own exceptions
as defined in this module.

You may also have other exceptions that are not defined here, but any exceptions that
logically fall under the purview of the exceptions defined here should your exceptions
with the same name.

"""

from __future__ import annotations

import builtins
from typing import TypeVar


class BaseError(Exception):
    """The base obspec exception from which all other errors subclass."""


class NotFoundError(FileNotFoundError, BaseError):
    """Error when the object is not found at given location."""


class InvalidPathError(BaseError):
    """Error for invalid path."""


class NotSupportedError(BaseError):
    """Error when the attempted operation is not supported."""


class AlreadyExistsError(BaseError):
    """Error when the object already exists."""


class PreconditionError(BaseError):
    """Error when the required conditions failed for the operation."""


class NotModifiedError(BaseError):
    """Error when the object at the location isn't modified."""


class NotImplementedError(BaseError, builtins.NotImplementedError):  # noqa: A001
    """Error when an operation is not implemented.

    Subclasses from the built-in [NotImplementedError][].
    """


class PermissionDeniedError(BaseError):
    """Error when the used credentials don't have enough permission to perform the requested operation."""  # noqa: E501


class UnauthenticatedError(BaseError):
    """Error when the used credentials lack valid authentication."""


_name_mapping: dict[str, type[BaseError]] = {
    FileNotFoundError.__name__: NotFoundError,
    NotFoundError.__name__: NotFoundError,
    InvalidPathError.__name__: InvalidPathError,
    NotSupportedError.__name__: NotSupportedError,
    AlreadyExistsError.__name__: AlreadyExistsError,
    PreconditionError.__name__: PreconditionError,
    NotModifiedError.__name__: NotModifiedError,
    NotImplementedError.__name__: NotImplementedError,
    PermissionDeniedError.__name__: PermissionDeniedError,
    UnauthenticatedError.__name__: UnauthenticatedError,
}
"""A mapping from well-known names to obspec-defined exception classes.
"""

ExceptionType = TypeVar("ExceptionType", bound=Exception)
"""Type variable for an exception type, bound to `Exception`."""


def map_exception(exception: ExceptionType) -> ExceptionType | BaseError:
    """Map an implementation-defined exception to an obspec-defined exception by name.

    This will use the name of the exception class to find a corresponding obspec-defined
    exception class. If no mapping is found, the original exception is returned.
    """
    new_exc_class = _name_mapping.get(exception.__class__.__name__)

    if new_exc_class is None:
        return exception

    return new_exc_class(*exception.args)
