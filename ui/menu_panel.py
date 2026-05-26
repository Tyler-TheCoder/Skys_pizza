import customtkinter as ctk
from db.database import Database


# ── Brand colors (must match order_screen.py) ────────────────────────────────
SIDEBAR_BG    = "#1C1008"
ACCENT        = "#F59E0B"
ACCENT_DARK   = "#B45309"
ACCENT_LIGHT  = "#FEF3C7"
TOPBAR_BG     = "#FFFFFF"
CONTENT_BG    = "#FFF8F0"
BORDER_COLOR  = "#F5C060"
CARD_BG       = "#FFFFFF"
TEXT_DARK     = "#1C1008"
TEXT_MUTED    = "#78716C"
TEXT_LABEL    = "#A16207"
DANGER        = "#EF4444"
CART_ITEM_BG  = "#FFFBEB"


class MenuPanel:
    """
    Builds and manages the 'Create Order' page.

    New multi-item flow:
        Left  — pizza grid → size selector → toppings list → "Add to order" btn
        Right — live cart  (list of added pizzas) + "Send to kitchen" btn

    The receptionist can add as many pizzas as they like before sending.
    Each cart row shows pizza, size, toppings, price and a × remove button.
    """

    def __init__(self, parent_frame: ctk.CTkFrame, db: Database, order_screen):
        self.frame        = parent_frame
        self.db           = db
        self.order_screen = order_screen

        # ── Current selection state (left panel) ─────────────────────────────
        self.selected_pizza : dict | None = None
        self.selected_size  : str  | None = None
        self.selected_price : float       = 0.0
        self.topping_vars   : dict[str, ctk.BooleanVar] = {}
        self.topping_prices : dict[str, float]          = {}

        # ── Cart state (right panel) ──────────────────────────────────────────
        # Each entry: {'pizza_name', 'size', 'toppings', 'item_price'}
        self.cart: list[dict] = []

        # Widget references for dynamic updates
        self.pizza_cards  : dict[int, ctk.CTkFrame]   = {}
        self.size_buttons : dict[str, ctk.CTkButton]  = {}

        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=0)
        self.frame.grid_rowconfigure(0, weight=1)

        # Left scrollable column
        self.left_scroll = ctk.CTkScrollableFrame(
            self.frame,
            fg_color=CONTENT_BG,
            scrollbar_button_color=BORDER_COLOR,
            scrollbar_button_hover_color=ACCENT,
        )
        self.left_scroll.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        self.left_scroll.grid_columnconfigure(0, weight=1)

        # Right fixed-width cart panel
        self.right_panel = ctk.CTkFrame(self.frame, width=280, fg_color=CONTENT_BG)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 16), pady=16)
        self.right_panel.grid_propagate(False)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(0, weight=1)

        self._build_left()
        self._build_right()

    # ── Left column ───────────────────────────────────────────────────────────

    def _build_left(self):
        row = 0

        # Section 1 — pizza
        self._section_label(self.left_scroll, "1 — Choose a pizza", row); row += 1
        self.pizza_grid_frame = ctk.CTkFrame(self.left_scroll, fg_color="transparent")
        self.pizza_grid_frame.grid(row=row, column=0, sticky="ew", pady=(0, 16)); row += 1
        self._populate_pizza_grid()

        # Section 2 — size
        self._section_label(self.left_scroll, "2 — Choose a size", row); row += 1
        self.size_frame = ctk.CTkFrame(self.left_scroll, fg_color="transparent")
        self.size_frame.grid(row=row, column=0, sticky="ew", pady=(0, 16))
        self.size_frame.grid_columnconfigure((0, 1), weight=1); row += 1
        self._build_size_buttons()

        # Section 3 — toppings
        self._section_label(self.left_scroll, "3 — Add toppings  (optional)", row); row += 1
        self.toppings_frame = ctk.CTkFrame(self.left_scroll, fg_color="transparent")
        self.toppings_frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        self.toppings_frame.grid_columnconfigure(0, weight=1); row += 1
        self._populate_toppings()

        # "Add to order" button
        self.add_btn = ctk.CTkButton(
            self.left_scroll,
            text="+ Add to order",
            height=42,
            corner_radius=8,
            fg_color=ACCENT,
            hover_color=ACCENT_DARK,
            text_color=TEXT_DARK,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_add_to_cart,
        )
        self.add_btn.grid(row=row, column=0, sticky="ew", pady=(0, 8)); row += 1

        # Inline message (validation errors / success)
        self.add_msg_label = ctk.CTkLabel(
            self.left_scroll, text="",
            font=ctk.CTkFont(size=11), text_color=DANGER,
        )
        self.add_msg_label.grid(row=row, column=0)

    def _section_label(self, parent, text: str, row: int):
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_LABEL, anchor="w",
        ).grid(row=row, column=0, sticky="ew", pady=(8, 4))

    # ── Pizza grid ────────────────────────────────────────────────────────────

    def _populate_pizza_grid(self):
        for w in self.pizza_grid_frame.winfo_children():
            w.destroy()
        self.pizza_cards.clear()

        pizzas = self.db.get_menu_items()
        cols   = 4
        for i, pizza in enumerate(pizzas):
            col = i % cols
            row = i // cols
            self.pizza_grid_frame.grid_columnconfigure(col, weight=1)
            card = self._make_pizza_card(pizza)
            card.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
            self.pizza_cards[pizza["pizza_id"]] = card

    def _make_pizza_card(self, pizza: dict) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            self.pizza_grid_frame,
            fg_color=CARD_BG, border_width=1, border_color=BORDER_COLOR,
            corner_radius=10, cursor="hand2",
        )
        name_lbl = ctk.CTkLabel(
            card, text=pizza["name"],
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_DARK, anchor="w",
        )
        name_lbl.pack(fill="x", padx=10, pady=(10, 2))

        desc_lbl = ctk.CTkLabel(
            card, text=pizza.get("ingrediants", ""),
            font=ctk.CTkFont(size=10), text_color=TEXT_MUTED,
            anchor="w", wraplength=140, justify="left",
        )
        desc_lbl.pack(fill="x", padx=10, pady=(0, 6))

        price_lbl = ctk.CTkLabel(
            card,
            text=f"N: {int(pizza['base_price'])} DA   M: {int(pizza['mega_price'])} DA",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=ACCENT_DARK, anchor="w",
        )
        price_lbl.pack(fill="x", padx=10, pady=(0, 10))

        for w in [card, name_lbl, desc_lbl, price_lbl]:
            w.bind("<Button-1>", lambda e, p=pizza: self._on_pizza_select(p))
        return card

    def _on_pizza_select(self, pizza: dict):
        self.selected_pizza = pizza
        self.selected_size  = None
        self.selected_price = 0.0

        for btn in self.size_buttons.values():
            btn.configure(fg_color=CARD_BG, text_color=TEXT_MUTED, border_color=BORDER_COLOR)

        for pid, card in self.pizza_cards.items():
            if pid == pizza["pizza_id"]:
                card.configure(border_color=ACCENT, fg_color=ACCENT_LIGHT)
            else:
                card.configure(border_color=BORDER_COLOR, fg_color=CARD_BG)

        self._refresh_size_button_labels()
        self.add_msg_label.configure(text="")

    # ── Size buttons ──────────────────────────────────────────────────────────

    def _build_size_buttons(self):
        for label, col in [("Normale", 0), ("Mega", 1)]:
            btn = ctk.CTkButton(
                self.size_frame, text=f"{label}\n—", height=52,
                corner_radius=8, fg_color=CARD_BG, hover_color=ACCENT_LIGHT,
                text_color=TEXT_MUTED, border_width=1, border_color=BORDER_COLOR,
                font=ctk.CTkFont(size=13),
                command=lambda s=label: self._on_size_select(s),
            )
            btn.grid(row=0, column=col, padx=4, sticky="ew")
            self.size_buttons[label] = btn

    def _on_size_select(self, size: str):
        if not self.selected_pizza:
            self._show_add_msg("Please select a pizza first.")
            return
        self.selected_size  = size
        self.selected_price = (
            self.selected_pizza["base_price"] if size == "Normale"
            else self.selected_pizza["mega_price"]
        )
        for s, btn in self.size_buttons.items():
            if s == size:
                btn.configure(fg_color=ACCENT_LIGHT, text_color=ACCENT_DARK, border_color=ACCENT)
            else:
                btn.configure(fg_color=CARD_BG, text_color=TEXT_MUTED, border_color=BORDER_COLOR)
        self.add_msg_label.configure(text="")

    def _refresh_size_button_labels(self):
        if not self.selected_pizza:
            return
        self.size_buttons["Normale"].configure(
            text=f"Normale\n{int(self.selected_pizza['base_price'])} DA"
        )
        self.size_buttons["Mega"].configure(
            text=f"Mega\n{int(self.selected_pizza['mega_price'])} DA"
        )

    # ── Toppings ──────────────────────────────────────────────────────────────

    def _populate_toppings(self):
        for w in self.toppings_frame.winfo_children():
            w.destroy()
        self.topping_vars.clear()
        self.topping_prices.clear()

        default_toppings = [
            ("Extra fromage", 1.50),
            ("Jambon",        2.00),
            ("Champignons",   1.00),
            ("Olives",        1.00),
            ("Oignons",       0.50),
            ("Poivrons",      0.50),
            ("Jalapenos",     1.50),
            ("Oeuf",          1.00),
        ]
        for i, (name, price) in enumerate(default_toppings):
            var = ctk.BooleanVar(value=False)
            self.topping_vars[name]   = var
            self.topping_prices[name] = price

            row_frame = ctk.CTkFrame(
                self.toppings_frame, fg_color=CARD_BG,
                border_width=1, border_color=BORDER_COLOR, corner_radius=8,
            )
            row_frame.grid(row=i, column=0, sticky="ew", pady=3)
            row_frame.grid_columnconfigure(1, weight=1)

            ctk.CTkCheckBox(
                row_frame, text="", variable=var,
                width=20, checkbox_width=18, checkbox_height=18,
                fg_color=ACCENT, hover_color=ACCENT_DARK, border_color=BORDER_COLOR,
                command=lambda: None,   # no live summary needed anymore
            ).grid(row=0, column=0, padx=(10, 6), pady=10)

            ctk.CTkLabel(
                row_frame, text=name,
                font=ctk.CTkFont(size=13), text_color=TEXT_DARK, anchor="w",
            ).grid(row=0, column=1, sticky="ew")

            ctk.CTkLabel(
                row_frame, text=f"+{price:.2f} DA",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=ACCENT_DARK, anchor="e",
            ).grid(row=0, column=2, padx=(0, 12))

    # ── Add to cart ───────────────────────────────────────────────────────────

    def _on_add_to_cart(self):
        """Validate the current selection and push it onto the cart."""
        if not self.selected_pizza:
            self._show_add_msg("⚠  Please select a pizza first.")
            return
        if not self.selected_size:
            self._show_add_msg("⚠  Please choose a size (Normale or Mega).")
            return

        topping_extra = sum(
            self.topping_prices[n] for n, v in self.topping_vars.items() if v.get()
        )
        toppings_str = ", ".join(n for n, v in self.topping_vars.items() if v.get())
        item_price   = self.selected_price + topping_extra

        self.cart.append({
            'pizza_name': self.selected_pizza["name"],
            'size':        self.selected_size,
            'toppings':    toppings_str,
            'item_price':  item_price,
        })

        # Give a quick success hint
        self._show_add_msg(
            f"✓  {self.selected_pizza['name']} ({self.selected_size}) added.",
            success=True,
        )

        # Reset the left-panel selection for the next pizza
        self._reset_selection()
        self._refresh_cart()

    def _reset_selection(self):
        """Clear the left panel so the receptionist can pick the next pizza."""
        self.selected_pizza  = None
        self.selected_size   = None
        self.selected_price  = 0.0

        for card in self.pizza_cards.values():
            card.configure(border_color=BORDER_COLOR, fg_color=CARD_BG)

        for btn in self.size_buttons.values():
            btn.configure(
                text=btn.cget("text").split("\n")[0] + "\n—",
                fg_color=CARD_BG, text_color=TEXT_MUTED, border_color=BORDER_COLOR,
            )

        for var in self.topping_vars.values():
            var.set(False)

    # ── Right panel: cart ─────────────────────────────────────────────────────

    def _build_right(self):
        """Build the cart panel: header, scrollable item list, total, send btn."""
        # ── Card wrapper ──────────────────────────────────────────────────────
        cart_card = ctk.CTkFrame(
            self.right_panel, fg_color=CARD_BG,
            border_width=1, border_color=BORDER_COLOR, corner_radius=12,
        )
        cart_card.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        cart_card.grid_columnconfigure(0, weight=1)
        cart_card.grid_rowconfigure(1, weight=1)

        # Title row
        title_row = ctk.CTkFrame(cart_card, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 4))
        title_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            title_row, text="Order",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_LABEL,
        ).grid(row=0, column=0, sticky="w")

        self.item_count_label = ctk.CTkLabel(
            title_row, text="0 items",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED,
        )
        self.item_count_label.grid(row=0, column=1, sticky="e")

        # Scrollable item list
        self.cart_scroll = ctk.CTkScrollableFrame(
            cart_card, fg_color="transparent",
            scrollbar_button_color=BORDER_COLOR,
            scrollbar_button_hover_color=ACCENT,
        )
        self.cart_scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        self.cart_scroll.grid_columnconfigure(0, weight=1)

        # Empty-cart placeholder label
        self.empty_label = ctk.CTkLabel(
            self.cart_scroll,
            text="No items yet.\nAdd a pizza from the left.",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED, justify="center",
        )
        self.empty_label.pack(pady=40)

        # Divider
        ctk.CTkFrame(cart_card, height=1, fg_color=BORDER_COLOR).grid(
            row=2, column=0, sticky="ew", padx=14
        )

        # Total row
        total_row = ctk.CTkFrame(cart_card, fg_color="transparent")
        total_row.grid(row=3, column=0, sticky="ew", padx=14, pady=(8, 14))
        total_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            total_row, text="TOTAL",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_DARK,
        ).grid(row=0, column=0, sticky="w")

        self.total_label = ctk.CTkLabel(
            total_row, text="0 DA",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT_DARK,
        )
        self.total_label.grid(row=0, column=1, sticky="e")

        # ── Send to kitchen button ────────────────────────────────────────────
        self.send_btn = ctk.CTkButton(
            self.right_panel,
            text="🖨  Send to kitchen",
            height=44, corner_radius=8,
            fg_color=ACCENT, hover_color=ACCENT_DARK,
            text_color=TEXT_DARK,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_send_to_kitchen,
        )
        self.send_btn.grid(row=1, column=0, sticky="ew")

        self.send_msg_label = ctk.CTkLabel(
            self.right_panel, text="",
            font=ctk.CTkFont(size=11), text_color=DANGER,
        )
        self.send_msg_label.grid(row=2, column=0, pady=(4, 0))

    # ── Cart rendering ────────────────────────────────────────────────────────

    def _refresh_cart(self):
        """Rebuild the cart item list from self.cart."""
        for w in self.cart_scroll.winfo_children():
            w.destroy()

        if not self.cart:
            self.empty_label = ctk.CTkLabel(
                self.cart_scroll,
                text="No items yet.\nAdd a pizza from the left.",
                font=ctk.CTkFont(size=12), text_color=TEXT_MUTED, justify="center",
            )
            self.empty_label.pack(pady=40)
            self.item_count_label.configure(text="0 items")
            self.total_label.configure(text="0 DA")
            return

        for idx, item in enumerate(self.cart):
            self._make_cart_row(idx, item)

        count = len(self.cart)
        total = sum(i['item_price'] for i in self.cart)
        self.item_count_label.configure(text=f"{count} item{'s' if count != 1 else ''}")
        self.total_label.configure(text=f"{total:.0f} DA")
        self.order_screen._bind_mousewheel(self.cart_scroll)

    def _make_cart_row(self, idx: int, item: dict):
        """Render one cart item row."""
        row = ctk.CTkFrame(
            self.cart_scroll, fg_color=CART_ITEM_BG,
            border_width=1, border_color=BORDER_COLOR, corner_radius=8,
        )
        row.pack(fill="x", pady=3, padx=2)
        row.grid_columnconfigure(0, weight=1)

        # Top line: pizza name + size + × button
        top = ctk.CTkFrame(row, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 0))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top,
            text=f"{item['pizza_name']}  ·  {item['size']}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_DARK, anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            top, text="×", width=22, height=22,
            corner_radius=6, fg_color="transparent",
            hover_color="#FEE2E2", text_color=DANGER,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda i=idx: self._remove_cart_item(i),
        ).grid(row=0, column=1, sticky="e")

        # Bottom line: toppings + price
        bot = ctk.CTkFrame(row, fg_color="transparent")
        bot.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 6))
        bot.grid_columnconfigure(0, weight=1)

        toppings_text = item['toppings'] if item['toppings'] else "No extras"
        ctk.CTkLabel(
            bot, text=toppings_text,
            font=ctk.CTkFont(size=10), text_color=TEXT_MUTED,
            anchor="w", wraplength=170, justify="left",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            bot, text=f"{item['item_price']:.0f} DA",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=ACCENT_DARK, anchor="e",
        ).grid(row=0, column=1, sticky="e")

    def _remove_cart_item(self, idx: int):
        """Remove the item at position idx from the cart and re-render."""
        if 0 <= idx < len(self.cart):
            self.cart.pop(idx)
        self._refresh_cart()

    # ── Send to kitchen ───────────────────────────────────────────────────────

    def _on_send_to_kitchen(self):
        if not self.cart:
            self._show_send_msg("⚠  Add at least one pizza before sending.")
            return

        order_id = self.db.create_order(self.cart)

        all_orders = self.db.get_all_orders()
        self.order_screen.update_pending_badge(len(all_orders))

        total = sum(i['item_price'] for i in self.cart)
        count = len(self.cart)
        self._show_send_msg(
            f"✓  Order #{order_id} sent!  {count} pizza{'s' if count != 1 else ''}  —  {total:.0f} DA",
            success=True,
        )

        self.cart.clear()
        self._refresh_cart()
        self._reset_selection()

    # ── Message helpers ───────────────────────────────────────────────────────

    def _show_add_msg(self, text: str, success: bool = False):
        color = "#16A34A" if success else DANGER
        self.add_msg_label.configure(text=text, text_color=color)
        self.frame.after(4000, lambda: self.add_msg_label.configure(text=""))

    def _show_send_msg(self, text: str, success: bool = False):
        color = "#16A34A" if success else DANGER
        self.send_msg_label.configure(text=text, text_color=color)
        self.frame.after(4000, lambda: self.send_msg_label.configure(text=""))