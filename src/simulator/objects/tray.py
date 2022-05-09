class Tray:

    def __init__(self, tray_id=-1, product=False):
        self.tray_id = tray_id
        self.product = product

    def load_product(self, product):
        self.product = product

    def unload_product(self):
        product = self.product
        self.product = False
        return product
