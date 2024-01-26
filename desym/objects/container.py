from __future__ import annotations
from typing import Generic, TypeVar

ContentType = TypeVar("ContentType")

ContainerId = str


class Container(Generic[ContentType]):
    def __init__(self, id: str, content: ContentType | None = None):
        self.id = id
        self.content = content

    def __str__(self) -> str:
        return f"Tray {self.id}{f' with {self.content}' if self.content else ''}"

    def load(self, content: ContentType) -> bool:
        if self.content:
            raise Exception("Container is already loaded")
        self.content = content
        return True

    def unload(self):
        content = self.content
        self.content = None
        return content
