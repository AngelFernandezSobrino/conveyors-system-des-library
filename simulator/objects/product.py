class Product:

    def __init__(self, product_id, state=0, model=0):
        self.product_id = product_id
        self.state = state
        self.model = model

    def __str__(self):
        return "Product ID: {}, State: {}, Model: {}".format(self.product_id, self.state, self.model)

    def update_state(self, new_state):
        self.state = new_state

