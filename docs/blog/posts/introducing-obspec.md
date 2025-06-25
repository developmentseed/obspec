---
draft: false
date: 2025-06-26
categories:
  - Release
authors:
  - kylebarron
---

# Introducing Obspec: A Python protocol for interfacing with object storage

Obspec defines a minimal, transparent Python interface to read, write, and modify data on object storage.

It's designed to abstract away the complexities of different object storage providers while acknowledging that object storage is _not a filesystem_. The Python protocols present more similarities to HTTP requests than Python file objects.

<!-- more -->

<!-- ## Why a new interface? -->

The primary existing Python specification used for object storage is [fsspec](https://filesystem-spec.readthedocs.io/en/latest/), which defines a filesystem-like interface based around Python file-like objects.

However this presents an impedance mismatch: **object storage is not a filesystem** and does not have the same semantics as filesystems. This leads to surprising behavior, poor performance, and integration complexity.

## File-like, stateful APIs add ambiguity

Fsspec has significant layers of caching to try to make object storage behave _like_ a filesystem, but this also causes unpredictable results.

### Fsspec: Opaque list caching

Take the following example. Is the list request cached? How many requests are made, one or two? What happens if the remote data changes? Will the second list automatically reflect new data?

```py
from time import sleep
from fsspec import AbstractFileSystem

def list_files_twice(fs: AbstractFileSystem):
    fs.ls("s3://mybucket")
    sleep(5)
    fs.ls("s3://mybucket")
```

Because [`AbstractFileSystem.ls`][fsspec.spec.AbstractFileSystem.ls] returns a _fully-materialized_ `list` and there can be thousands of items in a bucket, fsspec implementations tend to use some sort of internal caching. Furthermore, the specification explicitly allows for caching by defining a keyword argument named `refresh`. But the API documentation for `ls` [doesn't say][fsspec.spec.AbstractFileSystem.ls] what the default for `refresh` is (only that you _may_ explicitly pass `refresh=True|False` to force a behavior).

You have to read implementation-specific source code to find out that, in the case of [`s3fs`](https://github.com/fsspec/s3fs), the fsspec implementation for S3, the [default is `refresh=False`](https://github.com/fsspec/s3fs/blob/ec57f88c057dfd29fa1db80db423832fbfa4832a/s3fs/core.py#L1021). So in the case of `s3fs`, the list call _is cached_, only one HTTP request is made, and the second call to `ls` will not reflect new data without an explicit call to `refresh=True`.

But the design of the abstraction means that it's very difficult for generic code operating on the abstract base class to infer from the function signature how many HTTP requests will be made by most implementations.

### Obstore: Streaming list

In contrast, obspec relies on iterators wherever possible. The [`obspec.List`][] protocol returns an iterator of metadata about files, which enables stateless implementations that map much more closely to the underlying HTTP requests.

```py
from time import sleep
from obspec import List

def list_files_twice(client: List):
    list_items = list(client.list("prefix"))
    sleep(5)
    list_items = list(client.list("prefix"))
```

There's no internal caching, a set of possibly-multiple requests are made for each call to `list`, and each call to `list` will reflect the latest state of the bucket.

### Fsspec: Opaque file downloads

Consider the options fsspec provides for downloading data. Fsspec doesn't have a method to stream a file download into memory, so your options are:

1. Materialize the entire file in memory, which is not practical for large files.
2. Make targeted range requests, which requires you to know the byte ranges you want to download and requires multiple HTTP calls.
3. Use a file-like object, which is not clear how many HTTP requests it will make, and how caching works.
4. Download to a local file, which incurs overhead of writing to disk and then reading back into memory.

Suppose we choose option 3, using a file-like object. It's fully opaque how many requests are being made:

```py
from fsspec import AbstractFileSystem

def iterate_over_file_object(fs: AbstractFileSystem, path: str):
    with fs.open(path) as f:
        for line in f:
            print(line.strip())
```

### Obspec: Streaming download

By mapping more closely to the underlying HTTP requests, obspec makes it clearer what HTTP requests are happening under the hood. [obspec.Get] allows for streaming a file download via a Python iterator:

```py
from obspec import Get

def download_file(client: Get):
    response = client.get("my-file.txt")
    for buffer in response:
        # Process each buffer chunk as needed
        print(f"Received buffer of size: {len(memoryview(buffer))} bytes")
```

In this case, only one HTTP request is made, and you can start processing the data as it arrives without needing to materialize the entire file in memory.

### Support for functionality not native to filesystems

Obspec allows for functionality not native to filesystems, such as preconditions (fetch if unmodified) and atomic multipart uploads.

## Native Async support

Fsspec was originally designed for synchronous I/O. Async support was bolted on via async versions of methods, but the core architecture is still sync-first and the async support is relatively sparsely documented.

The async support in fsspec is intentionally hidden away: all async operations are named with a leading underscore and in effect "private" and not designed to be visible by most users. Additionally some "async" calls in fsspec just use `loop.run_in_executor(...)` to perform the work in a thread in the background.

In 2025, the Python async ecosystem has progressed to the point where an interface should provide **first-class support for async code**. All obspec functionality is defined in matching sync and async protocols with clear separation between the two.

## API Surface

The fsspec API surface is _quite large_. [`AbstractFileSystem`][fsspec.spec.AbstractFileSystem] defines around 10 public attributes and 56 public methods. [`AbstractBufferedFile`][fsspec.spec.AbstractBufferedFile] defines around 20 public methods. And that's not including the async implementation in [`AsyncFileSystem`][fsspec.asyn.AsyncFileSystem].

Aside from being difficult for backends to implement the full surface area, it's also common to hit `NotImplementedError` at runtime when a backend doesn't support the method you're using.

Obspec has a **much smaller API surface** than fsspec, which makes it easier to understand, implement, and compose. Obspec has just 10 core methods with synchronous and asynchronous variants:

- [`copy`][obspec.Copy]/[`copy_async`][obspec.CopyAsync]: Copy an object within the same store.
- [`delete`][obspec.Delete]/[`delete_async`][obspec.DeleteAsync]: Delete an object.
- [`get`][obspec.Get]/[`get_async`][obspec.GetAsync]: Download a file, returning an iterator or async iterator of buffers.
- [`get_range`][obspec.GetRange]/[`get_range_async`][obspec.GetRangeAsync]: Get a single byte range.
- [`get_ranges`][obspec.GetRanges]/[`get_ranges_async`][obspec.GetRangesAsync]: Get multiple byte ranges.
- [`head`][obspec.Head]/[`head_async`][obspec.HeadAsync]: Access file metadata.
- [`list`][obspec.List]/[`list_async`][obspec.ListAsync]: List objects, returning an iterator or async iterator of metadata.
- [`list_with_delimiter`][obspec.ListWithDelimiter]/[`list_with_delimiter_async`][obspec.ListWithDelimiterAsync]: List objects within a specific directory.
- [`put`][obspec.Put]/[`put_async`][obspec.PutAsync]: Upload a file, buffer, or iterable of buffers.
- [`rename`][obspec.Rename]/[`rename_async`][obspec.RenameAsync]: Move an object from one path to another within the same store.

This smaller API surface also means that it's much rarer to get a runtime `NotImplementedError`.

## Static typing support

Fsspec hardly has any support for static typing, which makes it hard for a user to know they're using the interface correctly.

Obspec is **fully statically typed**. This provides excellent in-editor documentation and autocompletion, as well as static warnings when the interface is used incorrectly.


<!-- 1. api surface area of obspec vs fsspec. moving away from trying to make a file system layer which is a poor semantic mismatch and causes confusion and overhead.

2. We don't have any implementation logic inside of obstore. A lot of baked-in fsspec logic is going to go away. If you want to have implementation-specific logic, it can be on top of obspec instead of having to go into obspec and understand what's going on.
 -->

## Protocols & duck typing, not subclassing

Python defines two types of subtyping: [nominal and structural subtyping](https://docs.python.org/3/library/typing.html#nominal-vs-structural-subtyping).

In essence, _nominal_ subtyping means _subclassing_. Class `A` is a nominal subtype of class `B` if `A` subclasses from `B`. _Structural_ subtyping means _duck typing_. Class `A` is a structural subtype of class `B` if `A` "looks like" `B`, that is, it _conforms to the same shape_ as `B`.

Using structural subtyping means that an ecosystem of libraries don't need to have any knowledge or dependency on each other, as long as they strictly and accurately implement the same duck-typed interface.

For example, an `Iterable` is a protocol. You don't need to subclass from a base `Iterable` class in order to make your type iterable. Instead, if you define an `__iter__` dunder method on your class, it _automatically becomes iterable_ because Python has a convention that if you see an `__iter__` method, you can call it to iterate over a sequence.

As another example, the [Buffer Protocol](https://docs.python.org/3/c-api/buffer.html) is a protocol to enable zero-copy exchange of binary data between Python libraries. Unlike `Iterable`, this is a protocol that is inaccessible in user Python code and only accessible at the C level, but it's still a protocol. Numpy can create arrays that view a buffer via the buffer protocol, even when Numpy has no prior knowledge of the library that produces the buffer.

Obspec relies on structural subtyping to provide flexibility to implementors while not requiring them to take an explicit dependency on obspec, which would be required to subclass from obspec using nominal subtyping.


## Existing implementations

[Obstore](https://developmentseed.org/obstore/latest/) is the primary existing implementation of obspec. Indeed, obspec's API is essentially a simplified formalization of obstore's existing API.

We'd like to see additional future first-party and third-party implementations of the obspec protocol.

## Example: Caching wrapper

Obspec does not have any built-in caching logic. This is a deliberate design choice to keep the interface simple and predictable. Caching can be implemented as a wrapper around obspec, allowing users to choose their caching strategy without complicating the core interface.

Here we have a very simple example of this approach. `SimpleCache` is a wrapper class around something implementing the `GetRange` protocol. The `SimpleCache` manages caching logic itself _outside the underlying `GetRange` backend_. But since `SimpleCache` also implements `GetRange`, it can be used wherever `GetRange` is expected.

```py
from __future__ import annotations
from typing_extensions import Buffer
from obspec import GetRange

class SimpleCache(GetRange):
    """A simple cache for synchronous range requests that never evicts data."""

    def __init__(self, client: GetRange):
        self.client = client
        self.cache: dict[tuple[str, int, int | None, int | None], Buffer] = {}

    def get_range(
        self,
        path: str,
        *,
        start: int,
        end: int | None = None,
        length: int | None = None,
    ) -> Buffer:
        cache_key = (path, start, end, length)
        if cache_key in self.cache:
            return self.cache[cache_key]

        response = self.client.get_range(
            path,
            start=start,
            end=end,
            length=length,
        )
        self.cache[cache_key] = response
        return response
```

Of course, a real implementation would be smarter than just caching the exact byte range, and might use something like block caching.

Now if `GetRange` is expected to be used like so:

```py
def my_function(client: GetRange, path: str, *, start: int, end: int):
    buffer = client.get_range(path, start=start, end=end)
    # Do something with the buffer
    print(len(memoryview(buffer)))
```

Then a user can seamlessly insert the `SimpleCache` in the middle. The second request will be cached and not reach the S3Store

```py
from obstore.store import S3Store

store = S3Store("bucket")
caching_wrapper = SimpleCache(store)
my_function(caching_wrapper, "path.txt", start=0, end=10)
my_function(caching_wrapper, "path.txt", start=0, end=10)
```

## Usage for downstream libraries

Not all backends will necessarily support all features. Obspec is defined as a set of _independent_ protocols to allow libraries depending on obspec to verify that obspec implementations provide all required functionality.

In particular, Python allows you to [intersect protocols](https://typing.python.org/en/latest/spec/protocol.html#unions-and-intersections-of-protocols). Thus, you should use the most minimal methods required for your use case, **creating your own subclassed protocol** with just what you need.

```py
from typing import Protocol
from obspec import Delete, Get, List, Put


class MyCustomObspecProtocol(Delete, Get, List, Put, Protocol):
    """
    My custom protocol with functionality required in a downstream library.
    """
```

Then use that protocol generically:

```py
def do_something(backend: MyCustomObspecProtocol):
    backend.put("path.txt", b"hello world!")

    files = list(backend.list())
    assert any(file["path"] == "path.txt" for file in files)

    assert memoryview(backend.get("path.txt").buffer()) == b"hello world!"

    backend.delete("path.txt")

    files = list(backend.list())
    assert not any(file["path"] == "path.txt" for file in files)
```

By defining the most minimal interface you require, it widens the set of possible backends that can implement your interface. For example, making a range request is possible by any HTTP client, but a list call may have semantics not defined in the HTTP specification. So by only requiring, say, `Get` and `GetRange` you allow more implementations to be used with your program.

Alternatively, if you only require a single method, there's no need to create your own custom protocol, and you can use the obspec protocol directly.

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
