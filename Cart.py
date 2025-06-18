import json
from typing import Dict


class Product:
    def __init__(self, product_id: str, name: str, price: float, quantity_available: int):
        self._product_id = product_id
        self._name = name
        self._price = price
        self._quantity_available = quantity_available

    @property
    def product_id(self):
        return self._product_id

    @property
    def name(self):
        return self._name

    @property
    def price(self):
        return self._price

    @property
    def quantity_available(self):
        return self._quantity_available

    @quantity_available.setter
    def quantity_available(self, value):
        if value >= 0:
            self._quantity_available = value

    def decrease_quantity(self, amount):
        if 0 < amount <= self._quantity_available:
            self._quantity_available -= amount
            return True
        return False

    def increase_quantity(self, amount):
        self._quantity_available += amount

    def display_details(self):
        return f"ID: {self._product_id}, Name: {self._name}, Price: ${self._price}, Stock: {self._quantity_available}"

    def to_dict(self):
        return {
            "type": "base",
            "product_id": self._product_id,
            "name": self._name,
            "price": self._price,
            "quantity_available": self._quantity_available
        }


class PhysicalProduct(Product):
    def __init__(self, product_id, name, price, quantity_available, weight):
        super().__init__(product_id, name, price, quantity_available)
        self._weight = weight

    @property
    def weight(self):
        return self._weight

    def display_details(self):
        return super().display_details() + f", Weight: {self._weight}kg"

    def to_dict(self):
        d = super().to_dict()
        d.update({"weight": self._weight, "type": "physical"})
        return d


class DigitalProduct(Product):
    def __init__(self, product_id, name, price, quantity_available, download_link):
        super().__init__(product_id, name, price, quantity_available)
        self._download_link = download_link

    @property
    def download_link(self):
        return self._download_link

    def display_details(self):
        return f"ID: {self._product_id}, Name: {self._name}, Price: ${self._price}, Download: {self._download_link}"

    def to_dict(self):
        d = super().to_dict()
        d.update({"download_link": self._download_link, "type": "digital"})
        return d


class CartItem:
    def __init__(self, product: Product, quantity: int):
        self._product = product
        self._quantity = quantity

    @property
    def product(self):
        return self._product

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, value):
        if value >= 0:
            self._quantity = value

    def calculate_subtotal(self):
        return self._product.price * self._quantity

    def __str__(self):
        return f"Item: {self._product.name}, Quantity: {self._quantity}, Price: ${self._product.price}, Subtotal: ${self.calculate_subtotal()}"

    def to_dict(self):
        return {"product_id": self._product.product_id, "quantity": self._quantity}


class ShoppingCart:
    def __init__(self, product_catalog_file='products.json', cart_state_file='cart.json'):
        self._items: Dict[str, CartItem] = {}
        self._product_catalog_file = product_catalog_file
        self._cart_state_file = cart_state_file
        self._catalog = self._load_catalog()
        self._load_cart_state()

    def _load_catalog(self):
        try:
            with open(self._product_catalog_file, 'r') as f:
                data = json.load(f)
                catalog = {}
                for item in data:
                    if 'product_id' not in item:
                        print(f"Skipping item without product_id: {item}")
                        continue
                    item_type = item.get('type', 'base')
                    item_args = dict(item)
                    item_args.pop('type', None)
                    if item_type == 'physical':
                        prod = PhysicalProduct(**{k: item_args[k] for k in ['product_id', 'name', 'price', 'quantity_available', 'weight'] if k in item_args})
                    elif item_type == 'digital':
                        prod = DigitalProduct(**{k: item_args[k] for k in ['product_id', 'name', 'price', 'quantity_available', 'download_link'] if k in item_args})
                    else:
                        prod = Product(**{k: item_args[k] for k in ['product_id', 'name', 'price', 'quantity_available'] if k in item_args})
                    catalog[item['product_id']] = prod
                return catalog
        except FileNotFoundError:
            return {}

    def _save_catalog(self):
        with open(self._product_catalog_file, 'w') as f:
            json.dump([p.to_dict() for p in self._catalog.values()], f, indent=2)

    def _load_cart_state(self):
        try:
            with open(self._cart_state_file, 'r') as f:
                cart_data = json.load(f)
                for item in cart_data:
                    prod = self._catalog.get(item['product_id'])
                    if prod:
                        self._items[item['product_id']] = CartItem(prod, item['quantity'])
                        prod.decrease_quantity(item['quantity'])  # Adjust stock
        except FileNotFoundError:
            pass

    def _save_cart_state(self):
        with open(self._cart_state_file, 'w') as f:
            json.dump([item.to_dict() for item in self._items.values()], f, indent=2)

    def add_item(self, product_id, quantity):
        if product_id not in self._catalog:
            print("Product not found.")
            return False
        product = self._catalog[product_id]
        if product.decrease_quantity(quantity):
            if product_id in self._items:
                self._items[product_id].quantity += quantity
            else:
                self._items[product_id] = CartItem(product, quantity)
            self._save_cart_state()
            return True
        print("Not enough stock.")
        return False

    def remove_item(self, product_id):
        if product_id in self._items:
            item = self._items.pop(product_id)
            item.product.increase_quantity(item.quantity)
            self._save_cart_state()
            return True
        return False

    def update_quantity(self, product_id, new_quantity):
        if product_id not in self._items:
            return False
        item = self._items[product_id]
        diff = new_quantity - item.quantity
        if diff > 0:
            if item.product.decrease_quantity(diff):
                item.quantity = new_quantity
                self._save_cart_state()
                return True
        elif diff < 0:
            item.product.increase_quantity(-diff)
            item.quantity = new_quantity
            self._save_cart_state()
            return True
        return False

    def get_total(self):
        return sum(item.calculate_subtotal() for item in self._items.values())

    def display_cart(self):
        if not self._items:
            print("Cart is empty.")
            return
        for item in self._items.values():
            print(item)
        print(f"Grand Total: ${self.get_total()}")

    def display_products(self):
        if not self._catalog:
            print("No products available.")
            return
        for product in self._catalog.values():
            print(product.display_details())


# Console Interface

def main():
    cart = ShoppingCart()
    while True:
        print("\n1. View Products\n2. Add Item to Cart\n3. View Cart\n4. Update Quantity\n5. Remove Item\n6. Checkout\n7. Exit")
        choice = input("Enter choice: ")

        if choice == '1':
            cart.display_products()
        elif choice == '2':
            pid = input("Enter Product ID: ")
            try:
                qty = int(input("Enter Quantity: "))
            except ValueError:
                print("Invalid quantity. Please enter a number.")
                continue
            cart.add_item(pid, qty)
        elif choice == '3':
            cart.display_cart()
        elif choice == '4':
            pid = input("Enter Product ID to update: ")
            try:
                qty = int(input("Enter new quantity: "))
            except ValueError:
                print("Invalid quantity. Please enter a number.")
                continue
            if not cart.update_quantity(pid, qty):
                print("Update failed.")
        elif choice == '5':
            pid = input("Enter Product ID to remove: ")
            if not cart.remove_item(pid):
                print("Item not found.")
        elif choice == '6':
            print("Checkout complete. (Simulation)")
        elif choice == '7':
            break
        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()
