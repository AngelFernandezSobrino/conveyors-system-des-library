class Tray:

    def __init__(self, trayId=-1, product=-1):
        self.id = id
        self.product = product

    def load_product(self, product):
        self.product = product

    def unload_product(self):
        product = self.product
        self.product = -1
        return product
