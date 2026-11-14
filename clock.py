import tkinter as tk
from datetime import datetime


class DigitalClock(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Digital Clock")
        self.configure(bg="#0b1020")
        self.resizable(False, False)

        container = tk.Frame(self, bg="#11182d", padx=40, pady=32)
        container.pack(padx=24, pady=24)

        tk.Label(
            container,
            text="LOCAL TIME",
            font=("Segoe UI", 10, "bold"),
            fg="#aab8e8",
            bg="#11182d",
        ).pack(pady=(0, 12))

        self.time_label = tk.Label(
            container,
            font=("Segoe UI", 48, "bold"),
            fg="#f4f7ff",
            bg="#11182d",
        )
        self.time_label.pack()

        self.date_label = tk.Label(
            container,
            font=("Segoe UI", 13),
            fg="#aab8e8",
            bg="#11182d",
        )
        self.date_label.pack(pady=(12, 0))

        self.update_clock()

    def update_clock(self):
        now = datetime.now()
        self.time_label.config(text=now.strftime("%H:%M:%S"))
        self.date_label.config(text=now.strftime("%A, %B %d, %Y"))
        self.after(1000, self.update_clock)


if __name__ == "__main__":
    DigitalClock().mainloop()