import customtkinter as ctk
from db.database import Database
from ui.order_screen import OrderScreen


def main():
    # ── Appearance ──────────────────────────────────────────────────────────
    # Set the theme and color before any window is created
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")   # we override colors in our widgets anyway

    # ── Database ─────────────────────────────────────────────────────────────
    # Initialize once here and pass it down to every screen that needs it.
    # This way there is always a single connection for the whole app lifetime.
    db = Database()

    # ── Main window ──────────────────────────────────────────────────────────
    root = ctk.CTk()
    root.title("Pizza House — Reception")
    root.geometry("1100x650")      # comfortable default size
    root.minsize(900, 580)         # prevent the window from getting too small

    # Center the window on the screen when the app opens
    root.update_idletasks()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = (screen_w // 2) - (1100 // 2)
    y = (screen_h // 2) - (650 // 2)
    root.geometry(f"1100x650+{x}+{y}")

    # ── Load main screen ─────────────────────────────────────────────────────
    # OrderScreen takes the root window and the database.
    # It builds the full UI (sidebar + topbar + content area) inside root.
    app = OrderScreen(root, db)

    # ── Shutdown hook ────────────────────────────────────────────────────────
    # Close the database connection cleanly when the window is closed.
    def on_close():
        db.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    # ── Start ────────────────────────────────────────────────────────────────
    root.mainloop()


if __name__ == "__main__":
    main()