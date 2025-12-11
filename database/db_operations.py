from database.db_models import Database
import config

db = Database(config.DATABASE_PATH)


class ProductOperations:
    @staticmethod
    def get_all_products():

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products ORDER BY name")
        products = cursor.fetchall()
        conn.close()
        return products

    @staticmethod
    def get_products_by_category(category):

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE category = ? ORDER BY name", (category,))
        products = cursor.fetchall()
        conn.close()
        return products

    @staticmethod
    def get_new_products(limit=5):

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE is_new = 1 ORDER BY created_at DESC LIMIT ?", (limit,))
        products = cursor.fetchall()
        conn.close()
        return products

    @staticmethod
    def get_product_by_id(product_id):

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        conn.close()
        return product

    @staticmethod
    def add_product(name, category, price, description, quantity, is_new=False):

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (name, category, price, description, quantity, is_new)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, category, price, description, quantity, 1 if is_new else 0))
        conn.commit()
        conn.close()
        return cursor.lastrowid

    @staticmethod
    def update_product_quantity(product_id, quantity):

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET quantity = ? WHERE id = ?", (quantity, product_id))
        conn.commit()
        conn.close()

    @staticmethod
    def delete_product(product_id):

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        conn.close()


class SellerOperations:
    @staticmethod
    def is_seller(user_id):

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM sellers WHERE user_id = ? AND is_active = 1", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    @staticmethod
    def add_seller(user_id, user_name):

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO sellers (user_id, user_name, is_active)
            VALUES (?, ?, 1)
        ''', (user_id, user_name))
        conn.commit()
        conn.close()

    @staticmethod
    def get_stock_info():

        conn = db.get_connection()
        cursor = conn.cursor()

        # Общая статистика
        cursor.execute("SELECT COUNT(*), SUM(quantity) FROM products")
        total_products, total_quantity = cursor.fetchone()

        # По категориям
        cursor.execute("SELECT category, SUM(quantity) FROM products GROUP BY category")
        categories = cursor.fetchall()


        cursor.execute("SELECT name, quantity FROM products WHERE quantity < 10 ORDER BY quantity ASC")
        low_stock = cursor.fetchall()

        conn.close()

        return {
            'total_products': total_products or 0,
            'total_quantity': total_quantity or 0,
            'categories': categories,
            'low_stock': low_stock
        }


class AboutOperations:
    @staticmethod
    def get_all_sections():

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT section, content FROM about_us ORDER BY id")
        sections = cursor.fetchall()
        conn.close()
        return sections

    @staticmethod
    def update_section(section, content):

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO about_us (section, content)
            VALUES (?, ?)
        ''', (section, content))
        conn.commit()
        conn.close()


class ReviewOperations:
    @staticmethod
    def add_review(user_id, user_name, product_name, rating, review_text):

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reviews (user_id, user_name, product_name, rating, review_text)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, user_name, product_name, rating, review_text))
        conn.commit()
        conn.close()

    @staticmethod
    def get_product_reviews(product_name, limit=10):

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_name, rating, review_text, created_at 
            FROM reviews 
            WHERE product_name = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (product_name, limit))
        reviews = cursor.fetchall()
        conn.close()
        return reviews