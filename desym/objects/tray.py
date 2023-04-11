from typing import Union

from desym.objects import Item


class Tray:

    def __init__(self, tray_id: str, item: Union[Item, bool] = False):
        self.tray_id = tray_id
        self.item = item

    def __str__(self) -> str:
        return f"Tray {self.tray_id}{f' with {self.item}' if self.item else ''}"

    def load_item(self, item) -> bool:
        if self.item:
            return False
        self.item = item
        return True

    def unload_item(self):
        item = self.item
        self.item = False
        return item
