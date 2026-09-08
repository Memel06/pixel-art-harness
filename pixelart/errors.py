class PixelartError(Exception):
    """Expected user-facing error from the harness."""


class SceneError(PixelartError):
    """A scene file does not satisfy the compact drawing DSL."""


class AsepriteNotFound(PixelartError):
    """No usable Aseprite executable was found."""
