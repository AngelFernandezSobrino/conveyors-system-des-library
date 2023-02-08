from typing import Union

from sim.objects import Item


class Tray:

    def __init__(self, tray_id=-1, item: Union[Item, bool] = False):
        self.tray_id = tray_id
        self.item = item

    def load_item(self, item):
        if self.item:
            raise Exception("Tray already loaded")
        self.item = item

    def unload_item(self):
        item = self.item
        self.item = False
        return item
