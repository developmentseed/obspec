---
draft: false
date: 2025-05-29
categories:
  - Release
authors:
  - kylebarron
---

# Introducing Obspec: A Python protocol for interfacing with object storage

Obspec defines a minimal, transparent Python interface for object storage.

It's designed to abstract away the complexities of different object storage APIs while acknowledging that object storage is _not a filesystem_ and presents more similarities to HTTP requests than Python file objects.

<!-- more -->

## Why a new interface?

The primary existing Python specification used for object storage is [fsspec](https://filesystem-spec.readthedocs.io/en/latest/), which defines a filesystem-like interface based around Python file-like objects.

However this presents an impedance mismatch: object storage is not a filesystem and does not have the same semantics as filesystems. This leads to surprising behavior, poor performance, and integration complexity

### Fsspec's stateful APIs add user uncertainty.

Fsspec has significant layers of caching to try to make object storage behave _like_ a filesystem, but this also causes unpredictable results.

#### Opaque list requests

Take the following example. Is the list request cached? How many requests are made, one or two? What happens if the remote data changes? Will the second list automatically reflect new data?

```py
from time import sleep
from fsspec import AbstractFileSystem

def list_files_twice(fs: AbstractFileSystem):
    fs.ls("s3://mybucket")
    sleep(5)
    fs.ls("s3://mybucket")
```

The API documentation for `ls` [doesn't say](https://filesystem-spec.readthedocs.io/en/latest/api.html#fsspec.spec.AbstractFileSystem.ls) what the default is (only that you _may_ explicitly pass `refresh=True|False` to force a behavior). You have to read implementation-specific source code to find out that, in the case of `s3fs`, the [default is `refresh=False`](https://github.com/fsspec/s3fs/blob/ec57f88c057dfd29fa1db80db423832fbfa4832a/s3fs/core.py#L1021). So the list call is cached, only one HTTP request is made, and the second call to `ls` will not reflect new data without an explicit call to `refresh=True`.

In contrast, since obspec is stateless and abstracts HTTPs requests, not files, the comparable obspec code is easier to understand and reason about.

```py
from time import sleep
from obspec import List

def list_files_twice(client: List):
    list_items = list(client.list("prefix"))
    sleep(5)
    list_items = list(client.list("prefix"))
```

There's no internal caching, two requests are made, and every `list` method call will reflect the latest state of the bucket.

#### Opaque file downloads

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

In contrast, obspec makes it fully transparent what HTTP requests are happening under the hood. Obspec also allows for streaming a file via a Python iterator:

```py
from obspec import Get

def download_file(client: Get):
    response = client.get("my-file.txt")
    for buffer in response:
        # Process each buffer chunk as needed
        print(f"Received buffer of size: {len(memoryview(buffer))} bytes")
```

Only one HTTP request is made, and you can start processing the data as it arrives without needing to materialize the entire file in memory.

----------

Consistent interface to object storage.



- Obspec grew out of obstore.

Comparison to obstore: Obstore is a concrete implementation; obspec is an abstract interface using Python protocols.

Builds on a series of known protocols. Uses the buffer protocol for representing binary data.

## Compare and contrast to fsspec

1. api surface area of obspec vs fsspec. moving away from trying to make a file system layer which is a poor semantic mismatch and causes confusion and overhead.

2. We don't have any implementation logic inside of obstore. A lot of baked-in fsspec logic is going to go away. If you want to have implementation-specific logic, it can be on top of obspec instead of having to go into obspec and understand what's going on.

### Abstraction target

Fsspec:
Access remote data via stateful file objects



```py
from fsspec import AbstractFileSystem


def download_file(fs: AbstractFileSystem) -> str:
    with fs.open("my-file.txt", "rb") as f:
        return f.read().decode()
```


Obstore: HTTP requests

Access remote data via HTTP-like requests
All operations are atomic (readers cannot observe partial/failed writes)
Allows for functionality not native to filesystems
Operation preconditions (fetch if unmodified)
Atomic multipart uploads



```py
from obspec import Get


def download_file(client: Get) -> str:
    response = client.get("my-file.txt")
    # buffer is only known to implement the Buffer Protocol
    buffer = response.bytes()
    return bytes(buffer).decode()
```

!!! note

    Core point: mismatched abstraction, object stores are not filesystems.

### Stateful vs Stateless

Core point: stateful APIs add user uncertainty.
Is the list request cached?
How many requests are made?
What happens if the remote data changes?
Will the second list automatically reflect new data?


We want a clear contract between provider (backend) and consumer (user/library)
Is the list request cached? (yes)
How many requests does this make? (1)
What happens if the remote data changes?
Will the second list automatically reflect new data? (no, not by default, but could be implementation dependent)


```py
from time import sleep

from fsspec import AbstractFileSystem


def list_files_twice(fs: AbstractFileSystem):
    fs.ls("s3://mybucket")
    sleep(5)
    fs.ls("s3://mybucket")
```

```py
from time import sleep

from obspec import List


def list_files_twice(client: List):
    list_iter = client.list("prefix")
    list_items = list(list_iter)
    sleep(5)
    list_iter = client.list("prefix")
    list_items = list(list_iter)
```

### API Surface

Core point: obstore has a smaller API surface, easier to understand, compose.

Fsspec:

AbstractFileSystem: 10 public attributes, 56 public methods, more public async methods
AbstractBufferedFile: 20 public methods
Common to hit NotImplementedError since not all backends support all filesystem concepts (e.g. async)

Obstore:

Just 11 methods total: Core operations that object stores support natively
Full clarity of underlying HTTP calls
E.g. opening an fsspec file and then iterating over the responses… unclear how many raw HTTP requests that translates into.
Predictable performance.
No automatic caching (to be provided on top)
Very rare NotImplementedError: Azure suffix requests


copy/copy_async: Copy an object
delete/delete_async: Delete an object
get: Download a file
get_range/get_range_async: Get a byte range
get_ranges/get_ranges_async: Get multiple byte ranges
head/head_async: Access file metadata
list: List objects
list_with_delimiter/list_with_delimiter_async: List objects within a specific “directory”, avoiding recursing into further directories.
put/put_async: Upload to file
rename/rename_async: Move an object from one path to another
sign/sign_async: Create a signed URL

### Streaming

Core point: obstore has full streaming support.

Fsspec:

Streaming download: No support.
Can be emulated with file object, but no way to make one request and have it return as a stream.
Streaming upload: supported synchronously by passing file-like object.
Streaming list: No support: ls will always return all objects within prefix.


Both sync and async streaming support.
Streaming download: start working with byte response before entire file has downloaded.
Streaming upload: upload data from any byte source without materializing everything in memory.
Streaming list: automatic pagination behind the scenes

Streaming download:

```py
from obspec import Get


def streaming_download(client: Get):
    response = client.get("file.txt")
    for buffer_chunk in response:
        # The iteration object is again a Buffer Protocol object
        print(len(memoryview(buffer_chunk)))
```

Async streaming download. In just a few lines of code we can switch to supporting async.


```py
from obspec import GetAsync


async def streaming_download(client: GetAsync):
    response = await client.get_async("file.txt")
    async for buffer_chunk in response:
        # The iteration object is again a Buffer Protocol object
        print(len(memoryview(buffer_chunk)))
```




### Intersecting features

Not all backends will support all features.

This is why obspec is defined as a set of independent protocols. Users can intersect the ones they need.

### Full async API

### Type hinting

Fully type hinted

### Manner of subtyping

As [described in the Mypy documentation](https://mypy.readthedocs.io/en/stable/protocols.html), the Python type system supports two different manners of subtyping.

> _Nominal_ subtyping is strictly based on the class hierarchy. If class `Dog`
> inherits class `Animal`, it's a subtype of `Animal`. Instances of `Dog`
> can be used when `Animal` instances are expected. This form of subtyping
> is what Python's type system predominantly uses: it's easy to
> understand and produces clear and concise error messages, and matches how the
> native :py:func:`isinstance <isinstance>` check works -- based on class
> hierarchy.
>
> _Structural_ subtyping is based on the operations that can be performed with
> an object. Class `Dog` is a structural subtype of class `Animal` if the former
> has all attributes and methods of the latter, and with compatible types.
>
> Structural subtyping can be seen as a static equivalent of duck typing, which
> is well known to Python programmers.

Fsspec uses nominal subtyping.

Obspec uses structural subtyping.


### Predictability

We don't have any implementation logic inside of obstore. A lot of baked-in fsspec logic is going to go away. If you want to have implementation-specific logic, it can be on top of obspec instead of having to go into obspec and understand what's going on.

#### Caching

Fsspec has caching built in. This can cause unpredictable results.

With obspec, the idea is to provide the low-level primitives and caching can be implemented _as wrappers_ on top of

### Dependencies?

Talk about protocols?

## Implemented by obstore

Protocols are worthless if a concrete implementation doesn't exist.

Obstore is a zero-dependency implementation.


## Future work

### Common exceptions
