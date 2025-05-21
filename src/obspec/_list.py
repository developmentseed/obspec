from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Generic, Protocol, TypedDict, TypeVar

if TYPE_CHECKING:
    import sys
    from collections.abc import Sequence

    from ._meta import ObjectMeta

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


ListChunkType_co = TypeVar("ListChunkType_co", covariant=True)
"""The data structure used for holding list results."""


class ListResult(TypedDict, Generic[ListChunkType_co]):
    """Result of a `list_with_delimiter` call.

    Includes objects, prefixes (directories) and a token for the next set of results.
    Individual result sets may be limited to 1,000 objects based on the underlying
    object storage's limitations.
    """

    common_prefixes: Sequence[str]
    """Prefixes that are common (like directories)"""

    objects: ListChunkType_co
    """Object metadata for the listing"""


class ListIterator(Protocol[ListChunkType_co]):
    """A stream of [ObjectMeta][obspec.ObjectMeta] that can be polled synchronously."""

    def __iter__(self) -> Self:
        """Return `Self` as an async iterator."""
        ...

    def collect(self) -> ListChunkType_co:
        """Collect all remaining ObjectMeta objects in the stream.

        This ignores the `chunk_size` parameter from the `list` call and collects all
        remaining data into a single chunk.
        """
        ...

    def __next__(self) -> ListChunkType_co:
        """Return the next chunk of ObjectMeta in the stream."""
        ...


class ListStream(Protocol[ListChunkType_co]):
    """A stream of [ObjectMeta][obspec.ObjectMeta] that can be polled asynchronously."""

    def __aiter__(self) -> Self:
        """Return `Self` as an async iterator."""
        ...

    async def collect_async(self) -> ListChunkType_co:
        """Collect all remaining ObjectMeta objects in the stream.

        This ignores the `chunk_size` parameter from the `list` call and collects all
        remaining data into a single chunk.
        """
        ...

    async def __anext__(self) -> ListChunkType_co:
        """Return the next chunk of ObjectMeta in the stream."""
        ...


class List(Protocol):
    def list(
        self,
        prefix: str | None = None,
        *,
        offset: str | None = None,
        chunk_size: int = 50,
    ) -> ListIterator[Sequence[ObjectMeta]]:
        """List all the objects with the given prefix.

        Prefixes are evaluated on a path segment basis, i.e. `foo/bar/` is a prefix of
        `foo/bar/x` but not of `foo/bar_baz/x`. List is recursive, i.e. `foo/bar/more/x`
        will be included.

        **Examples**:

        Synchronously iterate through list results:

        ```py
        import obstore as obs
        from obstore.store import MemoryStore

        store = MemoryStore()
        for i in range(100):
            obs.put(store, f"file{i}.txt", b"foo")

        stream = obs.list(store, chunk_size=10)
        for list_result in stream:
            print(list_result[0])
            # {'path': 'file0.txt', 'last_modified': datetime.datetime(2024, 10, 23, 19, 19, 28, 781723, tzinfo=datetime.timezone.utc), 'size': 3, 'e_tag': '0', 'version': None}
            break
        ```

        !!! note
            The order of returned [`ObjectMeta`][obspec.ObjectMeta] is not
            guaranteed

        Args:
            prefix: The prefix within ObjectStore to use for listing. Defaults to None.

        Keyword Args:
            offset: If provided, list all the objects with the given prefix and a
                location greater than `offset`. Defaults to `None`.
            chunk_size: The number of items to collect per chunk in the returned
                (async) iterator. All chunks except for the last one will have this many
                items. This is ignored in [`collect`][obspec.ListIterator.collect].

        Returns:
            A ListStream, which you can iterate through to access list results.

        """  # noqa: E501
        ...


class ListAsync(Protocol):
    def list_async(
        self,
        prefix: str | None = None,
        *,
        offset: str | None = None,
        chunk_size: int = 50,
    ) -> ListStream[Sequence[ObjectMeta]]:
        """List all the objects with the given prefix.

        Note that this method itself is **not async**. It's a synchronous method but
        returns an **async iterator**.

        Refer to [obspec.List][obspec.List] for more information about list semantics.

        **Examples**:

        Asynchronously iterate through list results. Just change `for` to `async for`:

        ```py
        stream = obs.list_async(store, chunk_size=10)
        async for list_result in stream:
            print(list_result[2])
            # {'path': 'file10.txt', 'last_modified': datetime.datetime(2024, 10, 23, 19, 21, 46, 224725, tzinfo=datetime.timezone.utc), 'size': 3, 'e_tag': '10', 'version': None}
            break
        ```

        !!! note
            The order of returned [`ObjectMeta`][obspec.ObjectMeta] is not
            guaranteed

        Args:
            prefix: The prefix within ObjectStore to use for listing. Defaults to None.

        Keyword Args:
            offset: If provided, list all the objects with the given prefix and a
                location greater than `offset`. Defaults to `None`.
            chunk_size: The number of items to collect per chunk in the returned
                (async) iterator. All chunks except for the last one will have this many
                items. This is ignored in
                [`collect_async`][obspec.ListStream.collect_async].

        Returns:
            A ListStream, which you can iterate through to access list results.

        """  # noqa: E501
        ...


class ListWithDelimiter(Protocol):
    def list_with_delimiter(
        self,
        prefix: str | None = None,
    ) -> ListResult[Sequence[ObjectMeta]]:
        """List objects with the given prefix and an implementation specific
        delimiter.

        Returns common prefixes (directories) in addition to object
        metadata.

        Prefixes are evaluated on a path segment basis, i.e. `foo/bar/` is a prefix of
        `foo/bar/x` but not of `foo/bar_baz/x`. This list is not recursive, i.e.
        `foo/bar/more/x` will **not** be included.

        !!! note

            Any prefix supplied to this `prefix` parameter will **not** be stripped off
            the paths in the result.

        Args:
            prefix: The prefix within ObjectStore to use for listing. Defaults to None.

        Returns:
            ListResult

        """  # noqa: D205
        ...


class ListWithDelimiterAsync(Protocol):
    async def list_with_delimiter_async(
        self,
        prefix: str | None = None,
    ) -> ListResult[Sequence[ObjectMeta]]:
        """Call `list_with_delimiter` asynchronously.

        Refer to the documentation for
        [ListWithDelimiter][obspec.ListWithDelimiter].
        """
        ...
