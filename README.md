# Skys Pizza
**Pizza Restaurant Order App**

A desktop application for managing pizza orders in a restaurant. Staff can create multi-item orders, calculate prices, send orders to the kitchen printer, and view order history — all through a modern GUI.

---

## Project Overview

### What This App Does

1. **Order Creation** — Select pizzas, choose size (Normale/Mega), add toppings, build a cart of multiple items
2. **Price Calculation** — Auto-calculates total (base/mega price + topping costs)
3. **Cart Management** — Review and modify the order before sending (add/remove items)
4. **Kitchen Printing** — Orders are sent to a thermal printer
5. **Order History** — Searchable history panel with order cards showing items, prices, and timestamps
6. **Analytics** (future) — Monthly revenue charts and popularity diagrams

### Who Uses It

- **Reception staff** — Creates orders, manages printing
- **Kitchen staff** — Receives printed orders from the thermal printer
- **Manager** — Views history and reports

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.10+ | App logic and scripting |
| **UI Framework** | CustomTkinter | Modern, cross-platform interface |
| **Database** | SQLite | Local order and menu storage |
| **Printer Communication** | python-escpos | Sends print commands to thermal printer |
| **Packaging** | PyInstaller | Converts app to standalone executable |

---

## Project Structure

```
Skys/
│
├── main.py                  # Entry point — launches the application
├── requirements.txt         # Python dependencies
├── README.md                # This file
│
├── ui/                      # User Interface Layer
│   ├── order_screen.py      # Main layout: sidebar, topbar, content area, navigation
│   ├── menu_panel.py        # "Create Order" page — pizza grid, size, toppings, cart
│   └── history_panel.py     # "History" page — searchable order history with cards
│
├── db/                      # Database Layer
│   ├── database.py          # SQLite operations (v2 multi-item schema)
│   └── orders.db            # Database file (auto-generated on first run)
│
└── printer/                 # Printer Communication Layer
    └── printer.py           # ESC/POS commands for thermal printer
```

### Folder Responsibilities

- **`ui/`** — Anything the user sees and clicks on. New pages, tabs, or panels go here.
- **`db/`** — All database queries and data persistence. Schema changes happen here.
- **`printer/`** — All printer communication. Receipt format changes happen here.

---

## Setup & Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Skys
```

### 2. Create Virtual Environment

```bash
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

Entry point. Sets the CustomTkinter theme, initializes the database, and launches the main window.

```python
import customtkinter as ctk
from db.database import Database
from ui.order_screen import OrderScreen

db = Database()
root = ctk.CTk()
root.title("Pizza House — Reception")
root.geometry("1100x650")

app = OrderScreen(root, db)
root.mainloop()
```

**What to do here:** Only touch this if you're changing how the app starts.

---

### `db/database.py`

Handles all database operations using a **v2 multi-item schema**:

- **`orders`** — one row per customer order (`order_id`, `total_price`, `timestamp`)
- **`order_items`** — one row per pizza in an order (`item_id`, `order_id` FK, `pizza_name`, `size`, `toppings`, `item_price`)
- **`menu_items`** — pizza catalog (`pizza_id`, `name`, `base_price`, `mega_price`, `ingrediants`, `is_active`)

**Key functions:**

- `get_menu_items()` — Returns all active pizzas
- `get_pizza_by_id(pizza_id)` — Returns a single pizza
- `create_order(items)` — Saves a multi-item order in one transaction
- `get_order_by_id(order_id)` — Fetches a specific order with its items
- `get_all_orders()` — Returns all orders (most recent first) with their items
- `get_monthly_orders(month, year)` — Orders for a given month
- `get_monthly_revenue(month, year)` — Monthly sales total
- `get_yearly_revenue(year)` — Yearly sales total
- `get_popular_pizzas(limit=5)` — Most-ordered pizzas

---

### `ui/order_screen.py`

Main application window with a three-zone layout:

- **Left sidebar** — Navigation (Menu / Admin sections) with a logo and settings button
- **Top bar** — Section-aware tabs that change based on the active sidebar section
- **Content area** — Swappable page frames, each hosting a panel module

Handles navigation switching, tab styling, the pending orders badge, and mousewheel scroll binding.

---

### `ui/menu_panel.py`

The **"Create Order"** page with a two-column layout:

**Left column (pizza selection):**
1. Pizza grid — selectable cards showing name, ingredients, and prices
2. Size selector — Normale or Mega (each with its own price)
3. Toppings list — optional extras with individual prices
4. "Add to order" button — adds the configured pizza to the cart

**Right column (cart):**
- Scrollable list of cart items (each with pizza name, size, toppings, price, and a × remove button)
- Running total
- "Send to kitchen" button — saves the order and clears the cart

---

### `ui/history_panel.py`

The **"History"** page showing all past orders as cards. Each card displays:
- Order number, timestamp, item count, and total price
- Individual pizza lines with name, size, toppings, and item price

Includes a **search bar** to filter orders by pizza name, order number, or date.

---

### `printer/printer.py`

Communicates with the thermal printer using ESC/POS commands.

**What to do here:** If the receipt format changes or if the printer model changes, edit here.

---

## Database Schema

### `menu_items` Table

```sql
CREATE TABLE menu_items (
    pizza_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL UNIQUE,
    base_price REAL    NOT NULL,
    mega_price REAL    NOT NULL,
    ingrediants TEXT  NOT NULL,
    is_active  BOOLEAN DEFAULT 1
)
```

### `orders` Table

```sql
CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    total_price REAL    NOT NULL DEFAULT 0,
    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### `order_items` Table

```sql
CREATE TABLE order_items (
    item_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL REFERENCES orders(order_id),
    pizza_name TEXT    NOT NULL,
    size       TEXT    NOT NULL,
    toppings   TEXT    NOT NULL DEFAULT '',
    item_price REAL    NOT NULL
)
```

---

## Workflow

### Creating an Order

1. Open the app — the "Create Order" page is shown by default
2. Click a pizza card (e.g. "Skys") — see ingredients and prices for Normale/Mega
3. Select a size — price updates automatically
4. Add optional toppings (Extra fromage, Jambon, etc.)
5. Click **"+ Add to order"** — the item appears in the cart on the right
6. Repeat for additional pizzas
7. Review the cart — use the × button to remove items if needed
8. Click **"🖨 Send to kitchen"** — order saved to database, cart clears, badge updates

### Viewing History

1. Click the **"📊 Admin"** sidebar button
2. Click the **"🕐 History"** tab
3. Browse orders as cards — search by name, order number, or date

---

## Common Tasks

### Adding a New Pizza to the Menu

Edit `db/database.py`, in the `populate_default_menu()` function:

```python
default_pizzas = [
    ('Margeurite',   450,  1200, 'Sauce tomate, mozzarella'),
    ('Viande',       600,  1600, 'Sauce tomate, mozzarella, viande hachee'),
    ('YOUR_PIZZA',   700,  1800, 'Your ingredients here'),  # ← Add here
]
```

Columns: `(name, base_price (Normale), mega_price (Mega), ingredients)`

### Changing the Receipt Format

Edit `printer/printer.py`.

### Adding a New Page/Tab

1. Add a new page key to `page_keys` in `order_screen.py:_build_content_area()`
2. Add the tab entry to `SECTION_TABS` in `order_screen.py`
3. Create a new panel module in `ui/` and inject it into the page frame

---

## Running Tests

```bash
python db/database.py
```

This runs the `if __name__ == '__main__'` block, which creates a test multi-item order and prints results.

---

## Building the Executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

The executable will be in `dist/main.exe`.

---

## Important Notes

### Database Backup

```bash
cp db/orders.db backup_orders.db
```

### Printer Setup

The app expects a thermal receipt printer that supports ESC/POS protocol (e.g. Epson TM-T20, Star Micronics TSP100). Configure the port in `printer/printer.py`.

### Offline Operation

The app works completely offline. No internet needed.

---

## Troubleshooting

### Database is Corrupted

Delete `db/orders.db`. The app will recreate it on the next run.

### Printer Not Printing

Check: printer is on, paper is loaded, cable is connected, port in `printer.py` is correct.

### App Crashes on Startup

- Missing dependency: `pip install -r requirements.txt`
- Wrong Python version: Need Python 3.10+
- Database locked: Close other instances of the app

---

## Future Enhancements

- 📈 Statistics & charts (monthly revenue, pizza popularity)
- 🍕 Pizza manager (add/edit menu items from UI)
- 🥗 Supplements manager
- 📄 Customer receipts (print to separate printer)
- 🏷️ Discount codes
- 🪪 Staff login system
- 🌐 Network printing (multiple terminals)

---

## License

Internal project for **Skys Pizza**. Do not distribute.

---

**Last Updated:** May 28, 2026
