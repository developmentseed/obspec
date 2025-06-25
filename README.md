# obspec

A Python protocol for interfacing with object storage.

[Read the release post.](https://developmentseed.org/obspec/latest/blog/2025/06/26/introducing-obspec-a-python-protocol-for-interfacing-with-object-storage/)

It's designed to abstract away the complexities of different object storage providers while acknowledging that object storage is _not a filesystem_. The Python protocols present more similarities to HTTP requests than Python file objects.

## Implementations

The primary implementation that implements obspec is [obstore](https://developmentseed.org/obstore/latest/), and the obspec protocol was designed around the obstore API.

## Utilities

There are planned to be utilities that build on top of obspec. Potentially:

- globbing: an implementation of `glob()` similar to [`fsspec.glob`](https://filesystem-spec.readthedocs.io/en/latest/api.html#fsspec.spec.AbstractFileSystem.glob) that uses `obspec` primitives.
- Caching: wrappers around `Get`/`GetRange`/`GetRanges` that store a cache of bytes.

By having these utilities operate on generic obspec protocols, it means that they can instantly be used with any future obspec backend.
