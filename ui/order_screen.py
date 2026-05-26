import customtkinter as ctk
from db.database import Database
from ui.menu_panel import MenuPanel
from ui.history_panel import HistoryPanel


# ── Brand colors ─────────────────────────────────────────────────────────────
SIDEBAR_BG   = "#1C1008"   # dark brown — sidebar background
ACCENT       = "#F59E0B"   # amber — active highlights, buttons
ACCENT_DARK  = "#B45309"   # darker amber — hover states
TOPBAR_BG    = "#FFFFFF"   # white topbar
CONTENT_BG   = "#FFF8F0"   # warm off-white — content area
BORDER_COLOR = "#F5C060"   # light amber border
TEXT_DARK    = "#1C1008"   # near-black text
TEXT_MUTED   = "#78716C"   # muted gray-brown text
TAB_ACTIVE_BG = "#FEF3C7"  # light amber — active tab background


class OrderScreen:
    """
    Main application window.
    Builds the full layout:
        - Left sidebar  : navigation between sections (Menu, Administration)
        - Top bar       : sub-tabs for the active section
        - Content area  : swappable frames for each page
    """

    def __init__(self, root: ctk.CTk, db: Database):
        self.root = root
        self.db   = db

        # Track which nav item and tab are currently active
        self.active_nav  = "menu"
        self.active_page = "create_order"

        # Keep references to every page frame so we can show/hide them
        self.pages: dict[str, ctk.CTkFrame] = {}

        # Keep references to sidebar buttons and tab buttons for styling
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.tab_buttons: dict[str, ctk.CTkButton] = {}

        # Build the layout
        self._build_layout()
        self._build_sidebar()
        self._build_topbar()
        self._build_content_area()

        # Show the default page on startup
        self._show_page("create_order")

    # ── Layout skeleton ───────────────────────────────────────────────────────

    def _build_layout(self):
        """
        Divide the root window into three zones:
            sidebar_frame | main_frame (topbar_frame on top, content_frame below)
        """
        self.root.configure(fg_color=CONTENT_BG)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Left sidebar
        self.sidebar_frame = ctk.CTkFrame(
            self.root,
            width=72,
            corner_radius=0,
            fg_color=SIDEBAR_BG,
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)   # keep fixed width

        # Right main area
        self.main_frame = ctk.CTkFrame(
            self.root,
            corner_radius=0,
            fg_color=CONTENT_BG,
        )
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Topbar inside main area
        self.topbar_frame = ctk.CTkFrame(
            self.main_frame,
            height=50,
            corner_radius=0,
            fg_color=TOPBAR_BG,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        self.topbar_frame.grid(row=0, column=0, sticky="ew")
        self.topbar_frame.grid_propagate(False)

        # Content area inside main area
        self.content_frame = ctk.CTkFrame(
            self.main_frame,
            corner_radius=0,
            fg_color=CONTENT_BG,
        )
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        """
        Build the left sidebar with the logo and main navigation buttons.
        """
        # Logo area at the top
        logo_frame = ctk.CTkFrame(
            self.sidebar_frame,
            width=44,
            height=44,
            corner_radius=10,
            fg_color=ACCENT,
        )
        logo_frame.pack(pady=(18, 16))
        logo_frame.pack_propagate(False)

        logo_label = ctk.CTkLabel(
            logo_frame,
            text="🍕",
            font=ctk.CTkFont(size=22),
        )
        logo_label.place(relx=0.5, rely=0.5, anchor="center")

        # Navigation buttons
        nav_items = [
            ("menu",  "📋", "Menu"),
            ("admin", "📊", "Admin"),
        ]
        for key, icon, label in nav_items:
            btn = self._make_nav_button(key, icon, label)
            self.nav_buttons[key] = btn

        # Settings button pinned to the bottom
        settings_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="⚙",
            width=48,
            height=48,
            corner_radius=8,
            fg_color="transparent",
            hover_color="#2D1F0E",
            text_color="gray",
            font=ctk.CTkFont(size=18),
        )
        settings_btn.pack(side="bottom", pady=14)

    def _make_nav_button(self, key: str, icon: str, label: str) -> ctk.CTkButton:
        """
        Create and pack a single sidebar navigation button.
        Clicking it switches the active section and updates the topbar tabs.
        """
        btn = ctk.CTkButton(
            self.sidebar_frame,
            text=f"{icon}\n{label}",
            width=48,
            height=52,
            corner_radius=8,
            fg_color="transparent",
            hover_color="#2D1F0E",
            text_color="gray",
            font=ctk.CTkFont(size=10),
            command=lambda k=key: self._on_nav_click(k),
        )
        btn.pack(pady=3)
        return btn

    def _on_nav_click(self, key: str):
        """
        Called when a sidebar nav button is clicked.
        Updates the active section, refreshes button styles,
        and switches the topbar tabs to match the section.
        """
        self.active_nav = key
        self._refresh_nav_styles()
        self._refresh_topbar(key)

    def _refresh_nav_styles(self):
        """
        Update sidebar button colors to reflect which section is active.
        """
        for key, btn in self.nav_buttons.items():
            if key == self.active_nav:
                btn.configure(fg_color="#2D1F0E", text_color=ACCENT)
            else:
                btn.configure(fg_color="transparent", text_color="gray")

    # ── Topbar ────────────────────────────────────────────────────────────────

    # Define which tabs belong to each section
    SECTION_TABS = {
        "menu": [
            ("create_order",  "+ Create order"),
            ("pizzas",        "🍕 Pizzas"),
            ("supplements",   "🥗 Supplements"),
        ],
        "admin": [
            ("history",    "🕐 History"),
            ("statistics", "📈 Statistics"),
        ],
    }

    def _build_topbar(self):
        """
        Build the initial topbar with the tabs for the default section (menu).
        """
        # Section label on the left
        self.section_label = ctk.CTkLabel(
            self.topbar_frame,
            text="Menu",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=ACCENT_DARK,
        )
        self.section_label.pack(side="left", padx=(16, 8))

        # Thin vertical divider
        divider = ctk.CTkFrame(
            self.topbar_frame,
            width=1,
            height=20,
            fg_color=BORDER_COLOR,
        )
        divider.pack(side="left", padx=6)

        # Container for the tab buttons (so we can clear and rebuild them)
        self.tabs_container = ctk.CTkFrame(
            self.topbar_frame,
            fg_color="transparent",
        )
        self.tabs_container.pack(side="left", padx=4)

        # Pending orders badge on the right
        self.pending_badge = ctk.CTkLabel(
            self.topbar_frame,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=ACCENT,
            text_color=TEXT_DARK,
            corner_radius=10,
            width=0,
        )
        self.pending_badge.pack(side="right", padx=16)

        # Render the tabs for the default section
        self._refresh_topbar("menu")

    def _refresh_topbar(self, section: str):
        """
        Clear the current tabs and rebuild them for the given section.
        Also updates the section label text and jumps to the first tab.
        """
        # Update the section label
        self.section_label.configure(
            text="Menu" if section == "menu" else "Administration"
        )

        # Destroy existing tab buttons
        for widget in self.tabs_container.winfo_children():
            widget.destroy()
        self.tab_buttons.clear()

        # Create new tab buttons for the section
        tabs = self.SECTION_TABS.get(section, [])
        for page_key, tab_label in tabs:
            btn = self._make_tab_button(page_key, tab_label)
            self.tab_buttons[page_key] = btn

        # Jump to the first tab of the new section
        if tabs:
            first_key = tabs[0][0]
            self._on_tab_click(first_key)

    def _make_tab_button(self, page_key: str, label: str) -> ctk.CTkButton:
        """
        Create and pack a single topbar tab button.
        """
        btn = ctk.CTkButton(
            self.tabs_container,
            text=label,
            height=30,
            corner_radius=6,
            fg_color="transparent",
            hover_color=TAB_ACTIVE_BG,
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=12),
            border_width=1,
            border_color=TOPBAR_BG,
            command=lambda k=page_key: self._on_tab_click(k),
        )
        btn.pack(side="left", padx=2, pady=9)
        return btn

    def _on_tab_click(self, page_key: str):
        """
        Called when a topbar tab is clicked.
        Updates the active page and refreshes tab styles.
        """
        self.active_page = page_key
        self._refresh_tab_styles()
        self._show_page(page_key)

    def _refresh_tab_styles(self):
        """
        Update tab button colors to reflect which page is active.
        """
        for key, btn in self.tab_buttons.items():
            if key == self.active_page:
                btn.configure(
                    fg_color=TAB_ACTIVE_BG,
                    text_color=ACCENT_DARK,
                    border_color=BORDER_COLOR,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=TEXT_MUTED,
                    border_color=TOPBAR_BG,
                )

    def update_pending_badge(self, count: int):
        """
        Update the pending orders badge in the topbar.
        Called from menu_panel.py after an order is placed.
        Pass 0 to hide the badge.
        """
        if count > 0:
            self.pending_badge.configure(
                text=f"  {count} pending  ",
            )
        else:
            self.pending_badge.configure(text="")

    # ── Content area ──────────────────────────────────────────────────────────

    def _build_content_area(self):
        """
        Create a placeholder frame for every page.
        Each frame sits in the same grid cell — showing one hides the others.
        The real content for each page will be injected by menu_panel.py
        and the other UI modules in the next steps.
        """
        page_keys = [
            "create_order",
            "pizzas",
            "supplements",
            "history",
            "statistics",
        ]
        for key in page_keys:
            frame = ctk.CTkFrame(
                self.content_frame,
                corner_radius=0,
                fg_color=CONTENT_BG,
            )
            # All frames share the same grid cell
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_columnconfigure(0, weight=1)
            self.pages[key] = frame

        # ── Create Order: load the real MenuPanel ────────────────────────────
        self.menu_panel = MenuPanel(
            parent_frame = self.pages["create_order"],
            db           = self.db,
            order_screen = self,
        )
        self._bind_mousewheel(self.menu_panel.left_scroll)
        self._bind_mousewheel(self.menu_panel.cart_scroll)

        # ── History: load the real HistoryPanel ──────────────────────────────
        self.history_panel = HistoryPanel(
            parent_frame = self.pages["history"],
            db           = self.db,
            order_screen = self,
        )
        self._bind_mousewheel(self.history_panel.scroll)

        # ── Other pages: placeholders until their modules are built ──────────
        placeholder_text = {
            "pizzas":      "🍕  Pizza Manager — coming soon",
            "supplements": "🥗  Supplements Manager — coming soon",
            "statistics":  "📈  Statistics — coming soon",
        }
        for key, text in placeholder_text.items():
            ctk.CTkLabel(
                self.pages[key],
                text=text,
                font=ctk.CTkFont(size=16),
                text_color=TEXT_MUTED,
            ).grid(row=0, column=0)

    def _bind_mousewheel(self, scrollable_frame: ctk.CTkScrollableFrame):
        """
        Recursively bind mousewheel/touchpad scroll events to every widget
        inside a CTkScrollableFrame so scrolling works anywhere, not just
        on the scrollbar itself.
        Call this after building a panel, and again after any dynamic rebuild
        (e.g. after _refresh() repopulates cards).
        """
        canvas = scrollable_frame._parent_canvas

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_linux_scroll(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")

        def _bind_recursive(widget):
            widget.bind("<MouseWheel>", _on_mousewheel,   add="+")
            widget.bind("<Button-4>",   _on_linux_scroll, add="+")
            widget.bind("<Button-5>",   _on_linux_scroll, add="+")
            for child in widget.winfo_children():
                _bind_recursive(child)

        _bind_recursive(scrollable_frame)

    def _show_page(self, page_key: str):
        """
        Bring the requested page frame to the front.
        All other frames remain in the grid but are hidden behind it.
        """
        if page_key in self.pages:
            self.pages[page_key].tkraise()

    def get_page_frame(self, page_key: str) -> ctk.CTkFrame | None:
        """
        Return the frame for a given page key.
        Used by menu_panel.py and other modules to inject their content
        into the correct frame without needing access to the full layout.
        """
        return self.pages.get(page_key)