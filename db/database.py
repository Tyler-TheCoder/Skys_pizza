import sqlite3
from datetime import datetime
import os

class Database:
    """
    Handles all database operations for the pizza restaurant app.
    Manages menu items and orders.
    """

    def __init__(self, db_path='db/orders.db'):
        """
        Initialize the database connection.
        If the database doesn't exist, it will be created automatically.

        Args:
            db_path (str): Path to the SQLite database file
        """
        # Create the db directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Connect to the database
        self.conn = sqlite3.connect(db_path)
        # Enable returning results as dictionaries instead of tuples
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Create tables on initialization
        self.create_tables()
        # Populate default menu items if the table is empty
        self.populate_default_menu()

    def create_tables(self):
        """
        Create the necessary tables for the application if they don't exist.
        Tables: menu_items, orders
        """

        # Table 1: menu_items
        # Stores available pizzas, their prices per size, and their ingredients
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu_items (
                pizza_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL UNIQUE,
                base_price REAL    NOT NULL,
                mega_price REAL    NOT NULL,
                ingrediants TEXT   NOT NULL,
                is_active  BOOLEAN DEFAULT 1
            )
        ''')

        # Table 2: orders
        # Stores all orders placed by customers
        # Note: toppings are the extras added on top of the original pizza
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                pizza_name  TEXT    NOT NULL,
                size        TEXT    NOT NULL,
                toppings    TEXT,
                final_price REAL    NOT NULL,
                timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()

    def populate_default_menu(self):
        """
        Add default pizza items to the menu if the table is empty.
        This runs only once when the app starts for the first time.
        """
        # Check if menu is empty
        self.cursor.execute('SELECT COUNT(*) FROM menu_items')
        count = self.cursor.fetchone()[0]

        # If menu is empty, add default items
        if count == 0:
            default_pizzas = [
                ('Margeurite', 450,  1200, 'Sauce tomate, mozzarella'),
                ('Viande',     600,  1600, 'Sauce tomate, mozzarella, viande hachee'),
                ('Poulet',     600,  1600, 'Sauce tomate, mozzarella, poulet'),
                ('Vegetarienne',600, 1600, 'Sauce tomate, mozzarella, poivrons, champignons, olives'),
                ('Skys',       900,  2700, 'Sauce tomate, mozzarella, 4 fromages, jambon, viande'),
                ('Mix',        700,  2000, 'Sauce tomate, mozzarella, viande, poulet, legumes'),
            ]

            for name, price, mg_price, ingrediants in default_pizzas:
                self.cursor.execute('''
                    INSERT INTO menu_items (name, base_price, mega_price, ingrediants)
                    VALUES (?, ?, ?, ?)
                ''', (name, price, mg_price, ingrediants))

            self.conn.commit()

    def get_menu_items(self):
        """
        Retrieve all active menu items from the database.

        Returns:
            list: List of dictionaries containing pizza details
                  Example: [{'pizza_id': 1, 'name': 'Margeurite', 'base_price': 450.0,
                              'mega_price': 1200.0, 'ingrediants': 'Sauce tomate, mozzarella'}, ...]
        """
        self.cursor.execute('''
            SELECT pizza_id, name, base_price, mega_price, ingrediants
            FROM menu_items
            WHERE is_active = 1
            ORDER BY name
        ''')

        # Convert sqlite3.Row objects to dictionaries
        return [dict(row) for row in self.cursor.fetchall()]

    def get_pizza_by_id(self, pizza_id):
        """
        Retrieve a single pizza by its ID.

        Args:
            pizza_id (int): The ID of the pizza

        Returns:
            dict: Pizza details or None if not found
        """
        self.cursor.execute('''
            SELECT pizza_id, name, base_price, mega_price, ingrediants
            FROM menu_items
            WHERE pizza_id = ? AND is_active = 1
        ''', (pizza_id,))

        row = self.cursor.fetchone()
        return dict(row) if row else None

    def save_order(self, pizza_name, size, toppings, final_price):
        """
        Save a new order to the database.

        Args:
            pizza_name  (str):   Name of the pizza (e.g., 'Margeurite')
            size        (str):   Size of the pizza ('Normale' or 'Mega')
            toppings    (str):   Comma-separated extras added on top (e.g., 'jambon, olives')
                                 Pass an empty string if no toppings were added.
            final_price (float): Final calculated price

        Returns:
            int: The order_id of the newly created order
        """
        self.cursor.execute('''
            INSERT INTO orders (pizza_name, size, toppings, final_price)
            VALUES (?, ?, ?, ?)
        ''', (pizza_name, size, toppings, final_price))

        self.conn.commit()

        # Return the ID of the newly inserted order
        return self.cursor.lastrowid

    def get_order_by_id(self, order_id):
        """
        Retrieve a specific order by its ID.
        Used for printing the order to the kitchen or for the customer receipt.

        Args:
            order_id (int): The order ID to fetch

        Returns:
            dict: Order details or None if not found
                  Example: {'order_id': 1, 'pizza_name': 'Margeurite',
                             'size': 'Mega', 'toppings': 'jambon', ...}
        """
        self.cursor.execute('''
            SELECT order_id, pizza_name, size, toppings, final_price, timestamp
            FROM orders
            WHERE order_id = ?
        ''', (order_id,))

        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_all_orders(self):
        """
        Retrieve all orders from the database (most recent first).

        Returns:
            list: List of dictionaries containing all orders
        """
        self.cursor.execute('''
            SELECT order_id, pizza_name, size, toppings, final_price, timestamp
            FROM orders
            ORDER BY timestamp DESC
        ''')

        return [dict(row) for row in self.cursor.fetchall()]

    def get_monthly_orders(self, month, year):
        """
        Retrieve all orders from a specific month.
        Used for generating diagrams and restaurant statistics.

        Args:
            month (int): Month number (1-12)
            year  (int): Year (e.g., 2026)

        Returns:
            list: List of orders from that month
        """
        self.cursor.execute('''
            SELECT order_id, pizza_name, size, toppings, final_price, timestamp
            FROM orders
            WHERE strftime('%m', timestamp) = ? AND strftime('%Y', timestamp) = ?
            ORDER BY timestamp DESC
        ''', (str(month).zfill(2), str(year)))

        return [dict(row) for row in self.cursor.fetchall()]

    def get_monthly_revenue(self, month, year):
        """
        Calculate total revenue for a specific month.

        Args:
            month (int): Month number (1-12)
            year  (int): Year (e.g., 2026)

        Returns:
            float: Total revenue for that month
        """
        self.cursor.execute('''
            SELECT SUM(final_price) as total
            FROM orders
            WHERE strftime('%m', timestamp) = ? AND strftime('%Y', timestamp) = ?
        ''', (str(month).zfill(2), str(year)))

        result = self.cursor.fetchone()[0]
        return result if result else 0.0

    def get_yearly_revenue(self, year):
        """
        Calculate total revenue for an entire year.

        Args:
            year (int): Year (e.g., 2026)

        Returns:
            float: Total revenue for that year
        """
        self.cursor.execute('''
            SELECT SUM(final_price) as total
            FROM orders
            WHERE strftime('%Y', timestamp) = ?
        ''', (str(year),))

        result = self.cursor.fetchone()[0]
        return result if result else 0.0

    def get_popular_pizzas(self, limit=5):
        """
        Get the most ordered pizzas.
        Useful for business analytics.

        Args:
            limit (int): Number of top pizzas to return

        Returns:
            list: List of dictionaries with pizza names and order counts
                  Example: [{'pizza_name': 'Margeurite', 'count': 15}, ...]
        """
        self.cursor.execute('''
            SELECT pizza_name, COUNT(*) as count
            FROM orders
            GROUP BY pizza_name
            ORDER BY count DESC
            LIMIT ?
        ''', (limit,))

        return [dict(row) for row in self.cursor.fetchall()]

    def close(self):
        """
        Close the database connection.
        Call this when shutting down the app.
        """
        self.conn.close()


# Quick test — run with: python db/database.py
if __name__ == '__main__':
    db = Database()

    print("Menu items:")
    for item in db.get_menu_items():
        print(f"  {item['name']} | Normale: {item['base_price']} DA | Mega: {item['mega_price']} DA")
        print(f"    Ingredients: {item['ingrediants']}")

    print("\nSaving test order...")
    order_id = db.save_order('Margeurite', 'Mega', 'jambon, olives', 1300.0)
    print(f"Order saved with ID: {order_id}")

    print("\nRetrieving order:")
    order = db.get_order_by_id(order_id)
    print(f"  Pizza   : {order['pizza_name']}")
    print(f"  Size    : {order['size']}")
    print(f"  Toppings: {order['toppings']}")
    print(f"  Price   : {order['final_price']} DA")

    db.close()