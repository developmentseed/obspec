from __future__ import annotations

from typing import IO, TYPE_CHECKING, Literal, Protocol, TypedDict, Union

if TYPE_CHECKING:
    import sys
    from collections.abc import AsyncIterable, AsyncIterator, Iterable, Iterator
    from pathlib import Path

    from ._attributes import Attributes

    if sys.version_info >= (3, 10):
        from typing import TypeAlias
    else:
        from typing_extensions import TypeAlias

    if sys.version_info >= (3, 12):
        from collections.abc import Buffer
    else:
        from typing_extensions import Buffer


class UpdateVersion(TypedDict, total=False):
    """Uniquely identifies a version of an object to update.

    Stores will use differing combinations of `e_tag` and `version` to provide
    conditional updates, and it is therefore recommended applications preserve both
    """

    e_tag: str | None
    """The unique identifier for the newly created object.

    <https://datatracker.ietf.org/doc/html/rfc9110#name-etag>
    """

    version: str | None
    """A version indicator for the newly created object."""


PutMode: TypeAlias = Union[Literal["create", "overwrite"], UpdateVersion]
"""Configure preconditions for the put operation

There are three modes:

- Overwrite: Perform an atomic write operation, overwriting any object present at the
  provided path.
- Create: Perform an atomic write operation, returning
  an error if an object already exists at the provided path.
- Update: Perform an atomic write operation if the current version of the object matches
  the provided [`UpdateVersion`][obspec.UpdateVersion], returning an error otherwise.

If a string is provided, it must be one of:

- `"overwrite"`
- `"create"`

If a `dict` is provided, it must meet the criteria of
[`UpdateVersion`][obspec.UpdateVersion].
"""


class PutResult(TypedDict):
    """Result for a put request."""

    e_tag: str | None
    """
    The unique identifier for the newly created object

    <https://datatracker.ietf.org/doc/html/rfc9110#name-etag>
    """

    version: str | None
    """A version indicator for the newly created object."""


class Put(Protocol):
    def put(  # noqa: PLR0913
        self,
        path: str,
        file: IO[bytes] | Path | bytes | Buffer | Iterator[Buffer] | Iterable[Buffer],
        *,
        attributes: Attributes | None = None,
        tags: dict[str, str] | None = None,
        mode: PutMode | None = None,
        use_multipart: bool | None = None,
        chunk_size: int = ...,
        max_concurrency: int = ...,
    ) -> PutResult:
        """Save the provided bytes to the specified location.

        The operation is guaranteed to be atomic, it will either successfully write the
        entirety of `file` to `location`, or fail. No clients should be able to observe
        a partially written object.

        Args:
            path: The path within the store for where to save the file.
            file: The object to upload. Supports various input:

                - A file-like object opened in binary read mode
                - A [`Path`][pathlib.Path] to a local file
                - A [`bytes`][] object.
                - Any object implementing the Python [buffer
                protocol](https://docs.python.org/3/c-api/buffer.html) (includes `bytes`
                but also `memoryview`, numpy arrays, and more).
                - An iterator or iterable of objects implementing the Python buffer
                protocol.

        Keyword Args:
            mode: Configure the [`PutMode`][obspec.PutMode] for this operation. Refer
                to the [`PutMode`][obspec.PutMode] docstring for more information.

                If this provided and is not `"overwrite"`, a non-multipart upload will
                be performed. Defaults to `"overwrite"`.
            attributes: Provide a set of `Attributes`. Defaults to `None`.
            tags: Provide tags for this object. Defaults to `None`.
            use_multipart: Whether to force using a multipart upload.

                If `True`, the upload will always use a multipart upload, even if the
                length of the file is less than `chunk_size`. If `False`, the upload
                will never use a multipart upload, and the entire input will be
                materialized in memory as part of the upload. If `None`, the
                implementation will choose whether to use a multipart upload based on
                the length of the file and `chunk_size`.

                Defaults to `None`.
            chunk_size: The size of chunks to use within each part of the multipart
                upload. The default is allowed to be implementation-specific.
            max_concurrency: The maximum number of chunks to upload concurrently. This
                impacts the memory usage of large file uploads. The default is allowed
                to be implementation-specific.

        """
        ...


class PutAsync(Protocol):
    async def put_async(  # noqa: PLR0913
        self,
        path: str,
        file: IO[bytes]
        | Path
        | bytes
        | Buffer
        | AsyncIterator[Buffer]
        | AsyncIterable[Buffer]
        | Iterator[Buffer]
        | Iterable[Buffer],
        *,
        attributes: Attributes | None = None,
        tags: dict[str, str] | None = None,
        mode: PutMode | None = None,
        use_multipart: bool | None = None,
        chunk_size: int = ...,
        max_concurrency: int = ...,
    ) -> PutResult:
        """Call `put` asynchronously.

        Refer to the documentation for [`Put`][obspec.Put]. In addition to what the
        synchronous `put` allows for the `file` parameter, this **also supports an async
        iterator or iterable** of objects implementing the Python buffer protocol.

        This means, for example, you can pass the result of `get_async` directly to
        `put_async`, and the request will be streamed through Python during the put
        operation:

        ```py
        from obspec import GetAsync, PutAsync

        async def streaming_copy(
            fetch_client: GetAsync,
            put_client: PutAsync,
            path1: str,
            path2: str,
        ):
            # This only constructs the stream, it doesn't materialize the data in memory
            resp = await fetch_client.get_async(path1)
            # A streaming upload is created to copy the file to path2
            await put_client.put_async(path2, resp)
        ```
        """
        ...
