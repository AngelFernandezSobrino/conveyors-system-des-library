from typing import Any

class Container:

    def __init__(self, id: str, content: Any = None):
        self.id = id
        self.content = content

    def __str__(self) -> str:
        return f"Tray {self.id}{f' with {self.content}' if self.content else ''}"

    def load(self, content) -> bool:
        if self.content:
            return False
        self.content = content
        return True

    def unload(self):
        content = self.content
        self.content = None
        return content
