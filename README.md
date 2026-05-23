# Skys_pizza
**Pizza Restaurant Order App**

A simple Windows desktop application for managing pizza orders in a restaurant. The app runs on the reception desk, allows staff to create orders, calculates prices, sends orders to the kitchen printer, and maintains order history for customer receipts.

---

## Project Overview

### What This App Does

1. **Order Creation** — Reception staff select pizza type, add ingredients, choose size
2. **Price Calculation** — App automatically calculates final price (base price + ingredient costs + size multiplier)
3. **Kitchen Printing** — Orders are sent to a thermal printer in the kitchen
4. **Order History** — All orders are saved in a local database for later reference (customer receipts, statistics)
5. **Analytics** (future) — Monthly revenue charts and restaurant performance diagrams

### Who Uses It

- **Reception staff** — Creates orders, manages printing
- **Kitchen staff** — Receives printed orders from the thermal printer
- **Manager** — Views statistics and daily/monthly reports

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.10+ | App logic and scripting |
| **UI Framework** | CustomTkinter | Modern, easy-to-maintain interface |
| **Database** | SQLite | Local order and menu storage |
| **Printer Communication** | python-escpos | Sends print commands to thermal printer |
| **Packaging** | PyInstaller | Converts app to standalone .exe |

### Why These Choices?

- **Simple and stable** — No complex dependencies, minimal external services
- **Offline-first** — Works without internet, no server required
- **Single-machine** — Everything runs locally on the reception PC
- **Low maintenance** — All libraries are well-documented and battle-tested
- **Easy to extend** — Clean separation of concerns (UI, Database, Printer)

---

## Project Structure

```
pizza_app/
│
├── main.py                  # Entry point - launches the application
├── requirements.txt         # Python dependencies (pip install -r requirements.txt)
├── README.md               # This file
│
├── ui/                     # User Interface Layer
│   ├── order_screen.py     # Main ordering interface (pizza selection, ingredients, size)
│   └── menu_panel.py       # Menu display and pizza category management
│
├── db/                     # Database Layer
│   ├── database.py         # SQLite operations (queries, inserts, updates)
│   └── orders.db           # Database file (auto-generated on first run)
│
└── printer/                # Printer Communication Layer
    └── printer.py          # ESC/POS commands for thermal printer
```

### Folder Responsibilities

- **`ui/`** — Anything the user sees and clicks on. If menu display changes, edit here.
- **`db/`** — All database queries and data persistence. If order schema changes, edit here.
- **`printer/`** — All printer communication. If printer format changes, edit here.

This separation keeps the code clean and maintainable.

---

## Setup & Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd pizza_app
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Mac/Linux)
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the App

```bash
python main.py
```

The app will:
- Create `db/orders.db` if it doesn't exist
- Populate default menu items
- Open the main window

---

## How Each File Works

### `main.py`

Entry point. Initializes the database and launches the UI.

```python
from ui.order_screen import OrderScreen
from db.database import Database

# Initialize database
db = Database()

# Create and display main window
app = OrderScreen(db)
app.run()
```

**What to do here:** Only touch this if you're changing how the app starts.

---

### `db/database.py`

Handles all database operations. Every query to the database goes through this file.

**Key functions:**

- `get_menu_items()` — Returns all available pizzas
- `save_order(pizza_name, size, ingredients, final_price)` — Saves a new order
- `get_order_by_id(order_id)` — Fetches a specific order (for printing)
- `get_monthly_orders(month, year)` — Gets orders from a specific month (for analytics)
- `get_monthly_revenue(month, year)` — Calculates monthly sales
- `get_popular_pizzas()` — Returns most-ordered pizzas

**What to do here:** Add new queries if you need different data from the database.

---

### `ui/order_screen.py`

Main window where reception staff create orders.

**Responsibilities:**
- Display menu items
- Let users select pizza, ingredients, size
- Calculate price in real-time
- Send order to printer
- Show order confirmation

**What to do here:** If the UI needs a new button, field, or layout change, edit here.

---

### `ui/menu_panel.py`

Displays available pizzas and their categories.

**Responsibilities:**
- Load menu from database
- Display pizzas organized by category (Classic, Special, etc.)
- Handle pizza selection

**What to do here:** If menu display changes, edit here.

---

### `printer/printer.py`

Communicates with the thermal printer in the kitchen using ESC/POS commands.

**Responsibilities:**
- Format order data for printing
- Send print commands to the printer
- Handle printer errors

**What to do here:** If the receipt format changes or if the printer model changes, edit here.

---

## Database Schema

### `menu_items` Table

Stores available pizzas.

```sql
CREATE TABLE menu_items (
    pizza_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,              -- e.g., "Margherita"
    base_price REAL NOT NULL,        -- e.g., 8.00
    category TEXT NOT NULL,          -- e.g., "Classic", "Special"
    is_active BOOLEAN DEFAULT 1      -- Enable/disable menu items
)
```

### `orders` Table

Stores all customer orders.

```sql
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    pizza_name TEXT NOT NULL,        -- e.g., "Custom" or "Margherita"
    size TEXT NOT NULL,              -- "Small", "Medium", "Large"
    ingredients TEXT NOT NULL,       -- Comma-separated: "cheese,ham,onion"
    final_price REAL NOT NULL,       -- After size multiplier
    timestamp DATETIME,              -- When order was created
    status TEXT DEFAULT 'Pending'    -- "Pending", "Printed", "Completed"
)
```

---

## Workflow

### Creating an Order (What the Reception Guy Does)

1. Opens the app → sees the menu
2. Clicks on "Margherita" → ingredient selection screen appears
3. Selects ingredients (or leaves as default)
4. Chooses size: Small (1x), Medium (1.2x), Large (1.5x)
5. App calculates: $8.00 base × 1.5 (Large) = $12.00
6. Clicks "Create Order" → Order saved to database
7. Receipt prints to kitchen → Order appears on receipt printer

### What Happens Behind the Scenes

```
Reception Guy clicks "Create Order"
        ↓
order_screen.py validates input
        ↓
database.py saves to orders.db
        ↓
printer.py formats and prints
        ↓
Kitchen receives printed receipt
```

---

## Common Tasks

### Adding a New Pizza to the Menu

Edit `db/database.py`, in the `populate_default_menu()` function:

```python
default_pizzas = [
    ('Margherita', 8.00, 'Classic'),
    ('Pepperoni', 9.00, 'Classic'),
    ('Hawaiian', 10.00, 'Special'),
    ('Vegetarian', 8.50, 'Special'),
    ('YOUR_NEW_PIZZA', 11.00, 'Special'),  # ← Add here
]
```

Then the database will auto-create it on the next app restart.

---

### Changing the Receipt Format

The kitchen receipt is formatted in `printer/printer.py`. Edit the `format_receipt()` function to change what prints.

Example: To add a delivery time estimate, edit the receipt template.

---

### Adding a New Order Status

If you want to track "Completed", "Cancelled", etc., edit the `UPDATE orders SET status` queries in `db/database.py`.

---

### Generating Monthly Reports (Future Feature)

Use these database functions:

```python
from db.database import Database

db = Database()

# Get all orders from May 2026
may_orders = db.get_monthly_orders(5, 2026)

# Get total revenue for May
may_revenue = db.get_monthly_revenue(5, 2026)

# Get top 5 pizzas
popular = db.get_popular_pizzas(limit=5)
```

---

## Running Tests

To test the database without the UI:

```bash
python db/database.py
```

This runs the `if __name__ == '__main__'` block and:
- Creates a test order
- Fetches it back
- Prints results

---

## Building the Executable (.exe)

When the app is ready for the reception PC:

```bash
# Install PyInstaller
pip install pyinstaller

# Create a single .exe file
pyinstaller --onefile --windowed main.py

# The .exe will be in: dist/main.exe
```

Hand them `dist/main.exe` — they just double-click it. No Python installation needed.

---

## Important Notes

### Database Backup

The database file (`orders.db`) contains all order history. Back it up regularly:

```bash
# Copy to USB or cloud storage
cp db/orders.db backup_orders.db
```

---

### Printer Setup

The app expects a **thermal receipt printer** that supports **ESC/POS** protocol.

Common models:
- Epson TM-T20
- Star Micronics TSP100
- Any generic ESC/POS thermal printer

Configure the printer port in `printer/printer.py` (usually `COM3` or `LPT1`).

---

### Offline Operation

The app works completely offline. No internet needed. Orders are stored locally and persist even if the PC restarts.

---

## Troubleshooting

### Database is Corrupted

Delete `db/orders.db`. The app will recreate it on the next run (you'll lose order history, so backup first).

### Printer Not Printing

Check:
1. Printer is turned on and connected
2. Paper is loaded
3. USB/LAN cable is connected
4. Printer port in `printer.py` matches the actual port

### App Crashes on Startup

Check the error message. Common issues:
- Missing dependency: `pip install -r requirements.txt`
- Wrong Python version: Need Python 3.10+
- Database locked: Close other instances of the app

---

## Future Enhancements

Ideas for later versions:

- ✓ Monthly revenue diagrams
- ✓ Pizza popularity charts
- ✓ Customer receipts (print to separate printer)
- ✓ Discount codes
- ✓ Table/delivery management
- ✓ Staff login system
- ✓ Network printing (multiple terminals)

---

## Getting Help

If something breaks:

1. Check the error message
2. Review the relevant file (listed in "How Each File Works")
3. Check git history for recent changes
4. Ask the team

---

## License

Internal project for **Skys Pizza**. Do not distribute.

---


---

**Last Updated:** May 23, 2026
