from __future__ import annotations

from typing import Protocol


class Rename(Protocol):
    def rename(self, from_: str, to: str, *, overwrite: bool = True) -> None:
        """Move an object from one path to another in the same object store.

        By default, this is implemented as a copy and then delete source. It may not
        check when deleting source that it was the same object that was originally
        copied.

        Args:
            from_: Source path
            to: Destination path

        Keyword Args:
            overwrite: If `True`, if there exists an object at the destination, it will
                be overwritten. If `False`, will return an error if the destination
                already has an object.

        """


class RenameAsync(Protocol):
    async def rename_async(
        self,
        from_: str,
        to: str,
        *,
        overwrite: bool = True,
    ) -> None:
        """Call `rename` asynchronously.

        Refer to the documentation for [Rename][obspec.Rename].
        """
