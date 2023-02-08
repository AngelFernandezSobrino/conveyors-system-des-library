from typing import TypeVar

ItemData = TypeVar("ItemData")


class Item:
    def __init__(self, product_id: str, item_type: any, data: ItemData, state: str = "0"):
        self.product_id = product_id
        self.state = state
        self.data = data
        self.item_type = item_type

    def __str__(self):
        return "Product ID: {}, State: {}, Model: {}".format(
            self.product_id, self.state, self.data
        )

    def update_state(self, new_state):
        self.state = new_state
