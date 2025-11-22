import os
import tkinter as tk
from tkinter import ttk, messagebox
import time
from typing import Dict, Optional, List
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates

from models import HostStats, PingSample
from settings import Settings
from ping_worker import HostManager
from host_input import parse_hosts

INTERVAL_PRESETS = [0.1, 0.2, 0.5, 1.0, 2.0]  # seconds
TIMEOUT_PRESETS_MS = [100, 200, 300, 500, 1000, 1500, 2000]

class MultiPingApp(tk.Tk):
    def __init__(self, settings: Settings, host_manager: HostManager, sample_queue):
        super().__init__()

        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))

            # Prefer .ico on Windows
            ico_path = os.path.join(base_dir, "zestyping.ico")
            png_path = os.path.join(base_dir, "zestyping.png")

            if os.path.exists(ico_path):
                # On Windows this often sets both titlebar and taskbar icon
                self.iconbitmap(default=ico_path)
            if os.path.exists(png_path):
                # Cross-platform nice-looking icon (e.g. Linux, some Windows themes)
                img = tk.PhotoImage(file=png_path)
                # keep a reference so it doesn't get GC'd
                self._icon_img = img
                self.iconphoto(False, img)
        except Exception as e:
            # Failing to set an icon shouldn’t kill the app
            print("Could not set window icon:", e)
            
        self.title("ZestyPing v0.2")
        self.geometry("1000x680")

        self.settings = settings
        self.host_manager = host_manager
        self.sample_queue = sample_queue

        self.stats: Dict[str, HostStats] = {}
        self.test_active = False
        self.summary_shown = False

        self._build_ui()
        self._load_from_settings()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._ui_timer()

    def _build_ui(self):
        ctrl = ttk.Frame(self)
        ctrl.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)

        # Interval dropdown + custom
        ttk.Label(ctrl, text="Interval:").grid(row=0, column=0, padx=(0, 4), sticky="w")
        self.interval_choice = tk.StringVar()
        interval_labels = [f"{v:.1f} s" for v in INTERVAL_PRESETS] + ["Custom…"]
        self.interval_combo = ttk.Combobox(
            ctrl,
            values=interval_labels,
            textvariable=self.interval_choice,
            state="readonly",
            width=10,
        )
        self.interval_combo.grid(row=0, column=1, sticky="w")
        self.interval_combo.bind("<<ComboboxSelected>>", lambda e: self._on_interval_choice())

        self.interval_custom_var = tk.StringVar()
        self.interval_custom_entry = ttk.Entry(ctrl, textvariable=self.interval_custom_var, width=8)
        ttk.Label(ctrl, text="(s)").grid(row=0, column=2, padx=(6, 0), sticky="w")
        self.interval_custom_entry.grid(row=0, column=3, sticky="w", padx=(2, 10))

        # Timeout dropdown + custom
        ttk.Label(ctrl, text="Timeout:").grid(row=0, column=4, padx=(10, 4), sticky="w")
        self.timeout_choice = tk.StringVar()
        timeout_labels = [f"{v} ms" for v in TIMEOUT_PRESETS_MS] + ["Custom…"]
        self.timeout_combo = ttk.Combobox(
            ctrl,
            values=timeout_labels,
            textvariable=self.timeout_choice,
            state="readonly",
            width=10,
        )
        self.timeout_combo.grid(row=0, column=5, sticky="w")
        self.timeout_combo.bind("<<ComboboxSelected>>", lambda e: self._on_timeout_choice())

        self.timeout_custom_var = tk.StringVar()
        self.timeout_custom_entry = ttk.Entry(ctrl, textvariable=self.timeout_custom_var, width=8)
        ttk.Label(ctrl, text="(ms)").grid(row=0, column=6, padx=(6, 0), sticky="w")
        self.timeout_custom_entry.grid(row=0, column=7, sticky="w", padx=(2, 10))

        # Count
        ttk.Label(ctrl, text="Count:").grid(row=0, column=8, padx=(6, 4), sticky="w")
        self.count_var = tk.StringVar(value=str(self.settings.count))
        ttk.Entry(ctrl, textvariable=self.count_var, width=8).grid(row=0, column=9, sticky="w")

        ttk.Button(ctrl, text="Start", command=self._start).grid(row=0, column=10, padx=(10, 4))
        ttk.Button(ctrl, text="Stop", command=self._stop).grid(row=0, column=11, padx=(4, 8))
        ttk.Button(ctrl, text="Save Settings", command=self._save_settings).grid(row=0, column=12, padx=(4, 8))

        hosts_frame = ttk.LabelFrame(self, text="Hosts")
        hosts_frame.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=6)
        self.host_list = tk.Listbox(hosts_frame, height=20, selectmode=tk.EXTENDED)
        self.host_list.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6, pady=6)

        add_frame = ttk.Frame(hosts_frame)
        add_frame.pack(side=tk.TOP, fill=tk.X, padx=6, pady=(0, 6))

        self.new_host_var = tk.StringVar()
        self.new_desc_var = tk.StringVar()

        # Host entry
        ttk.Entry(add_frame, textvariable=self.new_host_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

        # Description (max ~20 chars)
        ttk.Label(add_frame, text="Desc:").pack(side=tk.LEFT, padx=(4, 2))
        ttk.Entry(add_frame, textvariable=self.new_desc_var, width=20).pack(side=tk.LEFT)

        ttk.Button(add_frame, text="Add", command=self._add_host).pack(side=tk.LEFT, padx=4)
        ttk.Button(add_frame, text="Remove Selected", command=self._remove_selected).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(add_frame, text="Bulk Add…", command=self._bulk_add_dialog).pack(
            side=tk.LEFT, padx=4
        )


        right = ttk.Frame(self)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=6)

        table_frame = ttk.LabelFrame(right, text="Summary (Live)")
        table_frame.pack(side=tk.TOP, fill=tk.X)
        cols = ("Host", "Desc", "IP", "Last", "Min", "Avg", "Max", "Loss%", "Recv", "Sent", "LastSeen")
        self.table = ttk.Treeview(table_frame, columns=cols, show="headings", height=10)
        for c in cols:
            self.table.heading(c, text=c)
            self.table.column(c, width=95 if c not in ("Host", "IP") else 150, anchor=tk.CENTER)
        self.table.pack(fill=tk.X)

        plot_frame = ttk.LabelFrame(right, text="Live Latency (ms)")
        plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(6, 0))
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Time (HH:MM:SS)")
        self.ax.set_ylabel("Latency (ms)")
        self.ax.grid(True, alpha=0.3)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # initialize dropdowns from settings
        self._init_interval_controls()
        self._init_timeout_controls()

    # ---- dropdown helpers ----
    def _init_interval_controls(self):
        s = round(float(self.settings.interval_s), 3)
        if s in INTERVAL_PRESETS:
            self.interval_choice.set(f"{s:.1f} s")
            self.interval_custom_entry.configure(state="disabled")
            self.interval_custom_var.set("")
        else:
            self.interval_choice.set("Custom…")
            self.interval_custom_entry.configure(state="normal")
            self.interval_custom_var.set(str(s))

    def _init_timeout_controls(self):
        ms = int(self.settings.timeout_ms)
        if ms in TIMEOUT_PRESETS_MS:
            self.timeout_choice.set(f"{ms} ms")
            self.timeout_custom_entry.configure(state="disabled")
            self.timeout_custom_var.set("")
        else:
            self.timeout_choice.set("Custom…")
            self.timeout_custom_entry.configure(state="normal")
            self.timeout_custom_var.set(str(ms))

    def _on_interval_choice(self):
        if self.interval_choice.get() == "Custom…":
            self.interval_custom_entry.configure(state="normal")
            if not self.interval_custom_var.get():
                self.interval_custom_var.set(str(self.settings.interval_s))
        else:
            self.interval_custom_entry.configure(state="disabled")
            self.interval_custom_var.set("")

    def _on_timeout_choice(self):
        if self.timeout_choice.get() == "Custom…":
            self.timeout_custom_entry.configure(state="normal")
            if not self.timeout_custom_var.get():
                self.timeout_custom_var.set(str(self.settings.timeout_ms))
        else:
            self.timeout_custom_entry.configure(state="disabled")
            self.timeout_custom_var.set("")

    def _get_interval_seconds(self) -> float:
        if self.interval_choice.get() == "Custom…":
            return float(self.interval_custom_var.get())
        label = self.interval_choice.get().split()[0]
        return float(label)

    def _get_timeout_ms(self) -> int:
        if self.timeout_choice.get() == "Custom…":
            return int(float(self.timeout_custom_var.get()))
        label = self.timeout_choice.get().split()[0]
        return int(float(label))

    def _load_from_settings(self):
        self.host_list.delete(0, tk.END)
        for h in self.settings.hosts:
            self.host_list.insert(tk.END, h)
            desc = self.settings.host_descriptions.get(h, "")
            st = HostStats(host=h, count=self.settings.count, description=desc)
            self.stats[h] = st

    # ----- host list ops -----
    def _add_host(self):
        h = self.new_host_var.get().strip()
        if not h:
            return
        if h in self.stats:
            messagebox.showinfo("Host exists", f"{h} already in list.")
            return

        # Clamp description to 20 chars (or whatever you want)
        desc_raw = self.new_desc_var.get().strip()
        desc = desc_raw[:20]

        self.host_list.insert(tk.END, h)
        self.stats[h] = HostStats(
            host=h,
            count=int(self.count_var.get() or 60),
            description=desc,
        )

        # Clear inputs
        self.new_host_var.set("")
        self.new_desc_var.set("")

    def _remove_selected(self):
        sel = list(self.host_list.curselection())
        if not sel:
            return
        sel_hosts = [self.host_list.get(i) for i in sel]
        for h in sel_hosts:
            self.host_manager.stop_host(h)
            if h in self.stats:
                del self.stats[h]
        for i in reversed(sel):
            self.host_list.delete(i)
        self._refresh_table()
        self._refresh_plot()

    def _bulk_add_dialog(self):
        win = tk.Toplevel(self)
        win.title("Bulk Add Hosts")
        win.geometry("650x420")
        ttk.Label(
            win,
            text="Paste hosts, CIDR blocks, or ranges (comma/space/newline separated).",
        ).pack(anchor="w", padx=8, pady=(8, 4))
        examples = (
            "Examples:\n"
            "10.0.0.1 10.0.0.2,10.0.0.3\n"
            "10.0.0.10-10.0.0.20   (full range)\n"
            "10.0.0.10-20          (last octet)\n"
            "10.0.0.[5-15]         (brackets)\n"
            "10.0.1.0/29           (CIDR; hosts only)\n"
            "switch-a.lan core-sw1"
        )
        ttk.Label(win, text=examples, justify="left").pack(anchor="w", padx=8, pady=(0, 6))
        txt = tk.Text(win, height=12, wrap="word")
        txt.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        status = tk.StringVar(value="")
        ttk.Label(win, textvariable=status).pack(anchor="w", padx=8, pady=(0, 6))
        btns = ttk.Frame(win)
        btns.pack(fill=tk.X, padx=8, pady=(0, 8))

        def do_add():
            hosts = parse_hosts(txt.get("1.0", tk.END), limit=10000)
            already = set(self.stats.keys())
            added = 0
            for h in hosts:
                if h not in already:
                    self.host_list.insert(tk.END, h)
                    self.stats[h] = HostStats(host=h, count=int(self.count_var.get() or 60))
                    already.add(h)
                    added += 1
            status.set(
                f"Parsed {len(hosts)} host(s). Added {added}, {len(hosts) - added} skipped (duplicates)."
            )
            self._refresh_table()

        ttk.Button(btns, text="Add Hosts", command=do_add).pack(side=tk.LEFT)
        ttk.Button(btns, text="Close", command=win.destroy).pack(side=tk.RIGHT)

    # ----- start/stop -----
    def _start(self):
        try:
            interval_s = float(self._get_interval_seconds())
            timeout_ms = int(self._get_timeout_ms())
            count = int(self.count_var.get())
            if interval_s <= 0:
                raise ValueError("Interval must be > 0")
            if timeout_ms <= 0:
                raise ValueError("Timeout must be > 0")
            if count <= 0:
                raise ValueError("Count must be > 0")
            for h in [self.host_list.get(i) for i in range(self.host_list.size())]:
                if h not in self.stats:
                    self.stats[h] = HostStats(host=h, count=count)
                else:
                    self.stats[h].set_count(count)
                    self.stats[h].reset()
        except Exception as e:
            messagebox.showerror("Invalid settings", str(e))
            return

        hosts = [self.host_list.get(i) for i in range(self.host_list.size())]
        if not hosts:
            messagebox.showinfo("No hosts", "Add at least one host first.")
            return

        self.summary_shown = False
        self.test_active = True
        for h in hosts:
            self.host_manager.start_host(
                h,
                interval_s=interval_s,
                timeout_ms=timeout_ms,
                max_count=count,
            )

    def _stop(self):
        self.host_manager.stop_all()
        if self.test_active:
            self.test_active = False
            self._show_summary()

    def _save_settings(self):
        try:
            self.settings.interval_s = float(self._get_interval_seconds())
            self.settings.timeout_ms = int(self._get_timeout_ms())
            self.settings.count = int(self.count_var.get())

            # Hosts in the listbox
            hosts = [self.host_list.get(i) for i in range(self.host_list.size())]
            self.settings.hosts = hosts

            # Build description map from stats
            desc_map = {}
            for h in hosts:
                st = self.stats.get(h)
                desc_map[h] = (st.description if st else "")
            self.settings.host_descriptions = desc_map

            self.settings.save()
            messagebox.showinfo("Saved", "Settings saved to config.json")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

    # ----- UI refresh loop -----
    def _ui_timer(self):
        while True:
            try:
                s: PingSample = self.sample_queue.get_nowait()
                if s.host not in self.stats:
                    self.stats[s.host] = HostStats(host=s.host, count=int(self.count_var.get() or 60))
                    self.host_list.insert(tk.END, s.host)
                self.stats[s.host].add(s)
            except Exception:
                break
        self.host_manager.cleanup_finished()
        if self.test_active and not self.host_manager.running_hosts() and not self.summary_shown:
            self.test_active = False
            self._show_summary()
        self._refresh_table()
        self._refresh_plot()
        self.after(500, self._ui_timer)

    def _refresh_table(self):
        for r in self.table.get_children():
            self.table.delete(r)
        for h, st in sorted(self.stats.items(), key=lambda kv: kv[0].lower()):
            last = st.last()
            ip = last.ip if last else ""
            sent, recv, loss = st.counts()
            mn, avg, mx = st.latency_stats()
            last_ms = last.latency_ms if last and last.success else None
            last_seen = time.strftime("%H:%M:%S", time.localtime(last.ts)) if last else ""
            desc = st.description or ""

            def fmt(v):
                return "" if v is None else str(v)

            self.table.insert(
                "",
                tk.END,
                values=(
                    h,
                    desc,
                    ip,
                    fmt(last_ms),
                    fmt(mn),
                    fmt(avg),
                    fmt(mx),
                    f"{loss}",
                    f"{recv}",
                    f"{sent}",
                    last_seen,
                ),
            )

    def _refresh_plot(self):
        from datetime import datetime

        # Clear and reconfigure axes for time-of-day X axis
        self.ax.cla()
        self.ax.set_xlabel("Time (HH:MM:SS)")
        self.ax.set_ylabel("Latency (ms)")
        self.ax.grid(True, alpha=0.3)
        # Format ticks as clock time
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))

        have_data = False
        for h, st in sorted(self.stats.items(), key=lambda kv: kv[0].lower()):
            xs, ys = st.series()
            if not xs:
                continue

            # Convert epoch timestamps to matplotlib datetimes
            x_dates = [mdates.date2num(datetime.fromtimestamp(t)) for t in xs]

            self.ax.plot(x_dates, ys, label=h, linewidth=1.5)
            have_data = True

        if have_data:
            self.ax.legend(loc="upper right", fontsize=8)
            self.fig.autofmt_xdate()

        self.canvas.draw_idle()

    def _show_summary(self):
        self.summary_shown = True
        rows: List[tuple] = []

        for h, st in sorted(self.stats.items(), key=lambda kv: kv[0].lower()):
            sent, recv, loss = st.counts()
            mn, avg, mx = st.latency_stats()
            last = st.last()
            ip = last.ip if last else ""
            desc = st.description or ""
            mn, avg, mx = st.latency_stats()
            mean_sd, stdev = st.latency_sigma()  # <-- NEW

            rows.append(
                (h, desc, ip, sent, recv, loss, mn, avg, mx, stdev)
            )

        win = tk.Toplevel(self)
        win.title("Run Summary")
        win.geometry("900x460")

        cols = ("Host", "Desc", "IP", "Sent", "Recv", "Loss%", "Min", "Avg", "Max", "StDev")

        tree = ttk.Treeview(win, columns=cols, show="headings")
        for c in cols:
            width = 95
            if c in ("Host", "IP"):
                width = 140
            if c == "Desc":
                width = 140
            tree.heading(c, text=c)
            tree.column(c, width=width, anchor=tk.CENTER)
        tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        def fmt(v):
            return "" if v is None else str(v)

        for (h, desc, ip, sent, recv, loss, mn, avg, mx, stdev) in rows:
            tree.insert(
        "",
        tk.END,
        values=(
            h,
            desc,
            ip,
            sent,
            recv,
            loss,
            fmt(mn),
            fmt(avg),
            fmt(mx),
            fmt(round(stdev, 2) if stdev is not None else "")
        ),
    )


        btns = ttk.Frame(win)
        btns.pack(fill=tk.X, padx=8, pady=(0, 8))

        def copy_to_clipboard():
            header = "\t".join(cols)
            tsv_rows = [header] + [
            "\t".join(
                [
                    str(h),
                    str(desc),
                    str(ip),
                    str(sent),
                    str(recv),
                    str(loss),
                    fmt(mn),
                    fmt(avg),
                    fmt(mx),
                    fmt(round(stdev, 2) if stdev is not None else "")
                ]
            )
            for (h, desc, ip, sent, recv, loss, mn, avg, mx, stdev) in rows
        ]

            self.clipboard_clear()
            self.clipboard_append("\n".join(tsv_rows))
            self.update()
            messagebox.showinfo("Copied", "Summary copied to clipboard as TSV.")

        ttk.Button(btns, text="Copy TSV", command=copy_to_clipboard).pack(side=tk.LEFT)
        ttk.Button(btns, text="Close", command=win.destroy).pack(side=tk.RIGHT)

    def _on_close(self):
        try:
            self.host_manager.stop_all()
        finally:
            self.destroy()
