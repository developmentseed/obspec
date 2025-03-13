from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("obspec")
except PackageNotFoundError:
    __version__ = "uninstalled"
