from enum import Enum
from typing import Any


class ProductTypeReferences(Enum):
    product_1 = "802001"
    product_2 = "802002"
    product_3 = "802003"


TypeId = str


class Product:
    def __init__(
        self, id: TypeId, type: ProductTypeReferences, data: Any, state: str = "0"
    ):
        self.id = id
        self.state = state
        self.data = data
        self.item_type = type

    def __str__(self):
        return "Item id: {}, State: {}, Model: {}".format(
            self.id, self.state, str(self.item_type)
        )

    def update_state(self, new_state):
        self.state = new_state

    def dump(self) -> str:
        return f"Item id: {self.id} Model: {str(self.item_type)} State: {self.state} Data: {self.data}"
