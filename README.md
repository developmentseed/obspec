# obspec

Object storage protocol definitions for Python.

## Background

Python defines two types of subtyping: [nominal and structural subtyping](https://docs.python.org/3/library/typing.html#nominal-vs-structural-subtyping). In essence, _nominal_ subtyping is subclassing. Class `A` is a nominal subtype of class `B` if `A` subclasses from `B`. _Structural_ subtyping is duck typing. Class `A` is a structural subtype of class `B` if `A` "looks like" `B`, that is, it _conforms to the same shape_ as `B`.

Using structural subtyping means that an ecosystem of libraries don't need to have any knowledge or dependency on each other, as long as they strictly and accurately implement the same duck-typed interface.

For example, an `Iterable` is a protocol. You don't need to subclass from a base `Iterable` class in order to make your type iterable. Instead, if you define an `__iter__` dunder method on your class, it _automatically becomes iterable_ because Python has a convention that if you see an `__iter__` method, you can call it to iterate over a sequence.

As another example, the [Buffer Protocol](https://docs.python.org/3/c-api/buffer.html) is a protocol to enable zero-copy exchange of binary data between Python libraries. Unlike `Iterable`, this is a protocol that is inaccessible in user Python code and only accessible at the C level, but it's still a protocol. Numpy can create arrays that view a buffer via the buffer protocol, even when Numpy has no prior knowledge of the library that produces the buffer.

Obspec defines core protocols to interface with data stored on file systems, remote object stores, etc.

## Usage

You should use the minimal methods required for your use case, **creating your own protocol** with just what you need.

In particular, Python allows you to [intersect protocols](https://typing.python.org/en/latest/spec/protocol.html#unions-and-intersections-of-protocols):

```py
from typing import Protocol

from obspec import Delete, Get, List, Put


class MyCustomObspecProtocol(Delete, Get, List, Put, Protocol):
    """My custom protocol."""
```

Then use that protocol generically:

```py
def do_something(backend: MyCustomObspecProtocol):
    backend.put("path.txt", b"hello world!")

    files = backend.list().collect()
    assert any(file["path"] == "path.txt" for file in files)

    assert backend.get("path.txt").bytes() == b"hello world!"

    backend.delete("path.txt")

    files = backend.list().collect()
    assert not any(file["path"] == "path.txt" for file in files)
```

In particular, by defining the most minimal interface you require, it widens the set of possible backends that can implement your interface. For example, making a range request is possible by any HTTP client, but a list call may have semantics not defined in the HTTP specification. So by only requiring, say, `Get` and `GetRange` you allow more implementations to be used with your program.

### Example: Cloud-Optimized GeoTIFF reader

A [Cloud-Optimized GeoTIFF (COG)](https://cogeo.org/) reader might only require range requests

```py
from typing import Protocol

from obspec import GetRange, GetRanges


class CloudOptimizedGeoTiffReader(GetRange, GetRanges, Protocol):
    """Protocol with necessary methods to read a Cloud-Optimized GeoTIFF file."""


def read_cog_header(backend: CloudOptimizedGeoTiffReader, path: str):
    # Make request for first 32KB of file
    header_bytes = backend.get_range(path, start=0, end=32 * 1024)

    # TODO: parse information from header
    raise NotImplementedError


def read_cog_image(backend: CloudOptimizedGeoTiffReader, path: str):
    header = read_cog_header(backend, path)

    # TODO: read image data from file.
```

An _async_ Cloud-Optimized GeoTIFF reader might instead subclass from obspec's async methods:

```py
from typing import Protocol

from obspec import GetRangeAsync, GetRangesAsync


class AsyncCloudOptimizedGeoTiffReader(GetRangeAsync, GetRangesAsync, Protocol):
    """Necessary methods to asynchronously read a Cloud-Optimized GeoTIFF file."""


async def read_cog_header(backend: AsyncCloudOptimizedGeoTiffReader, path: str):
    # Make request for first 32KB of file
    header_bytes = await backend.get_range_async(path, start=0, end=32 * 1024)

    # TODO: parse information from header

    raise NotImplementedError


async def read_cog_image(backend: AsyncCloudOptimizedGeoTiffReader, path: str):
    header = await read_cog_header(backend, path)

    # TODO: read image data from file.
```

## Implementations

The primary implementation that implements obspec is [obstore](https://developmentseed.org/obstore/latest/), and the obspec protocol was designed around the obstore API.

## Utilities

There are planned to be utilities that build on top of obspec. Potentially:

- globbing: an implementation of `glob()` similar to [`fsspec.glob`](https://filesystem-spec.readthedocs.io/en/latest/api.html#fsspec.spec.AbstractFileSystem.glob) that uses `obspec` primitives.
- Caching: wrappers around `Get`/`GetRange`/`GetRanges` that store a cache of bytes.

By having these utilities operate on generic obspec protocols, it means that they can instantly be used with any future obspec backend.
