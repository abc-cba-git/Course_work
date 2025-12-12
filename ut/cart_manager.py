class CartManager:
    def __init__(self):
        self.carts = {}

    def get_cart(self, user_id):

        if user_id not in self.carts:
            self.carts[user_id] = {}
        return self.carts[user_id]

    def add_to_cart(self, user_id, product_id, product_name, price, quantity=1):

        cart = self.get_cart(user_id)

        if product_id in cart:
            cart[product_id]['quantity'] += quantity
        else:
            cart[product_id] = {
                'name': product_name,
                'price': price,
                'quantity': quantity
            }

        return cart[product_id]['quantity']

    def remove_from_cart(self, user_id, product_id, quantity=None):

        if user_id not in self.carts or product_id not in self.carts[user_id]:
            return False

        if quantity is None:
            # Удалить полностью
            del self.carts[user_id][product_id]
        else:
            # Уменьшить количество
            self.carts[user_id][product_id]['quantity'] -= quantity

            if self.carts[user_id][product_id]['quantity'] <= 0:
                del self.carts[user_id][product_id]

        return True

    def clear_cart(self, user_id):

        if user_id in self.carts:
            self.carts[user_id] = {}
        return True

    def get_cart_total(self, user_id):

        if user_id not in self.carts or not self.carts[user_id]:
            return 0

        total = 0
        for product_id, item in self.carts[user_id].items():
            total += item['price'] * item['quantity']

        return total

    def get_cart_items_count(self, user_id):

        if user_id not in self.carts:
            return 0
        return len(self.carts[user_id])

    def get_cart_summary(self, user_id):

        cart = self.get_cart(user_id)

        if not cart:
            return None

        items = []
        total = 0

        for product_id, item in cart.items():
            item_total = item['price'] * item['quantity']
            total += item_total

            items.append({
                'product_id': product_id,
                'name': item['name'],
                'price': item['price'],
                'quantity': item['quantity'],
                'total': item_total
            })

        return {
            'items': items,
            'total': total,
            'items_count': len(items)
        }


# Глобальный экземпляр менеджера корзины
cart_manager = CartManager()