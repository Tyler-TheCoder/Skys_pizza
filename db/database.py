import sqlite3
from datetime import datetime
import os

class Database:
    """
    Handles all database operations for the pizza restaurant app.
    Manages menu items, orders, and order history.
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
        # Stores available pizzas and their base prices
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu_items (
                pizza_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                base_price REAL NOT NULL,
                category TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Table 2: orders
        # Stores all orders placed by customers
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pizza_name TEXT NOT NULL,
                size TEXT NOT NULL,
                ingredients TEXT NOT NULL,
                final_price REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'Pending'
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
                ('Margherita', 8.00, 'Classic'),
                ('Pepperoni', 9.00, 'Classic'),
                ('Hawaiian', 10.00, 'Special'),
                ('Vegetarian', 8.50, 'Special'),
            ]
            
            for name, price, category in default_pizzas:
                self.cursor.execute('''
                    INSERT INTO menu_items (name, base_price, category)
                    VALUES (?, ?, ?)
                ''', (name, price, category))
            
            self.conn.commit()
    
    def get_menu_items(self):
        """
        Retrieve all active menu items from the database.
        
        Returns:
            list: List of dictionaries containing pizza details
                  Example: [{'pizza_id': 1, 'name': 'Margherita', 'base_price': 8.0, 'category': 'Classic'}, ...]
        """
        self.cursor.execute('''
            SELECT pizza_id, name, base_price, category
            FROM menu_items
            WHERE is_active = 1
            ORDER BY category, name
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
            SELECT pizza_id, name, base_price, category
            FROM menu_items
            WHERE pizza_id = ? AND is_active = 1
        ''', (pizza_id,))
        
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def save_order(self, pizza_name, size, ingredients, final_price):
        """
        Save a new order to the database.
        
        Args:
            pizza_name (str): Name of the pizza (e.g., 'Margherita', 'Custom')
            size (str): Size of the pizza ('Small', 'Medium', 'Large')
            ingredients (str): Comma-separated list of ingredients (e.g., 'cheese,ham,onion')
            final_price (float): Final calculated price including size multiplier
        
        Returns:
            int: The order_id of the newly created order
        """
        self.cursor.execute('''
            INSERT INTO orders (pizza_name, size, ingredients, final_price, status)
            VALUES (?, ?, ?, ?, 'Pending')
        ''', (pizza_name, size, ingredients, final_price))
        
        self.conn.commit()
        
        # Return the ID of the newly inserted order
        return self.cursor.lastrowid
    
    def get_order_by_id(self, order_id):
        """
        Retrieve a specific order by its ID.
        Used for printing the order to the kitchen or for customer receipt.
        
        Args:
            order_id (int): The order ID to fetch
        
        Returns:
            dict: Order details or None if not found
                  Example: {'order_id': 1, 'pizza_name': 'Margherita', 'size': 'Large', ...}
        """
        self.cursor.execute('''
            SELECT order_id, pizza_name, size, ingredients, final_price, timestamp, status
            FROM orders
            WHERE order_id = ?
        ''', (order_id,))
        
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_orders(self):
        """
        Retrieve all orders from the database (ordered by most recent first).
        
        Returns:
            list: List of dictionaries containing all orders
        """
        self.cursor.execute('''
            SELECT order_id, pizza_name, size, ingredients, final_price, timestamp, status
            FROM orders
            ORDER BY timestamp DESC
        ''')
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_pending_orders(self):
        """
        Retrieve all orders with 'Pending' status.
        Useful for showing the reception guy what still needs to be printed.
        
        Returns:
            list: List of pending orders
        """
        self.cursor.execute('''
            SELECT order_id, pizza_name, size, ingredients, final_price, timestamp, status
            FROM orders
            WHERE status = 'Pending'
            ORDER BY timestamp ASC
        ''')
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def update_order_status(self, order_id, status):
        """
        Update the status of an order (e.g., from 'Pending' to 'Printed' or 'Completed').
        
        Args:
            order_id (int): The order ID to update
            status (str): New status ('Pending', 'Printed', 'Completed', etc.)
        """
        self.cursor.execute('''
            UPDATE orders
            SET status = ?
            WHERE order_id = ?
        ''', (status, order_id))
        
        self.conn.commit()
    
    def get_monthly_orders(self, month, year):
        """
        Retrieve all orders from a specific month.
        Used later for generating diagrams and restaurant statistics.
        
        Args:
            month (int): Month number (1-12)
            year (int): Year (e.g., 2026)
        
        Returns:
            list: List of orders from that month
        """
        self.cursor.execute('''
            SELECT order_id, pizza_name, size, ingredients, final_price, timestamp, status
            FROM orders
            WHERE strftime('%m', timestamp) = ? AND strftime('%Y', timestamp) = ?
            ORDER BY timestamp DESC
        ''', (str(month).zfill(2), str(year)))
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_monthly_revenue(self, month, year):
        """
        Calculate total revenue for a specific month.
        Used for restaurant statistics and diagrams.
        
        Args:
            month (int): Month number (1-12)
            year (int): Year (e.g., 2026)
        
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
        Useful for annual reports.
        
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
                  Example: [{'pizza_name': 'Margherita', 'count': 15}, ...]
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


# Example usage (for testing)
if __name__ == '__main__':
    # Create database instance
    db = Database()
    
    # Get all menu items
    print("Menu items:")
    for item in db.get_menu_items():
        print(f"  {item['name']} - ${item['base_price']} ({item['category']})")
    
    # Save a test order
    print("\nSaving test order...")
    order_id = db.save_order('Margherita', 'Large', 'cheese,tomato,basil', 12.50)
    print(f"Order saved with ID: {order_id}")
    
    # Retrieve that order
    print("\nRetrieving order:")
    order = db.get_order_by_id(order_id)
    print(f"  Pizza: {order['pizza_name']}")
    print(f"  Size: {order['size']}")
    print(f"  Price: ${order['final_price']}")
    
    # Close connection
    db.close()
