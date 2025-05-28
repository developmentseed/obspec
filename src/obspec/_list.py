from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Generic, Protocol, TypeVar

# Note: we need to use the typing-extensions typed dict because we also parametrize over
# a generic
# https://stackoverflow.com/a/79300271
if sys.version_info >= (3, 11):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator, Sequence

    from ._meta import ObjectMeta


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


class List(Protocol):
    def list(
        self,
        prefix: str | None = None,
        *,
        offset: str | None = None,
    ) -> Iterator[Sequence[ObjectMeta]]:
        """List all the objects with the given prefix.

        Prefixes are evaluated on a path segment basis, i.e. `foo/bar/` is a prefix of
        `foo/bar/x` but not of `foo/bar_baz/x`. List is recursive, i.e. `foo/bar/more/x`
        will be included.

        **Examples**:

        Synchronously iterate through list results:

        ```py
        import obspec

        def upload_files(client: obspec.Put):
            for i in range(100):
                client.put(f"file{i}.txt", b"foo")

        def list_files(client: obspec.List):
            stream = client.list()
            for list_result in stream:
                print(list_result[0])
                # {'path': 'file0.txt', 'last_modified': datetime.datetime(2024, 10, 23, 19, 19, 28, 781723, tzinfo=datetime.timezone.utc), 'size': 3, 'e_tag': '0', 'version': None}
                break
        ```

        !!! note
            The order of returned [`ObjectMeta`][obspec.ObjectMeta] is not
            guaranteed

        Args:
            prefix: The prefix within the store to use for listing. Defaults to None.

        Keyword Args:
            offset: If provided, list all the objects with the given prefix and a
                location greater than `offset`. Defaults to `None`.

        Returns:
            A ListIterator, which you can iterate through to access list results.

        """  # noqa: E501
        ...


class ListAsync(Protocol):
    def list_async(
        self,
        prefix: str | None = None,
        *,
        offset: str | None = None,
    ) -> AsyncIterator[Sequence[ObjectMeta]]:
        """List all the objects with the given prefix.

        Note that this method itself is **not async**. It's a synchronous method but
        returns an **async iterator**.

        Refer to [obspec.List][obspec.List] for more information about list semantics.

        **Examples**:

        Asynchronously iterate through list results. Just change `for` to `async for`:

        ```py
        stream = obs.list_async(store)
        async for list_result in stream:
            print(list_result[2])
            # {'path': 'file10.txt', 'last_modified': datetime.datetime(2024, 10, 23, 19, 21, 46, 224725, tzinfo=datetime.timezone.utc), 'size': 3, 'e_tag': '10', 'version': None}
            break
        ```

        !!! note
            The order of returned [`ObjectMeta`][obspec.ObjectMeta] is not
            guaranteed

        Args:
            prefix: The prefix within the store to use for listing. Defaults to None.

        Keyword Args:
            offset: If provided, list all the objects with the given prefix and a
                location greater than `offset`. Defaults to `None`.

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
            prefix: The prefix within the store to use for listing. Defaults to None.

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
