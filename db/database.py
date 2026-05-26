import sqlite3
from datetime import datetime
import os

class Database:
    """
    Handles all database operations for the pizza restaurant app.
    Manages menu items and orders.

    Order model (v2 — multi-item):
        orders      — one row per order  (order_id, total_price, timestamp)
        order_items — one row per pizza  (item_id, order_id FK, pizza_name,
                                          size, toppings, item_price)
    """

    def __init__(self, db_path='db/orders.db'):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.populate_default_menu()

    # ── Table creation ────────────────────────────────────────────────────────

    def create_tables(self):
        """
        Create all required tables.
        Tables: menu_items, orders, order_items
        """

        # menu_items — unchanged
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

        # orders — one row per customer order
        # total_price is the sum of all order_items.item_price
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                total_price REAL    NOT NULL DEFAULT 0,
                timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # order_items — one row per pizza line inside an order
        # toppings is a comma-separated string, empty string means no extras
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                item_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id   INTEGER NOT NULL REFERENCES orders(order_id),
                pizza_name TEXT    NOT NULL,
                size       TEXT    NOT NULL,
                toppings   TEXT    NOT NULL DEFAULT '',
                item_price REAL    NOT NULL
            )
        ''')

        self.conn.commit()

    # ── Menu ──────────────────────────────────────────────────────────────────

    def populate_default_menu(self):
        self.cursor.execute('SELECT COUNT(*) FROM menu_items')
        if self.cursor.fetchone()[0] == 0:
            default_pizzas = [
                ('Margeurite',   450,  1200, 'Sauce tomate, mozzarella'),
                ('Viande',       600,  1600, 'Sauce tomate, mozzarella, viande hachee'),
                ('Poulet',       600,  1600, 'Sauce tomate, mozzarella, poulet'),
                ('Vegetarienne', 600,  1600, 'Sauce tomate, mozzarella, poivrons, champignons, olives'),
                ('Skys',         900,  2700, 'Sauce tomate, mozzarella, 4 fromages, jambon, viande'),
                ('Mix',          700,  2000, 'Sauce tomate, mozzarella, viande, poulet, legumes'),
            ]
            for name, price, mg_price, ingrediants in default_pizzas:
                self.cursor.execute('''
                    INSERT INTO menu_items (name, base_price, mega_price, ingrediants)
                    VALUES (?, ?, ?, ?)
                ''', (name, price, mg_price, ingrediants))
            self.conn.commit()

    def get_menu_items(self):
        self.cursor.execute('''
            SELECT pizza_id, name, base_price, mega_price, ingrediants
            FROM menu_items WHERE is_active = 1 ORDER BY name
        ''')
        return [dict(row) for row in self.cursor.fetchall()]

    def get_pizza_by_id(self, pizza_id):
        self.cursor.execute('''
            SELECT pizza_id, name, base_price, mega_price, ingrediants
            FROM menu_items WHERE pizza_id = ? AND is_active = 1
        ''', (pizza_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    # ── Order creation ────────────────────────────────────────────────────────

    def create_order(self, items: list[dict]) -> int:
        """
        Save a full multi-item order in one transaction.

        Args:
            items: list of dicts, each with keys:
                   pizza_name (str), size (str),
                   toppings   (str, comma-separated, may be ''),
                   item_price (float)

        Returns:
            order_id (int) of the newly created order

        Example:
            items = [
                {'pizza_name': 'Skys',  'size': 'Mega',    'toppings': 'Extra fromage', 'item_price': 2750},
                {'pizza_name': 'Mix',   'size': 'Normale', 'toppings': '',              'item_price': 700},
            ]
            order_id = db.create_order(items)
        """
        if not items:
            raise ValueError("Cannot create an order with no items.")

        total_price = sum(i['item_price'] for i in items)
        local_now   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Insert the order header
        self.cursor.execute('''
            INSERT INTO orders (total_price, timestamp) VALUES (?, ?)
        ''', (total_price, local_now))
        order_id = self.cursor.lastrowid

        # Insert each pizza line
        for item in items:
            self.cursor.execute('''
                INSERT INTO order_items (order_id, pizza_name, size, toppings, item_price)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                order_id,
                item['pizza_name'],
                item['size'],
                item.get('toppings', ''),
                item['item_price'],
            ))

        self.conn.commit()
        return order_id

    # ── Order retrieval ───────────────────────────────────────────────────────

    def get_order_by_id(self, order_id: int) -> dict | None:
        """
        Retrieve a full order with all its items.

        Returns:
            {
                'order_id':    1,
                'total_price': 3450.0,
                'timestamp':   '2026-05-24 14:30:00',
                'items': [
                    {'item_id': 1, 'pizza_name': 'Skys', 'size': 'Mega',
                     'toppings': 'Extra fromage', 'item_price': 2750.0},
                    ...
                ]
            }
            or None if not found.
        """
        self.cursor.execute('''
            SELECT order_id, total_price, timestamp
            FROM orders WHERE order_id = ?
        ''', (order_id,))
        row = self.cursor.fetchone()
        if not row:
            return None

        order = dict(row)
        order['items'] = self._get_items_for_order(order_id)
        return order

    def get_all_orders(self) -> list[dict]:
        """
        Retrieve all orders with their items (most recent first).

        Returns:
            list of order dicts (same structure as get_order_by_id)
        """
        self.cursor.execute('''
            SELECT order_id, total_price, timestamp
            FROM orders ORDER BY timestamp DESC
        ''')
        orders = [dict(row) for row in self.cursor.fetchall()]
        for order in orders:
            order['items'] = self._get_items_for_order(order['order_id'])
        return orders

    def _get_items_for_order(self, order_id: int) -> list[dict]:
        """Return all order_items rows for a given order."""
        self.cursor.execute('''
            SELECT item_id, pizza_name, size, toppings, item_price
            FROM order_items WHERE order_id = ? ORDER BY item_id
        ''', (order_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    # ── Analytics ─────────────────────────────────────────────────────────────

    def get_monthly_orders(self, month: int, year: int) -> list[dict]:
        self.cursor.execute('''
            SELECT order_id, total_price, timestamp FROM orders
            WHERE strftime('%m', timestamp) = ?
              AND strftime('%Y', timestamp) = ?
            ORDER BY timestamp DESC
        ''', (str(month).zfill(2), str(year)))
        orders = [dict(row) for row in self.cursor.fetchall()]
        for order in orders:
            order['items'] = self._get_items_for_order(order['order_id'])
        return orders

    def get_monthly_revenue(self, month: int, year: int) -> float:
        self.cursor.execute('''
            SELECT SUM(total_price) FROM orders
            WHERE strftime('%m', timestamp) = ?
              AND strftime('%Y', timestamp) = ?
        ''', (str(month).zfill(2), str(year)))
        result = self.cursor.fetchone()[0]
        return result if result else 0.0

    def get_yearly_revenue(self, year: int) -> float:
        self.cursor.execute('''
            SELECT SUM(total_price) FROM orders
            WHERE strftime('%Y', timestamp) = ?
        ''', (str(year),))
        result = self.cursor.fetchone()[0]
        return result if result else 0.0

    def get_popular_pizzas(self, limit: int = 5) -> list[dict]:
        """Most ordered pizzas (counts individual items, not orders)."""
        self.cursor.execute('''
            SELECT pizza_name, COUNT(*) as count
            FROM order_items
            GROUP BY pizza_name
            ORDER BY count DESC
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in self.cursor.fetchall()]

    # ── Shutdown ──────────────────────────────────────────────────────────────

    def close(self):
        self.conn.close()


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import os
    os.makedirs('db', exist_ok=True)
    db = Database()

    print("Menu:")
    for p in db.get_menu_items():
        print(f"  {p['name']}  N:{p['base_price']}  M:{p['mega_price']}")

    print("\nCreating multi-item order...")
    oid = db.create_order([
        {'pizza_name': 'Skys',       'size': 'Mega',    'toppings': 'Extra fromage', 'item_price': 2750},
        {'pizza_name': 'Margeurite', 'size': 'Normale', 'toppings': '',              'item_price': 450},
    ])
    print(f"Order #{oid} saved.")

    order = db.get_order_by_id(oid)
    print(f"Total: {order['total_price']} DA")
    for item in order['items']:
        top = f" + {item['toppings']}" if item['toppings'] else ''
        print(f"  • {item['pizza_name']} ({item['size']}){top}  → {item['item_price']} DA")

    db.close()