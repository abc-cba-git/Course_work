# Глобальные словари для хранения данных
cart = {}
user_product_lists = {}
user_states = {}  # Для отслеживания состояния пользователя (возврат, отзыв и т.д.)
seller_sessions = {}  # Для хранения авторизованных продавцов


class UserState:


    @staticmethod
    def set_state(user_id, state_type, **kwargs):

        user_states[user_id] = {'type': state_type, **kwargs}

    @staticmethod
    def get_state(user_id):

        return user_states.get(user_id)

    @staticmethod
    def clear_state(user_id):

        if user_id in user_states:
            del user_states[user_id]

    @staticmethod
    def add_to_cart(user_id, product_name):

        if user_id not in cart:
            cart[user_id] = {}

        if product_name in cart[user_id]:
            cart[user_id][product_name] += 1
        else:
            cart[user_id][product_name] = 1

    @staticmethod
    def get_cart(user_id):

        return cart.get(user_id, {})

    @staticmethod
    def clear_cart(user_id):

        cart[user_id] = {}

    @staticmethod
    def remove_from_cart(user_id, product_name):

        if user_id in cart and product_name in cart[user_id]:
            if cart[user_id][product_name] > 1:
                cart[user_id][product_name] -= 1
                return cart[user_id][product_name]
            else:
                del cart[user_id][product_name]
                return 0

    @staticmethod
    def set_product_list(user_id, product_list):

        user_product_lists[user_id] = product_list

    @staticmethod
    def get_product_list(user_id):

        return user_product_lists.get(user_id, [])

    @staticmethod
    def authorize_seller(user_id):

        seller_sessions[user_id] = True

    @staticmethod
    def is_seller(user_id):

        return seller_sessions.get(user_id, False)

    @staticmethod
    def logout_seller(user_id):

        seller_sessions[user_id] = False