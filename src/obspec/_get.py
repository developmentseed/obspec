from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypedDict

if TYPE_CHECKING:
    import sys
    from collections.abc import Sequence
    from datetime import datetime

    from ._attributes import Attributes
    from ._meta import ObjectMeta

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    if sys.version_info >= (3, 12):
        from collections.abc import Buffer
    else:
        from typing_extensions import Buffer


class OffsetRange(TypedDict):
    """Request all bytes starting from a given byte offset."""

    offset: int
    """The byte offset for the offset range request."""


class SuffixRange(TypedDict):
    """Request up to the last `n` bytes."""

    suffix: int
    """The number of bytes from the suffix to request."""


class GetOptions(TypedDict, total=False):
    """Options for a get request.

    All options are optional.
    """

    if_match: str | None
    """
    Request will succeed if the `ObjectMeta::e_tag` matches.

    See <https://datatracker.ietf.org/doc/html/rfc9110#name-if-match>

    Examples:

    ```text
    If-Match: "xyzzy"
    If-Match: "xyzzy", "r2d2xxxx", "c3piozzzz"
    If-Match: *
    ```
    """

    if_none_match: str | None
    """
    Request will succeed if the `ObjectMeta::e_tag` does not match.

    See <https://datatracker.ietf.org/doc/html/rfc9110#section-13.1.2>

    Examples:

    ```text
    If-None-Match: "xyzzy"
    If-None-Match: "xyzzy", "r2d2xxxx", "c3piozzzz"
    If-None-Match: *
    ```
    """

    if_unmodified_since: datetime | None
    """
    Request will succeed if the object has been modified since

    <https://datatracker.ietf.org/doc/html/rfc9110#section-13.1.3>
    """

    if_modified_since: datetime | None
    """
    Request will succeed if the object has not been modified since.

    Some stores, such as S3, will only return `NotModified` for exact
    timestamp matches, instead of for any timestamp greater than or equal.

    <https://datatracker.ietf.org/doc/html/rfc9110#section-13.1.4>
    """

    range: tuple[int, int] | Sequence[int] | OffsetRange | SuffixRange
    """
    Request transfer of only the specified range of bytes.

    The semantics of this tuple are:

    - `(int, int)`: Request a specific range of bytes `(start, end)`.

        If the given range is zero-length or starts after the end of the object, an
        error will be returned. Additionally, if the range ends after the end of the
        object, the entire remainder of the object will be returned. Otherwise, the
        exact requested range will be returned.

        The `end` offset is _exclusive_.

    - `{"offset": int}`: Request all bytes starting from a given byte offset.

        This is equivalent to `bytes={int}-` as an HTTP header.

    - `{"suffix": int}`: Request the last `int` bytes. Note that here, `int` is _the
        size of the request_, not the byte offset. This is equivalent to `bytes=-{int}`
        as an HTTP header.

    <https://datatracker.ietf.org/doc/html/rfc9110#name-range>
    """

    version: str | None
    """
    Request a particular object version
    """

    head: bool
    """
    Request transfer of no content

    <https://datatracker.ietf.org/doc/html/rfc9110#name-head>
    """


class GetResult(Protocol):
    """Result for a get request.

    You can materialize the entire buffer by using `bytes`, or you can stream the result
    using `stream`. `__iter__` is implemented as an alias to `stream`, so you can
    alternatively call `iter()` on `GetResult` to start an iterator.

    **Example:**

    ```py
    resp = obs.get(store, path)
    # 20MB chunk size in stream
    stream = resp.stream(min_chunk_size=20 * 1024 * 1024)
    for buf in stream:
        print(len(buf))
    ```
    """

    @property
    def attributes(self) -> Attributes:
        """Additional object attributes."""
        ...

    def bytes(self) -> Buffer:
        """Collect the data into a `Buffer` object.

        This implements the Python buffer protocol. You can copy the buffer to Python
        memory by passing to [`bytes`][].
        """
        ...

    @property
    def meta(self) -> ObjectMeta:
        """The ObjectMeta for this object."""
        ...

    @property
    def range(self) -> tuple[int, int]:
        """The range of bytes returned by this request.

        Note that this is `(start, stop)` **not** `(start, length)`.
        """
        ...

    def stream(self, min_chunk_size: int = 10 * 1024 * 1024) -> BufferIterator:
        r"""Return a chunked stream over the result's bytes.

        Args:
            min_chunk_size: The minimum size in bytes for each chunk in the returned
                `BufferStream`. All chunks except for the last chunk will be at least
                this size. Defaults to 10\*1024\*1024 (10MB).

        Returns:
            A chunked stream

        """
        ...

    def __iter__(self) -> BufferStream:
        """Return a chunked stream over the result's bytes.

        Uses the default (10MB) chunk size.
        """
        ...


class GetResultAsync(Protocol):
    """Result for an async get request.

    You can materialize the entire buffer by using `bytes_async`, or you can stream the
    result using `stream`. `__aiter__` is implemented as an alias to `stream`, so you
    can alternatively call `aiter()` on `GetResult` to start an iterator.

    **Example:**

    ```py
    resp = await obs.get_async(store, path)
    # 5MB chunk size in stream
    stream = resp.stream(min_chunk_size=5 * 1024 * 1024)
    async for buf in stream:
        print(len(buf))
    ```
    """

    @property
    def attributes(self) -> Attributes:
        """Additional object attributes."""
        ...

    async def bytes_async(self) -> Buffer:
        """Collect the data into a `Buffer` object.

        This implements the Python buffer protocol. You can copy the buffer to Python
        memory by passing to [`bytes`][].
        """
        ...

    @property
    def meta(self) -> ObjectMeta:
        """The ObjectMeta for this object."""
        ...

    @property
    def range(self) -> tuple[int, int]:
        """The range of bytes returned by this request.

        Note that this is `(start, stop)` **not** `(start, length)`.

        """
        ...

    def stream(self, min_chunk_size: int = 10 * 1024 * 1024) -> BufferStream:
        r"""Return a chunked stream over the result's bytes.

        Args:
            min_chunk_size: The minimum size in bytes for each chunk in the returned
                `BufferStream`. All chunks except for the last chunk will be at least
                this size. Defaults to 10\*1024\*1024 (10MB).

        Returns:
            A chunked stream

        """
        ...

    def __aiter__(self) -> BufferStream:
        """Return a chunked stream over the result's bytes.

        Uses the default (10MB) chunk size.
        """
        ...


class BufferIterator(Protocol):
    """A synchronous iterator of bytes."""

    def __iter__(self) -> Self:
        """Return `Self` as an async iterator."""
        ...

    def __next__(self) -> Buffer:
        """Return the next Buffer chunk in the stream."""
        ...


class BufferStream(Protocol):
    """An asynchronous iterator of bytes."""

    def __aiter__(self) -> Self:
        """Return `Self` as an async iterator."""
        ...

    async def __anext__(self) -> Buffer:
        """Return the next Buffer chunk in the stream."""
        ...


class Get(Protocol):
    def get(
        self,
        path: str,
        *,
        options: GetOptions | None = None,
    ) -> GetResult:
        """Return the bytes that are stored at the specified location.

        Args:
            path: The path within ObjectStore to retrieve.
            options: options for accessing the file. Defaults to None.

        Returns:
            GetResult

        """
        ...


class GetAsync(Protocol):
    async def get_async(
        self,
        path: str,
        *,
        options: GetOptions | None = None,
    ) -> GetResultAsync:
        """Call `get` asynchronously.

        Refer to the documentation for [Get][obspec.Get].
        """
        ...


class GetRange(Protocol):
    def get_range(
        self,
        path: str,
        *,
        start: int,
        end: int | None = None,
        length: int | None = None,
    ) -> Buffer:
        """Return the bytes stored at the specified location in the given byte range.

        If the given range is zero-length or starts after the end of the object, an
        error will be returned. Additionally, if the range ends after the end of the
        object, the entire remainder of the object will be returned. Otherwise, the
        exact requested range will be returned.

        Args:
            path: The path within ObjectStore to retrieve.

        Keyword Args:
            start: The start of the byte range.
            end: The end of the byte range (exclusive). Either `end` or `length` must be
                non-None.
            length: The number of bytes of the byte range. Either `end` or `length` must
                be non-None.

        Returns:
            A `Buffer` object implementing the Python buffer protocol, allowing
                zero-copy access to the underlying memory provided by Rust.

        """
        ...


class GetRangeAsync(Protocol):
    async def get_range_async(
        self,
        path: str,
        *,
        start: int,
        end: int | None = None,
        length: int | None = None,
    ) -> Buffer:
        """Call `get_range` asynchronously.

        Refer to the documentation for [GetRange][obspec.GetRange].
        """
        ...


class GetRanges(Protocol):
    def get_ranges(
        self,
        path: str,
        *,
        starts: Sequence[int],
        ends: Sequence[int] | None = None,
        lengths: Sequence[int] | None = None,
    ) -> Sequence[Buffer]:
        """Return the bytes stored at the specified location in the given byte ranges.

        To improve performance this will:

        - Transparently combine ranges less than 1MB apart into a single underlying
          request
        - Make multiple `fetch` requests in parallel (up to maximum of 10)

        Args:
            path: The path within ObjectStore to retrieve.

        Other Args:
            starts: A sequence of `int` where each offset starts.
            ends: A sequence of `int` where each offset ends (exclusive). Either `ends`
                or `lengths` must be non-None.
            lengths: A sequence of `int` with the number of bytes of each byte range.
                Either `ends` or `lengths` must be non-None.

        Returns:
            A sequence of `Buffer`, one for each range. This `Buffer` object implements
            the Python buffer protocol, allowing zero-copy access to the underlying
            memory provided by Rust.

        """
        ...


class GetRangesAsync(Protocol):
    async def get_ranges_async(
        self,
        path: str,
        *,
        starts: Sequence[int],
        ends: Sequence[int] | None = None,
        lengths: Sequence[int] | None = None,
    ) -> Sequence[Buffer]:
        """Call `get_ranges` asynchronously.

        Refer to the documentation for [GetRanges][obspec.GetRanges].
        """
        ...
