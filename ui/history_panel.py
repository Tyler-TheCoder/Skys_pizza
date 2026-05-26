import customtkinter as ctk
from db.database import Database
from datetime import datetime

CONTENT_BG   = "#FFF8F0"
BORDER_COLOR = "#F5C060"
ACCENT       = "#F59E0B"
ACCENT_DARK  = "#B45309"
ACCENT_LIGHT = "#FEF3C7"
CARD_BG      = "#FFFFFF"
TEXT_DARK    = "#1C1008"
TEXT_MUTED   = "#78716C"
TEXT_LABEL   = "#A16207"
ITEM_BG      = "#FFFBEB"


class HistoryPanel:
    def __init__(self, parent_frame: ctk.CTkFrame, db: Database, order_screen):
        self.frame        = parent_frame
        self.db           = db
        self.order_screen = order_screen
        self._build()

    def _build(self):
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(2, weight=1)

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(8, 2))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="Order History",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_DARK,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header, text="Refresh", width=80, height=28,
            corner_radius=6, fg_color=CARD_BG, hover_color=ACCENT_LIGHT,
            text_color=TEXT_DARK, border_width=1, border_color=BORDER_COLOR,
            font=ctk.CTkFont(size=12), command=self._refresh,
        ).grid(row=0, column=1, padx=(8, 0), sticky="e")

        # ── Search ────────────────────────────────────────────────────────────
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh())
        ctk.CTkEntry(
            self.frame, textvariable=self.search_var,
            placeholder_text="Search by pizza name, order #, or date...",
            height=32, corner_radius=6, fg_color=CARD_BG,
            border_color=BORDER_COLOR, text_color=TEXT_DARK,
            placeholder_text_color=TEXT_MUTED,
        ).grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 4))

        # ── Scrollable order list ─────────────────────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(
            self.frame, fg_color=CONTENT_BG,
            scrollbar_button_color=BORDER_COLOR,
            scrollbar_button_hover_color=ACCENT,
            corner_radius=8,
        )
        self.scroll.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 8))
        self.scroll.grid_columnconfigure(0, weight=1)

        self._refresh()

    # ── Refresh ───────────────────────────────────────────────────────────────

    def _refresh(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        orders = self.db.get_all_orders()
        query  = self.search_var.get().strip().lower()

        if query:
            orders = [
                o for o in orders
                if query in str(o["order_id"])
                or query in (o.get("timestamp") or "")
                or any(
                    query in item["pizza_name"].lower()
                    for item in o.get("items", [])
                )
            ]

        if not orders:
            ctk.CTkLabel(
                self.scroll,
                text="No orders found." if query else "No orders yet.",
                font=ctk.CTkFont(size=13), text_color=TEXT_MUTED,
            ).pack(pady=40)
            return

        for order in orders:
            self._make_order_card(order)

        self.order_screen._bind_mousewheel(self.scroll)

    # ── Order card ────────────────────────────────────────────────────────────

    def _make_order_card(self, order: dict):
        """
        Each order is shown as a card:
            header row  — Order #  |  date  |  N pizzas  |  total
            items block — one row per pizza line
        """
        card = ctk.CTkFrame(
            self.scroll, fg_color=CARD_BG,
            border_width=1, border_color=BORDER_COLOR, corner_radius=10,
        )
        card.pack(fill="x", pady=4, padx=2)
        card.grid_columnconfigure(0, weight=1)

        # ── Header row ────────────────────────────────────────────────────────
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        header.grid_columnconfigure(1, weight=1)

        # Order # badge
        ctk.CTkLabel(
            header,
            text=f"Order #{order['order_id']}",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=ACCENT_LIGHT, text_color=ACCENT_DARK,
            corner_radius=6, padx=8, pady=2,
        ).grid(row=0, column=0, sticky="w")

        # Timestamp
        ts = order.get("timestamp", "")
        try:
            date_str = datetime.fromisoformat(ts).strftime("%d/%m/%Y  %H:%M")
        except (ValueError, TypeError):
            date_str = ts or "—"

        ctk.CTkLabel(
            header, text=date_str,
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED,
        ).grid(row=0, column=1, sticky="w", padx=(10, 0))

        # Item count + total (right side)
        items      = order.get("items", [])
        item_count = len(items)
        ctk.CTkLabel(
            header,
            text=f"{item_count} pizza{'s' if item_count != 1 else ''}",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED,
        ).grid(row=0, column=2, sticky="e", padx=(0, 12))

        ctk.CTkLabel(
            header,
            text=f"{order['total_price']:.0f} DA",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=ACCENT_DARK,
        ).grid(row=0, column=3, sticky="e")

        # ── Divider ───────────────────────────────────────────────────────────
        ctk.CTkFrame(card, height=1, fg_color=BORDER_COLOR).grid(
            row=1, column=0, sticky="ew", padx=12,
        )

        # ── Pizza items block ─────────────────────────────────────────────────
        items_frame = ctk.CTkFrame(card, fg_color="transparent")
        items_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(6, 10))
        items_frame.grid_columnconfigure(1, weight=1)

        if not items:
            ctk.CTkLabel(
                items_frame, text="(no items recorded)",
                font=ctk.CTkFont(size=11), text_color=TEXT_MUTED,
            ).grid(row=0, column=0, columnspan=4)
            return

        for i, item in enumerate(items):
            self._make_item_row(items_frame, i, item)

    def _make_item_row(self, parent, row_idx: int, item: dict):
        """One pizza line inside an order card."""
        row = ctk.CTkFrame(
            parent, fg_color=ITEM_BG if row_idx % 2 == 0 else "transparent",
            corner_radius=6,
        )
        row.grid(row=row_idx, column=0, sticky="ew", pady=2)
        row.grid_columnconfigure(2, weight=1)

        # Bullet
        ctk.CTkLabel(
            row, text="•", font=ctk.CTkFont(size=12),
            text_color=ACCENT, width=16,
        ).grid(row=0, column=0, padx=(8, 2), pady=4)

        # Pizza name + size
        ctk.CTkLabel(
            row,
            text=f"{item['pizza_name']}  ({item['size']})",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_DARK, anchor="w",
        ).grid(row=0, column=1, sticky="w", padx=(0, 12))

        # Toppings
        toppings_text = item.get("toppings") or "—"
        ctk.CTkLabel(
            row, text=toppings_text,
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED,
            anchor="w",
        ).grid(row=0, column=2, sticky="w")

        # Price
        ctk.CTkLabel(
            row, text=f"{item['item_price']:.0f} DA",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=ACCENT_DARK, anchor="e",
        ).grid(row=0, column=3, sticky="e", padx=(0, 8))