import tkinter as tk
from tkinter import ttk, messagebox
import time
from datetime import datetime, timedelta

try:
    import winsound  # Windows only
except ImportError:
    winsound = None


class DigitalClock(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Digital Clock")
        self.configure(bg="#0b1020")
        self.resizable(False, False)

        # Alarm state
        self.alarms = []          # list of dicts: {"time": "HH:MM", "label": str}
        self.fired = set()        # (date, "HH:MM") already rung, avoids repeat rings
        self.ring_window = None
        self.ringing = False

        # Stopwatch state
        self.sw_running = False
        self.sw_start = 0.0       # perf_counter value when last started
        self.sw_elapsed = 0.0     # seconds accumulated before last start
        self.sw_last_lap = 0.0    # total elapsed at previous lap
        self.sw_laps = 0

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

        self.build_tabs(container)
        self.update_clock()

    # ---------------------------------------------------------------- UI
    def build_tabs(self, parent):
        bg = "#11182d"
        tk.Frame(parent, bg="#26305a", height=1).pack(fill="x", pady=(22, 14))

        bar = tk.Frame(parent, bg=bg)
        bar.pack(pady=(0, 14))
        self.tab_buttons = {}
        for name in ("Alarm", "Stopwatch"):
            btn = tk.Button(
                bar, text=name, command=lambda n=name: self.show_tab(n),
                font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                cursor="hand2", padx=18, pady=6,
            )
            btn.pack(side="left", padx=3)
            self.tab_buttons[name] = btn

        body = tk.Frame(parent, bg=bg)
        body.pack()
        self.tabs = {
            "Alarm": tk.Frame(body, bg=bg),
            "Stopwatch": tk.Frame(body, bg=bg),
        }
        self.build_alarm_section(self.tabs["Alarm"])
        self.build_stopwatch_section(self.tabs["Stopwatch"])
        self.show_tab("Alarm")

    def show_tab(self, name):
        for n, frame in self.tabs.items():
            frame.pack_forget()
            active = n == name
            self.tab_buttons[n].config(
                bg="#4f6bff" if active else "#1b2447",
                fg="white" if active else "#aab8e8",
                activebackground="#6b83ff" if active else "#26305a",
                activeforeground="white",
            )
        self.tabs[name].pack()

    def build_stopwatch_section(self, parent):
        bg = "#11182d"

        tk.Label(
            parent, text="STOPWATCH", font=("Segoe UI", 10, "bold"),
            fg="#aab8e8", bg=bg,
        ).pack(pady=(0, 10))

        self.sw_label = tk.Label(
            parent, text=self.format_sw(0), font=("Consolas", 32, "bold"),
            fg="#f4f7ff", bg=bg,
        )
        self.sw_label.pack()

        btn_opts = dict(
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            padx=14, pady=6, bd=0, width=8,
        )
        btns = tk.Frame(parent, bg=bg)
        btns.pack(pady=14)
        self.sw_start_btn = tk.Button(
            btns, text="Start", command=self.sw_toggle,
            bg="#2ec27e", fg="white", activebackground="#46d68f",
            activeforeground="white", **btn_opts
        )
        self.sw_start_btn.pack(side="left", padx=4)
        tk.Button(
            btns, text="Lap", command=self.sw_lap,
            bg="#26305a", fg="#f4f7ff", activebackground="#33407a",
            activeforeground="#f4f7ff", **btn_opts
        ).pack(side="left", padx=4)
        tk.Button(
            btns, text="Reset", command=self.sw_reset,
            bg="#3a2540", fg="#ffb3c1", activebackground="#55304f",
            activeforeground="#ffb3c1", **btn_opts
        ).pack(side="left", padx=4)

        self.lap_list = tk.Listbox(
            parent, height=6, width=34, font=("Consolas", 11),
            bg="#1b2447", fg="#f4f7ff", selectbackground="#4f6bff",
            relief="flat", highlightthickness=0, activestyle="none",
        )
        self.lap_list.pack(pady=(4, 0))

    # --------------------------------------------------------- Stopwatch
    @staticmethod
    def format_sw(seconds):
        total_cs = int(seconds * 100)
        cs = total_cs % 100
        secs = (total_cs // 100) % 60
        mins = (total_cs // 6000) % 60
        hrs = total_cs // 360000
        return f"{hrs:02d}:{mins:02d}:{secs:02d}.{cs:02d}"

    def sw_current(self):
        if self.sw_running:
            return self.sw_elapsed + (time.perf_counter() - self.sw_start)
        return self.sw_elapsed

    def sw_toggle(self):
        if self.sw_running:
            self.sw_elapsed += time.perf_counter() - self.sw_start
            self.sw_running = False
            self.sw_start_btn.config(
                text="Start", bg="#2ec27e", activebackground="#46d68f"
            )
            self.sw_label.config(text=self.format_sw(self.sw_elapsed))
        else:
            self.sw_start = time.perf_counter()
            self.sw_running = True
            self.sw_start_btn.config(
                text="Stop", bg="#ff5d73", activebackground="#ff8093"
            )
            self.sw_tick()

    def sw_tick(self):
        if not self.sw_running:
            return
        self.sw_label.config(text=self.format_sw(self.sw_current()))
        self.after(30, self.sw_tick)

    def sw_lap(self):
        if not self.sw_running:
            return
        total = self.sw_current()
        split = total - self.sw_last_lap
        self.sw_last_lap = total
        self.sw_laps += 1
        self.lap_list.insert(
            0,
            f"#{self.sw_laps:<2} {self.format_sw(split)[3:]}  "
            f"total {self.format_sw(total)[3:]}",
        )

    def sw_reset(self):
        self.sw_running = False
        self.sw_elapsed = 0.0
        self.sw_last_lap = 0.0
        self.sw_laps = 0
        self.sw_start_btn.config(
            text="Start", bg="#2ec27e", activebackground="#46d68f"
        )
        self.sw_label.config(text=self.format_sw(0))
        self.lap_list.delete(0, tk.END)

    # ------------------------------------------------------------ Alarm UI
    def build_alarm_section(self, parent):
        bg = "#11182d"

        tk.Label(
            parent,
            text="SET ALARM",
            font=("Segoe UI", 10, "bold"),
            fg="#aab8e8",
            bg=bg,
        ).pack(pady=(0, 10))

        # Hour : Minute pickers
        picker = tk.Frame(parent, bg=bg)
        picker.pack()

        spin_opts = dict(
            width=3,
            font=("Segoe UI", 20, "bold"),
            justify="center",
            wrap=True,
            bg="#1b2447",
            fg="#f4f7ff",
            buttonbackground="#26305a",
            insertbackground="#f4f7ff",
            relief="flat",
        )

        self.hour_var = tk.StringVar(value="07")
        self.min_var = tk.StringVar(value="00")

        tk.Spinbox(
            picker, from_=0, to=23, textvariable=self.hour_var,
            format="%02.0f", **spin_opts
        ).pack(side="left")
        tk.Label(
            picker, text=":", font=("Segoe UI", 22, "bold"),
            fg="#f4f7ff", bg=bg
        ).pack(side="left", padx=6)
        tk.Spinbox(
            picker, from_=0, to=59, textvariable=self.min_var,
            format="%02.0f", **spin_opts
        ).pack(side="left")

        # Optional label
        label_row = tk.Frame(parent, bg=bg)
        label_row.pack(pady=(12, 0))
        tk.Label(
            label_row, text="Label:", font=("Segoe UI", 10),
            fg="#aab8e8", bg=bg
        ).pack(side="left", padx=(0, 6))
        self.label_var = tk.StringVar()
        tk.Entry(
            label_row, textvariable=self.label_var, width=22,
            font=("Segoe UI", 11), bg="#1b2447", fg="#f4f7ff",
            insertbackground="#f4f7ff", relief="flat"
        ).pack(side="left")

        # Buttons
        btn_opts = dict(
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            padx=14, pady=6, bd=0
        )
        btns = tk.Frame(parent, bg=bg)
        btns.pack(pady=14)
        tk.Button(
            btns, text="Add Alarm", command=self.add_alarm,
            bg="#4f6bff", fg="white", activebackground="#6b83ff",
            activeforeground="white", **btn_opts
        ).pack(side="left", padx=4)
        tk.Button(
            btns, text="Delete Selected", command=self.delete_alarm,
            bg="#3a2540", fg="#ffb3c1", activebackground="#55304f",
            activeforeground="#ffb3c1", **btn_opts
        ).pack(side="left", padx=4)

        # Alarm list
        self.alarm_list = tk.Listbox(
            parent, height=4, width=34, font=("Consolas", 12),
            bg="#1b2447", fg="#f4f7ff", selectbackground="#4f6bff",
            selectforeground="white", relief="flat", highlightthickness=0,
            activestyle="none",
        )
        self.alarm_list.pack(pady=(4, 0))

    # ------------------------------------------------------------ Alarms
    def add_alarm(self):
        try:
            h = int(self.hour_var.get())
            m = int(self.min_var.get())
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid time", "Enter hour 0-23 and minute 0-59.")
            return

        t = f"{h:02d}:{m:02d}"
        if any(a["time"] == t for a in self.alarms):
            messagebox.showinfo("Duplicate", f"An alarm for {t} already exists.")
            return

        self.alarms.append({"time": t, "label": self.label_var.get().strip()})
        self.alarms.sort(key=lambda a: a["time"])
        self.label_var.set("")
        self.refresh_alarm_list()

    def delete_alarm(self):
        sel = self.alarm_list.curselection()
        if not sel:
            messagebox.showinfo("Delete alarm", "Select an alarm in the list first.")
            return
        del self.alarms[sel[0]]
        self.refresh_alarm_list()

    def refresh_alarm_list(self):
        self.alarm_list.delete(0, tk.END)
        for a in self.alarms:
            text = f"⏰  {a['time']}"
            if a["label"]:
                text += f"   {a['label']}"
            self.alarm_list.insert(tk.END, text)

    def check_alarms(self, now):
        current = now.strftime("%H:%M")
        today = now.date()
        for a in self.alarms:
            key = (today, a["time"])
            if a["time"] == current and key not in self.fired:
                self.fired.add(key)
                self.trigger_alarm(a)
                break  # one popup at a time

        # keep the "fired" set small
        self.fired = {k for k in self.fired if k[0] == today}

    def trigger_alarm(self, alarm):
        if self.ringing:
            return
        self.ringing = True

        win = tk.Toplevel(self)
        self.ring_window = win
        win.title("Alarm")
        win.configure(bg="#11182d")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.protocol("WM_DELETE_WINDOW", lambda: self.stop_alarm(alarm))

        tk.Label(
            win, text="⏰  ALARM", font=("Segoe UI", 20, "bold"),
            fg="#ffd166", bg="#11182d"
        ).pack(padx=50, pady=(24, 4))
        tk.Label(
            win, text=alarm["time"], font=("Segoe UI", 36, "bold"),
            fg="#f4f7ff", bg="#11182d"
        ).pack()
        if alarm["label"]:
            tk.Label(
                win, text=alarm["label"], font=("Segoe UI", 13),
                fg="#aab8e8", bg="#11182d"
            ).pack(pady=(4, 0))

        row = tk.Frame(win, bg="#11182d")
        row.pack(pady=22)
        tk.Button(
            row, text="Snooze 5 min", command=lambda: self.snooze(alarm),
            font=("Segoe UI", 11, "bold"), bg="#26305a", fg="#f4f7ff",
            relief="flat", padx=14, pady=6, cursor="hand2"
        ).pack(side="left", padx=6)
        tk.Button(
            row, text="Stop", command=lambda: self.stop_alarm(alarm),
            font=("Segoe UI", 11, "bold"), bg="#ff5d73", fg="white",
            relief="flat", padx=22, pady=6, cursor="hand2"
        ).pack(side="left", padx=6)

        self.ring()

    def ring(self):
        """Beep repeatedly until the alarm window is closed."""
        if not self.ringing:
            return
        if winsound:
            winsound.Beep(1000, 400)
        else:
            self.bell()
        self.after(700, self.ring)

    def stop_alarm(self, alarm=None):
        self.ringing = False
        if self.ring_window is not None:
            self.ring_window.destroy()
            self.ring_window = None

    def snooze(self, alarm, minutes=5):
        self.stop_alarm()
        new_time = (datetime.now() + timedelta(minutes=minutes)).strftime("%H:%M")
        if not any(a["time"] == new_time for a in self.alarms):
            self.alarms.append(
                {"time": new_time, "label": alarm["label"] or "Snoozed"}
            )
            self.alarms.sort(key=lambda a: a["time"])
            self.refresh_alarm_list()

    # ------------------------------------------------------------- Clock
    def update_clock(self):
        now = datetime.now()
        self.time_label.config(text=now.strftime("%H:%M:%S"))
        self.date_label.config(text=now.strftime("%A, %B %d, %Y"))
        self.check_alarms(now)
        self.after(1000, self.update_clock)


if __name__ == "__main__":
    DigitalClock().mainloop()
