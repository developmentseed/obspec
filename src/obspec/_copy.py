from __future__ import annotations

from typing import Protocol


class Copy(Protocol):
    def copy(self, from_: str, to: str, *, overwrite: bool = True) -> None:
        """Copy an object from one path to another in the same object store.

        All paths should be a fragment relative to the bucket root or any prefix already
        assigned on the store. I.e. `path/to/file.txt`, not
        `s3://bucket/path/to/file.txt`.

        Args:
            from_: Source path.
            to: Destination path

        Keyword Args:
            overwrite: whether to overwrite the destination object if one already
                exists.

                - If `True`, if there exists an object at the destination, it will
                    be overwritten.

                - If `False`: will copy only if destination is empty. Performs an atomic
                operation if the underlying object storage supports it. If atomic
                operations are not supported by the underlying object storage it will
                return an error.

                    Will return an error if the destination already has an object.

        """


class CopyAsync(Protocol):
    async def copy_async(
        self,
        from_: str,
        to: str,
        *,
        overwrite: bool = True,
    ) -> None:
        """Call `copy` asynchronously.

        Refer to the documentation for [Copy][obspec.Copy].
        """
