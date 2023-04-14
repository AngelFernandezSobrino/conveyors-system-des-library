from typing import Generic, TypeVar

ItemData = TypeVar("ItemData")
ItemType = TypeVar("ItemType")

class Item(Generic[ItemData, ItemType]):
    def __init__(self, id: str, item_type: ItemType, data: ItemData, state: str = "0"):
        self.id = id
        self.state = state
        self.data = data
        self.item_type = item_type

    def __str__(self):
        return "Item id: {}, State: {}, Model: {}".format(
            self.id, self.state, self.item_type.name
        )

    def update_state(self, new_state):
        self.state = new_state
