from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Literal, Self, TypeVar, overload

from arro3.core import RecordBatch, Table

from obspec._meta import ObjectMeta

if TYPE_CHECKING:
    import obspec


def test_list_arrow_compatible():
    ListChunkType = TypeVar("ListChunkType", list[ObjectMeta], RecordBatch, Table)

    class ListStream(Generic[ListChunkType]):
        def __aiter__(self) -> Self:
            """Return `Self` as an async iterator."""
            ...

        def __iter__(self) -> Self:
            """Return `Self` as an async iterator."""
            ...

        async def collect_async(self) -> ListChunkType:
            """Collect all remaining ObjectMeta objects in the stream.

            This ignores the `chunk_size` parameter from the `list` call and collects all
            remaining data into a single chunk.
            """
            ...

        def collect(self) -> ListChunkType:
            """Collect all remaining ObjectMeta objects in the stream.

            This ignores the `chunk_size` parameter from the `list` call and collects all
            remaining data into a single chunk.
            """
            ...

        async def __anext__(self) -> ListChunkType:
            """Return the next chunk of ObjectMeta in the stream."""
            ...

        def __next__(self) -> ListChunkType:
            """Return the next chunk of ObjectMeta in the stream."""
            ...

    class ObstoreList:
        @overload
        def list(
            self,
            prefix: str | None = None,
            *,
            offset: str | None = None,
            chunk_size: int = 50,
            return_arrow: Literal[True],
        ) -> ListStream[RecordBatch]: ...
        @overload
        def list(
            self,
            prefix: str | None = None,
            *,
            offset: str | None = None,
            chunk_size: int = 50,
            return_arrow: Literal[False] = False,
        ) -> ListStream[list[ObjectMeta]]: ...
        def list(
            self,
            prefix: str | None = None,
            *,
            offset: str | None = None,
            chunk_size: int = 50,
            return_arrow: bool = False,
        ) -> ListStream[RecordBatch] | ListStream[list[ObjectMeta]]:
            pass

    def accepts_obspec_list(provider: obspec.List):
        pass

    accepts_obspec_list(ObstoreList())
