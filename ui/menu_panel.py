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


class MenuPanel:
    """
    Builds and manages the 'Create Order' page.

    Layout (left | right):
        Left  — pizza grid → size selector → toppings list
        Right — live order summary + send to kitchen button

    Flow:
        1. Reception guy clicks a pizza card   → size buttons appear
        2. He picks a size                     → toppings list appears
        3. He checks optional toppings         → price updates live
        4. He clicks 'Send to kitchen'         → order saved + receipt shown
    """

    def __init__(self, parent_frame: ctk.CTkFrame, db: Database, order_screen):
        """
        Args:
            parent_frame  : the 'create_order' page frame from OrderScreen
            db            : shared Database instance
            order_screen  : reference to OrderScreen so we can update the badge
        """
        self.frame        = parent_frame
        self.db           = db
        self.order_screen = order_screen

        # ── State ────────────────────────────────────────────────────────────
        self.selected_pizza : dict | None = None   # full pizza dict from db
        self.selected_size  : str  | None = None   # 'Normale' or 'Mega'
        self.selected_price : float       = 0.0    # price for chosen size
        self.topping_vars   : dict[str, ctk.BooleanVar] = {}  # key = topping name
        self.topping_prices : dict[str, float]           = {}  # key = topping name

        # References we need to update dynamically
        self.pizza_cards     : dict[int, ctk.CTkFrame] = {}
        self.size_buttons    : dict[str, ctk.CTkButton] = {}
        self.summary_widgets : dict[str, ctk.CTkLabel] = {}

        self._build()

    # ─────────────────────────────────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────────────────────────────────

    def _build(self):
        """
        Build the full two-column layout inside the parent frame.
        """
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=0)
        self.frame.grid_rowconfigure(0, weight=1)

        # ── Left column (scrollable) ─────────────────────────────────────────
        self.left_scroll = ctk.CTkScrollableFrame(
            self.frame,
            fg_color=CONTENT_BG,
            scrollbar_button_color=BORDER_COLOR,
            scrollbar_button_hover_color=ACCENT,
        )
        self.left_scroll.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        self.left_scroll.grid_columnconfigure(0, weight=1)

        # ── Right column (fixed width summary panel) ─────────────────────────
        self.right_panel = ctk.CTkFrame(
            self.frame,
            width=260,
            fg_color=CONTENT_BG,
        )
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 16), pady=16)
        self.right_panel.grid_propagate(False)
        self.right_panel.grid_columnconfigure(0, weight=1)

        # Fill both columns
        self._build_left()
        self._build_right()

    # ── Left column ───────────────────────────────────────────────────────────

    def _build_left(self):
        row = 0

        # ── Section 1: Pizza selection ───────────────────────────────────────
        self._section_label(self.left_scroll, "1 — Choose a pizza", row)
        row += 1

        self.pizza_grid_frame = ctk.CTkFrame(
            self.left_scroll,
            fg_color="transparent",
        )
        self.pizza_grid_frame.grid(row=row, column=0, sticky="ew", pady=(0, 16))
        row += 1

        self._populate_pizza_grid()

        # ── Section 2: Size ───────────────────────────────────────────────────
        self._section_label(self.left_scroll, "2 — Choose a size", row)
        row += 1

        self.size_frame = ctk.CTkFrame(self.left_scroll, fg_color="transparent")
        self.size_frame.grid(row=row, column=0, sticky="ew", pady=(0, 16))
        self.size_frame.grid_columnconfigure((0, 1), weight=1)
        row += 1

        self._build_size_buttons()

        # ── Section 3: Toppings ───────────────────────────────────────────────
        self._section_label(self.left_scroll, "3 — Add toppings  (optional)", row)
        row += 1

        self.toppings_frame = ctk.CTkFrame(self.left_scroll, fg_color="transparent")
        self.toppings_frame.grid(row=row, column=0, sticky="ew", pady=(0, 16))
        self.toppings_frame.grid_columnconfigure(0, weight=1)
        row += 1

        self._populate_toppings()

    def _section_label(self, parent, text: str, row: int):
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_LABEL,
            anchor="w",
        ).grid(row=row, column=0, sticky="ew", pady=(8, 4))

    # ── Pizza grid ────────────────────────────────────────────────────────────

    def _populate_pizza_grid(self):
        """
        Load pizzas from the database and render a card for each one.
        4 cards per row.
        """
        # Clear existing cards
        for widget in self.pizza_grid_frame.winfo_children():
            widget.destroy()
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
        """
        Build a single clickable pizza card showing name and description.
        """
        card = ctk.CTkFrame(
            self.pizza_grid_frame,
            fg_color=CARD_BG,
            border_width=1,
            border_color=BORDER_COLOR,
            corner_radius=10,
            cursor="hand2",
        )

        # Pizza name
        name_label = ctk.CTkLabel(
            card,
            text=pizza["name"],
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_DARK,
            anchor="w",
        )
        name_label.pack(fill="x", padx=10, pady=(10, 2))

        # Ingredients description
        desc_label = ctk.CTkLabel(
            card,
            text=pizza.get("ingrediants", ""),
            font=ctk.CTkFont(size=10),
            text_color=TEXT_MUTED,
            anchor="w",
            wraplength=140,
            justify="left",
        )
        desc_label.pack(fill="x", padx=10, pady=(0, 6))

        # Price range
        price_label = ctk.CTkLabel(
            card,
            text=f"N: {int(pizza['base_price'])} DA   M: {int(pizza['mega_price'])} DA",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=ACCENT_DARK,
            anchor="w",
        )
        price_label.pack(fill="x", padx=10, pady=(0, 10))

        # Bind click on card and all children
        for widget in [card, name_label, desc_label, price_label]:
            widget.bind("<Button-1>", lambda e, p=pizza: self._on_pizza_select(p))

        return card

    def _on_pizza_select(self, pizza: dict):
        """
        Called when a pizza card is clicked.
        Highlights the selected card and resets size + summary.
        """
        self.selected_pizza = pizza
        self.selected_size   = None
        self.selected_price  = 0.0

        # Reset size button styles
        for btn in self.size_buttons.values():
            btn.configure(fg_color=CARD_BG, text_color=TEXT_MUTED, border_color=BORDER_COLOR)

        # Highlight the selected card, reset others
        for pid, card in self.pizza_cards.items():
            if pid == pizza["pizza_id"]:
                card.configure(border_color=ACCENT, fg_color=ACCENT_LIGHT)
            else:
                card.configure(border_color=BORDER_COLOR, fg_color=CARD_BG)

        self._update_summary()

    # ── Size buttons ──────────────────────────────────────────────────────────

    def _build_size_buttons(self):
        """
        Build the Normale and Mega size selector buttons.
        Prices update dynamically once a pizza is selected.
        """
        sizes = [
            ("Normale", 0),   # column index
            ("Mega",    1),
        ]
        for label, col in sizes:
            btn = ctk.CTkButton(
                self.size_frame,
                text=f"{label}\n—",
                height=52,
                corner_radius=8,
                fg_color=CARD_BG,
                hover_color=ACCENT_LIGHT,
                text_color=TEXT_MUTED,
                border_width=1,
                border_color=BORDER_COLOR,
                font=ctk.CTkFont(size=13),
                command=lambda s=label: self._on_size_select(s),
            )
            btn.grid(row=0, column=col, padx=4, sticky="ew")
            self.size_buttons[label] = btn

    def _on_size_select(self, size: str):
        """
        Called when Normale or Mega is clicked.
        Updates price and summary.
        """
        if not self.selected_pizza:
            self._shake_label("Please select a pizza first")
            return

        self.selected_size = size
        if size == "Normale":
            self.selected_price = self.selected_pizza["base_price"]
        else:
            self.selected_price = self.selected_pizza["mega_price"]

        # Highlight selected size button
        for s, btn in self.size_buttons.items():
            if s == size:
                btn.configure(fg_color=ACCENT_LIGHT, text_color=ACCENT_DARK, border_color=ACCENT)
            else:
                btn.configure(fg_color=CARD_BG, text_color=TEXT_MUTED, border_color=BORDER_COLOR)

        self._update_summary()

    def _refresh_size_button_labels(self):
        """
        Update the price shown inside size buttons when a pizza is selected.
        """
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
        """
        Load supplements from the database and render a checkbox row for each.
        Falls back to a default list if the supplements table is empty.
        """
        for widget in self.toppings_frame.winfo_children():
            widget.destroy()
        self.topping_vars.clear()
        self.topping_prices.clear()

        # Load from DB — using a hardcoded default list for now.
        # This will be replaced when the supplements manager is built.
        default_toppings = [
            ("Extra fromage",  1.50),
            ("Jambon",         2.00),
            ("Champignons",    1.00),
            ("Olives",         1.00),
            ("Oignons",        0.50),
            ("Poivrons",       0.50),
            ("Jalapenos",      1.50),
            ("Oeuf",           1.00),
        ]

        for i, (name, price) in enumerate(default_toppings):
            var = ctk.BooleanVar(value=False)
            self.topping_vars[name]   = var
            self.topping_prices[name] = price

            row_frame = ctk.CTkFrame(
                self.toppings_frame,
                fg_color=CARD_BG,
                border_width=1,
                border_color=BORDER_COLOR,
                corner_radius=8,
            )
            row_frame.grid(row=i, column=0, sticky="ew", pady=3)
            row_frame.grid_columnconfigure(1, weight=1)

            # Checkbox
            cb = ctk.CTkCheckBox(
                row_frame,
                text="",
                variable=var,
                width=20,
                checkbox_width=18,
                checkbox_height=18,
                fg_color=ACCENT,
                hover_color=ACCENT_DARK,
                border_color=BORDER_COLOR,
                command=self._update_summary,
            )
            cb.grid(row=0, column=0, padx=(10, 6), pady=10)

            # Topping name
            ctk.CTkLabel(
                row_frame,
                text=name,
                font=ctk.CTkFont(size=13),
                text_color=TEXT_DARK,
                anchor="w",
            ).grid(row=0, column=1, sticky="ew")

            # Price
            ctk.CTkLabel(
                row_frame,
                text=f"+{price:.2f} DA",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=ACCENT_DARK,
                anchor="e",
            ).grid(row=0, column=2, padx=(0, 12))

    # ── Right panel: order summary ────────────────────────────────────────────

    def _build_right(self):
        """
        Build the order summary panel on the right side.
        Contains: summary card + send to kitchen button.
        """
        self.right_panel.grid_rowconfigure(0, weight=1)

        # Summary card
        summary_card = ctk.CTkFrame(
            self.right_panel,
            fg_color=CARD_BG,
            border_width=1,
            border_color=BORDER_COLOR,
            corner_radius=12,
        )
        summary_card.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        summary_card.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(
            summary_card,
            text="Order Summary",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_LABEL,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))

        # ── Summary rows ─────────────────────────────────────────────────────
        labels = [
            ("pizza_key",    "Pizza",      "—"),
            ("size_key",     "Size",       "—"),
            ("base_key",     "Base price", "—"),
        ]
        for grid_row, (key, left_text, default) in enumerate(labels, start=1):
            ctk.CTkLabel(
                summary_card,
                text=left_text,
                font=ctk.CTkFont(size=12),
                text_color=TEXT_MUTED,
                anchor="w",
            ).grid(row=grid_row, column=0, sticky="w", padx=14, pady=2)

            val_label = ctk.CTkLabel(
                summary_card,
                text=default,
                font=ctk.CTkFont(size=12),
                text_color=TEXT_DARK,
                anchor="e",
            )
            val_label.grid(row=grid_row, column=0, sticky="e", padx=14, pady=2)
            self.summary_widgets[key] = val_label

        # Toppings added label
        ctk.CTkLabel(
            summary_card,
            text="Toppings",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
            anchor="w",
        ).grid(row=4, column=0, sticky="w", padx=14, pady=2)

        self.toppings_cost_label = ctk.CTkLabel(
            summary_card,
            text="+0.00 DA",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_DARK,
            anchor="e",
        )
        self.toppings_cost_label.grid(row=4, column=0, sticky="e", padx=14, pady=2)

        # Toppings chips (small tags showing selected toppings)
        self.chips_frame = ctk.CTkFrame(summary_card, fg_color="transparent")
        self.chips_frame.grid(row=5, column=0, sticky="ew", padx=14, pady=(2, 8))

        # Divider
        ctk.CTkFrame(
            summary_card,
            height=1,
            fg_color=BORDER_COLOR,
        ).grid(row=6, column=0, sticky="ew", padx=14)

        # Total row
        ctk.CTkLabel(
            summary_card,
            text="TOTAL",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_DARK,
            anchor="w",
        ).grid(row=7, column=0, sticky="w", padx=14, pady=(10, 14))

        self.total_label = ctk.CTkLabel(
            summary_card,
            text="0 DA",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ACCENT_DARK,
            anchor="e",
        )
        self.total_label.grid(row=7, column=0, sticky="e", padx=14, pady=(10, 14))

        # ── Send to kitchen button ────────────────────────────────────────────
        self.send_btn = ctk.CTkButton(
            self.right_panel,
            text="🖨  Send to kitchen",
            height=44,
            corner_radius=8,
            fg_color=ACCENT,
            hover_color=ACCENT_DARK,
            text_color=TEXT_DARK,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_send_to_kitchen,
        )
        self.send_btn.grid(row=1, column=0, sticky="ew")

        # Error / info message below the button
        self.msg_label = ctk.CTkLabel(
            self.right_panel,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=DANGER,
        )
        self.msg_label.grid(row=2, column=0, pady=(4, 0))

    # ── Summary logic ─────────────────────────────────────────────────────────

    def _update_summary(self):
        """
        Recalculate and refresh the entire right-panel summary.
        Called whenever pizza, size, or any topping changes.
        """
        # Refresh size button labels whenever summary is updated after pizza select
        self._refresh_size_button_labels()

        pizza_name = self.selected_pizza["name"] if self.selected_pizza else "—"
        size_name  = self.selected_size           if self.selected_size   else "—"
        base_price = self.selected_price

        # Calculate toppings total
        topping_total = sum(
            self.topping_prices[name]
            for name, var in self.topping_vars.items()
            if var.get()
        )
        selected_toppings = [name for name, var in self.topping_vars.items() if var.get()]
        grand_total = base_price + topping_total

        # Update labels
        self.summary_widgets["pizza_key"].configure(text=pizza_name)
        self.summary_widgets["size_key"].configure(text=size_name)
        self.summary_widgets["base_key"].configure(
            text=f"{int(base_price)} DA" if base_price else "—"
        )
        self.toppings_cost_label.configure(
            text=f"+{topping_total:.2f} DA" if topping_total else "+0.00 DA"
        )
        self.total_label.configure(
            text=f"{grand_total:.0f} DA" if grand_total else "0 DA"
        )

        # Rebuild topping chips
        for w in self.chips_frame.winfo_children():
            w.destroy()
        for name in selected_toppings:
            ctk.CTkLabel(
                self.chips_frame,
                text=name,
                font=ctk.CTkFont(size=10),
                fg_color=ACCENT_LIGHT,
                text_color=ACCENT_DARK,
                corner_radius=6,
                padx=6,
                pady=2,
            ).pack(side="left", padx=2, pady=2)

        # Clear any previous message
        self.msg_label.configure(text="")

    # ── Send to kitchen ───────────────────────────────────────────────────────

    def _on_send_to_kitchen(self):
        """
        Validate the order, save it to the database, update the pending badge,
        and reset the form for the next order.
        """
        # ── Validation ───────────────────────────────────────────────────────
        if not self.selected_pizza:
            self._show_message("⚠  Please select a pizza first.")
            return
        if not self.selected_size:
            self._show_message("⚠  Please choose a size (Normale or Mega).")
            return

        # ── Build order data ─────────────────────────────────────────────────
        pizza_name  = self.selected_pizza["name"]
        size        = self.selected_size
        final_price = self.selected_price + sum(
            self.topping_prices[name]
            for name, var in self.topping_vars.items()
            if var.get()
        )
        toppings_str = ", ".join(
            name for name, var in self.topping_vars.items() if var.get()
        )

        # ── Save to database ─────────────────────────────────────────────────
        order_id = self.db.save_order(
            pizza_name  = pizza_name,
            size        = size,
            toppings    = toppings_str,
            final_price = final_price,
        )

        # ── Update pending badge ─────────────────────────────────────────────
        pending = self.db.get_all_orders()
        self.order_screen.update_pending_badge(len(pending))

        # ── Show confirmation ─────────────────────────────────────────────────
        self._show_message(
            f"✓  Order #{order_id} sent!  ({pizza_name} {size} — {final_price:.0f} DA)",
            success=True,
        )

        # ── Reset form ───────────────────────────────────────────────────────
        self._reset_form()

    def _reset_form(self):
        """
        Reset all selections so the receptionist can start the next order.
        """
        self.selected_pizza  = None
        self.selected_size   = None
        self.selected_price  = 0.0

        # Deselect all pizza cards
        for card in self.pizza_cards.values():
            card.configure(border_color=BORDER_COLOR, fg_color=CARD_BG)

        # Reset size buttons
        for btn in self.size_buttons.values():
            btn.configure(
                text=btn.cget("text").split("\n")[0] + "\n—",
                fg_color=CARD_BG,
                text_color=TEXT_MUTED,
                border_color=BORDER_COLOR,
            )

        # Uncheck all toppings
        for var in self.topping_vars.values():
            var.set(False)

        # Reset summary
        self._update_summary()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _show_message(self, text: str, success: bool = False):
        """Display a message below the send button."""
        color = "#16A34A" if success else DANGER
        self.msg_label.configure(text=text, text_color=color)
        # Auto-clear after 4 seconds
        self.frame.after(4000, lambda: self.msg_label.configure(text=""))

    def _shake_label(self, text: str):
        """Show a quick error message."""
        self._show_message(f"⚠  {text}")