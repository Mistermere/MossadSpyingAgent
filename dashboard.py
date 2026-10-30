import customtkinter as ctk
import sqlite3
import os
from datetime import datetime, timedelta

# --- SETUP ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# --- DATABASE PATH ---
DB_PATH = os.path.join(os.path.expanduser("~"), "tabwise_usage.db")

# --- DATABASE FUNCTIONS ---
def get_total_time():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(duration_seconds) FROM app_usage")
    total = cursor.fetchone()[0] or 0
    conn.close()
    return total

def get_today_time():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Gets time only for today's date (resets at midnight)
    cursor.execute("SELECT SUM(duration_seconds) FROM app_usage WHERE substr(start_time, 1, 10) = date('now')")
    total = cursor.fetchone()[0] or 0
    conn.close()
    return total

def get_weekly_time():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Gets time for the last 7 days
    cursor.execute("SELECT SUM(duration_seconds) FROM app_usage WHERE substr(start_time, 1, 10) >= date('now', '-7 days')")
    total = cursor.fetchone()[0] or 0
    conn.close()
    return total

def get_monthly_time():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Gets time for the current calendar month
    cursor.execute("SELECT SUM(duration_seconds) FROM app_usage WHERE substr(start_time, 1, 7) = strftime('%Y-%m', 'now')")
    total = cursor.fetchone()[0] or 0
    conn.close()
    return total

def get_top_apps():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT window_title, SUM(duration_seconds) as total_seconds 
        FROM app_usage 
        GROUP BY window_title 
        ORDER BY total_seconds DESC
        LIMIT 6
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_daily_time():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT substr(start_time, 1, 10) as day, SUM(duration_seconds) 
        FROM app_usage 
        GROUP BY day
    ''')
    rows = cursor.fetchall()
    conn.close()
    return dict(rows)

def get_progression_stats():
    daily_data = get_daily_time()
    total_days = len(daily_data)
    productive_days = sum(1 for time in daily_data.values() if time >= 14400)
    return total_days, productive_days

def format_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

# --- UI APPLICATION ---
class Dashboard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Tabwise Tracker")
        self.geometry("1050x750")
        self.configure(fg_color="#0f0f13")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.rectangles = {}

        self.create_sidebar()
        self.create_main_content()

        self.bind("<FocusIn>", self.on_window_focus)

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#141419")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        logo = ctk.CTkLabel(self.sidebar, text="tabwise", font=("Segoe UI", 24, "bold"), text_color="#a855f7")
        logo.pack(pady=30, padx=20, anchor="w")

        self.create_sidebar_btn("Overview", True)
        self.create_sidebar_btn("Activity", False)
        self.create_sidebar_btn("Websites", False)

    def create_sidebar_btn(self, text, active):
        color = "#a855f7" if active else "#6b7280"
        bg = "#1f1f27" if active else "transparent"
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color=bg, text_color=color, anchor="w", font=("Segoe UI", 14))
        btn.pack(fill="x", padx=10, pady=5)

    def create_main_content(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)

        # --- TOP HEADER ROW ---
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        header = ctk.CTkLabel(header_frame, text="A little clarity for your day.", font=("Segoe UI", 28, "bold"), text_color="white")
        header.pack(side="left")

        refresh_btn = ctk.CTkButton(header_frame, text="↻ Refresh", font=("Segoe UI", 12), fg_color="#1f1f27", text_color="#a855f7", width=80, command=self.manual_refresh)
        refresh_btn.pack(side="right", padx=(10, 0))

        perseverence_label = ctk.CTkLabel(header_frame, text="Perseverence", font=("Segoe UI", 14, "bold"), text_color="#9ca3af")
        perseverence_label.pack(side="right")

        # --- TOP CARDS ---
        self.cards_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.cards_frame.pack(fill="x", pady=10)

        self.card_browser_val = self.create_card(self.cards_frame, "Browser time today", "0m")
        self.card_weekly_val = self.create_card(self.cards_frame, "Weekly time", "0h 0m")
        self.card_monthly_val = self.create_card(self.cards_frame, "Monthly time", "0h 0m")
        self.card_total_val = self.create_card(self.cards_frame, "Total time", "0m")

        # --- BOTTOM SPLIT ---
        self.bottom_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.bottom_frame.pack(fill="both", expand=True, pady=20)
        
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=1)

        # Left side: List
        self.list_frame = ctk.CTkFrame(self.bottom_frame, fg_color="#141419", corner_radius=15, border_width=1, border_color="#2d2d3d")
        self.list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self.list_title = ctk.CTkLabel(self.list_frame, text="Time by website", font=("Segoe UI", 18, "bold"), text_color="white")
        self.list_title.pack(anchor="w", padx=20, pady=15)

        self.list_items_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        self.list_items_frame.pack(fill="x", padx=20)

        # Right side: Progression Grid
        self.prog_frame = ctk.CTkFrame(self.bottom_frame, fg_color="#141419", corner_radius=15, border_width=1, border_color="#2d2d3d")
        self.prog_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        prog_title = ctk.CTkLabel(self.prog_frame, text="Progression level", font=("Segoe UI", 22, "bold"), text_color="white")
        prog_title.pack(anchor="w", padx=20, pady=(15, 5))
        
        desc = ctk.CTkLabel(self.prog_frame, text="Success begins the moment you decide not to give up", font=("Segoe UI", 12), text_color="#6b7280")
        desc.pack(anchor="w", padx=20, pady=(0, 20))

        self.grid_and_stats_frame = ctk.CTkFrame(self.prog_frame, fg_color="transparent")
        self.grid_and_stats_frame.pack(fill="x", padx=20, pady=10)
        
        # --- Left Side: Canvas & Tooltip ---
        self.left_grid_frame = ctk.CTkFrame(self.grid_and_stats_frame, fg_color="transparent")
        self.left_grid_frame.pack(side="left", fill="y")

        self.grid_canvas = ctk.CTkCanvas(self.left_grid_frame, width=340, height=130, bg="#141419", highlightthickness=0)
        self.grid_canvas.pack(anchor="w")
        
        self.tooltip_label = ctk.CTkLabel(self.left_grid_frame, text="Hover over a box to see details", font=("Segoe UI", 12, "bold"), text_color="#6b7280")
        self.tooltip_label.pack(anchor="w", pady=(10, 0))

        # --- Right Side: Stats ---
        self.right_stats_frame = ctk.CTkFrame(self.grid_and_stats_frame, fg_color="transparent", width=250, height=130)
        self.right_stats_frame.pack(side="left", fill="y", padx=(20, 0))
        self.right_stats_frame.pack_propagate(False)

        self.create_progression_stats()
        self.update_grid_and_stats()
        self.update_list()

    def create_progression_stats(self):
        # --- CURRENT (Pinned to Top) ---
        curr_title = ctk.CTkLabel(self.right_stats_frame, text="Current", font=("Segoe UI", 18, "bold"), text_color="#e5e7eb")
        curr_title.place(x=0, y=0, anchor="nw")
        
        self.curr_value_label = ctk.CTkLabel(self.right_stats_frame, text="0", font=("Segoe UI", 26, "bold"), text_color="#ec4899")
        self.curr_value_label.place(relx=1.0, x=-10, y=0, anchor="ne")
        
        curr_desc = ctk.CTkLabel(self.right_stats_frame, text="Days over 4 hours", font=("Segoe UI", 11), text_color="#6b7280")
        curr_desc.place(x=0, y=28, anchor="nw")

        # --- ESTIMATED (Pinned to Bottom) ---
        est_title = ctk.CTkLabel(self.right_stats_frame, text="Estimated", font=("Segoe UI", 18, "bold"), text_color="#e5e7eb")
        est_title.place(x=0, rely=1.0, y=-20, anchor="sw")
        
        self.est_value_label = ctk.CTkLabel(self.right_stats_frame, text="0", font=("Segoe UI", 26, "bold"), text_color="#a855f7")
        self.est_value_label.place(relx=1.0, x=-10, rely=1.0, y=-20, anchor="se")
        
        est_desc = ctk.CTkLabel(self.right_stats_frame, text="Total days tracked", font=("Segoe UI", 11), text_color="#6b7280")
        est_desc.place(x=0, rely=1.0, y=0, anchor="sw")

    def on_window_focus(self, event):
        self.update_grid_and_stats()
        self.update_list()

    def manual_refresh(self):
        self.update_grid_and_stats()
        self.update_list()

    def create_card(self, parent, title, value):
        card = ctk.CTkFrame(parent, fg_color="#141419", corner_radius=15, border_width=1, border_color="#2d2d3d", width=180, height=100)
        card.pack(side="left", expand=True, fill="x", padx=5)
        
        lbl_title = ctk.CTkLabel(card, text=title, font=("Segoe UI", 12), text_color="#9ca3af")
        lbl_title.pack(anchor="w", padx=15, pady=(4, 0))
        
        lbl_value = ctk.CTkLabel(card, text=value, font=("Segoe UI", 22, "bold"), text_color="white")
        lbl_value.pack(anchor="w", padx=15, pady=(0, 10))
        return lbl_value

    def update_list(self):
        for widget in self.list_items_frame.winfo_children():
            widget.destroy()

        apps = get_top_apps()
        for app in apps:
            self.create_list_item(app[0], format_time(app[1]))

    def create_list_item(self, name, time_str):
        item_frame = ctk.CTkFrame(self.list_items_frame, fg_color="transparent")
        item_frame.pack(fill="x", pady=3) 
        
        display_name = name if name else "Unknown"
        if len(display_name) > 30:
            display_name = display_name[:27] + "..."
            
        lbl_name = ctk.CTkLabel(item_frame, text=display_name, font=("Segoe UI", 12), text_color="white")
        lbl_name.pack(side="left")
        
        lbl_time = ctk.CTkLabel(item_frame, text=time_str, font=("Segoe UI", 12, "bold"), text_color="#a855f7")
        lbl_time.pack(side="right")

    def update_grid_and_stats(self):
        today_sec = get_today_time()
        weekly_sec = get_weekly_time()
        monthly_sec = get_monthly_time()
        total_sec = get_total_time()
        
        # Updates the top cards
        self.card_browser_val.configure(text=format_time(today_sec))
        self.card_weekly_val.configure(text=format_time(weekly_sec))
        self.card_monthly_val.configure(text=format_time(monthly_sec))
        self.card_total_val.configure(text=format_time(total_sec))

        total_days, productive_days = get_progression_stats()
        self.curr_value_label.configure(text=str(productive_days))
        self.est_value_label.configure(text=str(total_days))

        self.grid_canvas.delete("all")
        self.rectangles = {}
        
        daily_data = get_daily_time()
        
        rows = 7
        cols = 16
        box_size = 14
        spacing = 6
        MAX_GOAL = 7200 
        
        today = datetime.now().date()
        start_date = today - timedelta(days=(rows * cols) - 1)

        for row in range(rows):
            for col in range(cols):
                current_date = start_date + timedelta(days=(row * cols + col))
                date_str = current_date.strftime('%Y-%m-%d')
                
                seconds_spent = daily_data.get(date_str, 0)
                color = self.get_color_for_time(seconds_spent, MAX_GOAL)
                
                x1 = col * (box_size + spacing)
                y1 = row * (box_size + spacing)
                x2 = x1 + box_size
                y2 = y1 + box_size
                
                rect_id = self.grid_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
                
                self.rectangles[rect_id] = {
                    "date": current_date.strftime('%B %d, %Y'),
                    "time": format_time(seconds_spent),
                    "original_color": color
                }
                
                self.grid_canvas.tag_bind(rect_id, "<Enter>", lambda event, r_id=rect_id: self.on_hover(event, r_id))
                self.grid_canvas.tag_bind(rect_id, "<Leave>", lambda event, r_id=rect_id: self.on_leave(event, r_id))

    def on_hover(self, event, rect_id):
        if rect_id in self.rectangles:
            data = self.rectangles[rect_id]
            self.tooltip_label.configure(text=f"{data['date']} — {data['time']}", text_color="white")
            self.grid_canvas.itemconfig(rect_id, outline="white", width=2)

    def on_leave(self, event, rect_id):
        self.tooltip_label.configure(text="Hover over a box to see details", text_color="#6b7280")
        self.grid_canvas.itemconfig(rect_id, outline="")

    def get_color_for_time(self, seconds, max_goal):
        if seconds == 0:
            return "#2d2d3d"
            
        percentage = min(seconds / max_goal, 1.0)
        
        if percentage < 0.25:
            return "#4c1d95"
        elif percentage < 0.50:
            return "#7e22ce"
        elif percentage < 0.75:
            return "#a855f7"
        elif percentage < 1.00:
            return "#d946ef"
        else:
            return "#ec4899"

if __name__ == "__main__":
    app = Dashboard()
    app.mainloop()