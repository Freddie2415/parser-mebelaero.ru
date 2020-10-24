class Catalog:
    name = ''
    link = ''


class Product:
    name = ''
    price = ''
    link = ''

    def __hash__(self):
        return hash((self.name, self.price, self.link))

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.price == other.price and self.name == other.name and self.link == other.link
