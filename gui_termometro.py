"""
GUI stile LCD per Xiaomi Mijia Thermometer 2 (LYWSD03MMC / NUN4126GL).

Aggiornamento:
  - a richiesta (pulsante Aggiorna)
  - oppure automatico a intervallo lungo (default 10 min), per non scaricare la batteria

Modalità compatta:
  - mostra solo il rettangolo LCD
  - trascinabile; doppio click, click destro o Esc per espandere di nuovo

Avvio:
  python gui_termometro.py
"""

from __future__ import annotations

import asyncio
import threading
import tkinter as tk
from tkinter import ttk
from typing import Callable

from mijia_ble import (
    DeviceInfo,
    Reading,
    read_once,
    rssi_bars,
    rssi_label,
    scan_devices,
)

BG_APP = "#E8E6E1"
FRAME_PLASTIC = "#F4F2ED"
FRAME_EDGE = "#C9C5BC"
LCD_BG = "#C8D2B8"
LCD_DIM = "#A8B498"
LCD_INK = "#1A2214"
LCD_FAINT = "#9AAB88"
STATUS_FG = "#5A5A52"


class BleWorker:
    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._busy = False
        self._thread.start()

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    @property
    def busy(self) -> bool:
        return self._busy

    def submit(self, coro, on_ok: Callable, on_err: Callable) -> None:
        if self._busy:
            on_err(RuntimeError("Operazione BLE già in corso"))
            return

        self._busy = True

        async def wrapped():
            try:
                return await coro
            finally:
                self._busy = False

        fut = asyncio.run_coroutine_threadsafe(wrapped(), self._loop)

        def done(f):
            try:
                on_ok(f.result())
            except Exception as exc:  # noqa: BLE001
                on_err(exc)

        fut.add_done_callback(done)

    def shutdown(self) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)


class LcdDisplay(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            width=280,
            height=200,
            highlightthickness=0,
            bg=FRAME_PLASTIC,
            **kwargs,
        )
        self._reading: Reading | None = None
        self._connecting = False
        self._rssi: int | None = None
        self._draw_chrome()
        self.show_placeholder()

    def _draw_chrome(self) -> None:
        self.create_rectangle(8, 8, 272, 192, fill=FRAME_PLASTIC, outline=FRAME_EDGE, width=2)
        self.create_rectangle(28, 28, 252, 172, fill=LCD_BG, outline=LCD_DIM, width=2)
        self.create_rectangle(34, 34, 246, 166, fill=LCD_BG, outline=LCD_FAINT, width=1)

    def show_placeholder(self) -> None:
        self._reading = None
        self._connecting = False
        self._redraw()

    def show_connecting(self) -> None:
        self._connecting = True
        self._redraw()

    def show_reading(self, reading: Reading, rssi: int | None = None) -> None:
        self._reading = reading
        self._connecting = False
        if rssi is not None:
            self._rssi = rssi
        self._redraw()

    def set_rssi(self, rssi: int | None) -> None:
        self._rssi = rssi
        self._redraw()

    def _redraw(self) -> None:
        self.delete("content")
        self.create_rectangle(35, 35, 245, 165, fill=LCD_BG, outline="", tags="content")
        self._draw_signal_bars(self._rssi)

        if self._connecting:
            self.create_text(
                140, 90, text="···", fill=LCD_INK, font=("Consolas", 42, "bold"), tags="content"
            )
            self.create_text(
                140, 140, text="BLE", fill=LCD_INK, font=("Segoe UI", 11), tags="content"
            )
            return

        if self._reading is None:
            self.create_text(
                140, 88, text="--.-", fill=LCD_FAINT, font=("Consolas", 48, "bold"), tags="content"
            )
            self.create_text(
                215, 78, text="°C", fill=LCD_FAINT, font=("Segoe UI", 14, "bold"), tags="content"
            )
            self.create_text(
                70, 145, text="--%", fill=LCD_FAINT, font=("Consolas", 20, "bold"), tags="content"
            )
            self._draw_face("neutral", faint=True)
            return

        r = self._reading
        temp_txt = f"{r.temperature:4.1f}".replace(" ", "")
        self.create_text(
            128, 88, text=temp_txt, fill=LCD_INK, font=("Consolas", 48, "bold"), tags="content"
        )
        self.create_text(
            220, 72, text="°C", fill=LCD_INK, font=("Segoe UI", 14, "bold"), tags="content"
        )
        self.create_text(
            228, 48, text="⌁", fill=LCD_INK, font=("Segoe UI", 12), tags="content"
        )
        self.create_text(
            72,
            145,
            text=f"{r.humidity:2d}%",
            fill=LCD_INK,
            font=("Consolas", 22, "bold"),
            tags="content",
        )
        self._draw_face(r.comfort_face())

    def _draw_signal_bars(self, rssi: int | None) -> None:
        levels = 0
        faint = True
        if rssi is not None:
            faint = False
            if rssi >= -55:
                levels = 4
            elif rssi >= -65:
                levels = 3
            elif rssi >= -75:
                levels = 2
            elif rssi >= -85:
                levels = 1
        x0, y0 = 48, 52
        for i in range(4):
            h = 4 + i * 3
            x = x0 + i * 6
            color = LCD_INK if (not faint and i < levels) else LCD_FAINT
            self.create_rectangle(x, y0 - h, x + 4, y0, fill=color, outline="", tags="content")

    def _draw_face(self, mood: str, faint: bool = False) -> None:
        color = LCD_FAINT if faint else LCD_INK
        cx, cy, r = 200, 140, 16
        self.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=2, tags="content")
        self.create_oval(cx - 6, cy - 5, cx - 3, cy - 2, fill=color, outline="", tags="content")
        self.create_oval(cx + 3, cy - 5, cx + 6, cy - 2, fill=color, outline="", tags="content")
        if mood == "happy":
            self.create_arc(
                cx - 8, cy - 2, cx + 8, cy + 10,
                start=200, extent=140, style=tk.ARC, outline=color, width=2, tags="content",
            )
        elif mood == "sad":
            self.create_arc(
                cx - 8, cy + 4, cx + 8, cy + 16,
                start=20, extent=140, style=tk.ARC, outline=color, width=2, tags="content",
            )
        else:
            self.create_line(cx - 6, cy + 6, cx + 6, cy + 6, fill=color, width=2, tags="content")


class ThermometerApp(tk.Tk):
    DEFAULT_INTERVAL_MIN = 10

    def __init__(self) -> None:
        super().__init__()
        self.title("Termometro Xiaomi")
        self.configure(bg=BG_APP)
        self.resizable(False, False)

        self.worker = BleWorker()
        self.devices: list[DeviceInfo] = []
        self.current: Reading | None = None
        self._auto_job: str | None = None
        self._compact = False
        self._drag_x = 0
        self._drag_y = 0
        self._geometry_full: str | None = None
        self._full_w = 360
        self._full_h = 480

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", lambda _e: self.exit_compact() if self._compact else None)
        self.after(200, self.scan_devices)

    def _build_ui(self) -> None:
        # Struttura: top_chrome / lcd_host / bottom_chrome
        # In modalità compatta si nascondono top/bottom e resta solo lcd_host.
        self.top_chrome = tk.Frame(self, bg=BG_APP)
        self.lcd_host = tk.Frame(
            self, bg=FRAME_PLASTIC, highlightbackground=FRAME_EDGE, highlightthickness=1
        )
        self.bottom_chrome = tk.Frame(self, bg=BG_APP)

        self.top_chrome.pack(fill="x", padx=16, pady=(8, 0))
        self.lcd_host.pack(padx=16, pady=8)
        self.bottom_chrome.pack(fill="x", padx=16, pady=(0, 12))

        header = tk.Frame(self.top_chrome, bg=BG_APP)
        header.pack(fill="x")
        tk.Label(
            header,
            text="Mi Temperature and Humidity Monitor 2",
            bg=BG_APP,
            fg=STATUS_FG,
            font=("Segoe UI", 9),
        ).pack(side="left", anchor="w")
        ttk.Button(header, text="Solo LCD", width=10, command=self.enter_compact).pack(
            side="right"
        )

        self.lcd = LcdDisplay(self.lcd_host)
        self.lcd.pack(padx=12, pady=12)

        self.status_var = tk.StringVar(value="Avvio scansione Bluetooth…")
        tk.Label(
            self.bottom_chrome,
            textvariable=self.status_var,
            bg=BG_APP,
            fg=STATUS_FG,
            font=("Segoe UI", 9),
            wraplength=320,
            justify="left",
        ).pack(anchor="w")

        self.detail_var = tk.StringVar(value="")
        tk.Label(
            self.bottom_chrome,
            textvariable=self.detail_var,
            bg=BG_APP,
            fg=STATUS_FG,
            font=("Consolas", 9),
        ).pack(anchor="w", pady=(2, 0))

        self.signal_var = tk.StringVar(value="")
        tk.Label(
            self.bottom_chrome,
            textvariable=self.signal_var,
            bg=BG_APP,
            fg=STATUS_FG,
            font=("Consolas", 9),
        ).pack(anchor="w", pady=(2, 0))

        row = tk.Frame(self.bottom_chrome, bg=BG_APP)
        row.pack(fill="x", pady=(10, 4))
        tk.Label(row, text="Sensore", bg=BG_APP, fg=STATUS_FG, font=("Segoe UI", 9)).pack(
            side="left"
        )
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(
            row, textvariable=self.device_var, state="readonly", width=36, values=[]
        )
        self.device_combo.pack(side="left", padx=(8, 0))
        self.device_combo.bind("<<ComboboxSelected>>", self._on_device_selected)

        controls = tk.Frame(self.bottom_chrome, bg=BG_APP)
        controls.pack(fill="x", pady=(6, 4))
        self.btn_refresh = ttk.Button(controls, text="Aggiorna", command=self.refresh_now)
        self.btn_refresh.pack(side="left")
        self.btn_scan = ttk.Button(controls, text="Scansiona", command=self.scan_devices)
        self.btn_scan.pack(side="left", padx=(8, 0))

        auto_row = tk.Frame(self.bottom_chrome, bg=BG_APP)
        auto_row.pack(fill="x", pady=(4, 8))
        self.auto_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            auto_row, text="Auto ogni", variable=self.auto_var, command=self._on_auto_toggle
        ).pack(side="left")
        self.interval_var = tk.IntVar(value=self.DEFAULT_INTERVAL_MIN)
        ttk.Spinbox(
            auto_row,
            from_=2,
            to=120,
            width=4,
            textvariable=self.interval_var,
            command=self._on_interval_change,
        ).pack(side="left", padx=(6, 4))
        tk.Label(auto_row, text="min", bg=BG_APP, fg=STATUS_FG, font=("Segoe UI", 9)).pack(
            side="left"
        )

        tk.Label(
            self.bottom_chrome,
            text="Elenco ordinato per segnale (più forte = più vicino). Solo LCD: trascinabile; doppio click / Esc per espandere.",
            bg=BG_APP,
            fg=STATUS_FG,
            font=("Segoe UI", 8),
            wraplength=340,
            justify="left",
        ).pack(anchor="w")

    def _device_label(self, d: DeviceInfo, nearest: bool = False) -> str:
        mark = " ★ vicino" if nearest else ""
        return f"{rssi_bars(d.rssi)} {rssi_label(d.rssi)}  {d.name} [{d.address}]{mark}"

    def _selected_device(self) -> DeviceInfo | None:
        idx = self.device_combo.current()
        if idx < 0 or idx >= len(self.devices):
            return None
        return self.devices[idx]

    def _update_signal_labels(self, device: DeviceInfo | None) -> None:
        if device is None:
            self.signal_var.set("")
            self.lcd.set_rssi(None)
            return
        self.signal_var.set(f"Segnale BLE: {rssi_bars(device.rssi)}  {rssi_label(device.rssi)}")
        self.lcd.set_rssi(device.rssi)

    def _on_device_selected(self, _event=None) -> None:
        self._update_signal_labels(self._selected_device())

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.btn_refresh.configure(state=state)
        self.btn_scan.configure(state=state)
        if busy:
            self.lcd.show_connecting()

    def scan_devices(self) -> None:
        self.status_var.set("Scansione Bluetooth e misura segnale…")
        self._set_busy(True)

        def ok(devices: list[DeviceInfo]):
            self.after(0, lambda: self._on_scan_ok(devices))

        def err(exc: BaseException):
            self.after(0, lambda: self._on_error(exc))

        self.worker.submit(scan_devices(timeout=8.0), ok, err)

    def _on_scan_ok(self, devices: list[DeviceInfo]) -> None:
        self._set_busy(False)
        self.devices = devices
        labels = [
            self._device_label(d, nearest=(i == 0 and d.rssi is not None))
            for i, d in enumerate(devices)
        ]
        self.device_combo.configure(values=labels)
        if devices:
            self.device_combo.current(0)
            self._update_signal_labels(devices[0])
            nearest = devices[0]
            extra = f" Più vicino: {rssi_label(nearest.rssi)}." if nearest.rssi is not None else ""
            self.status_var.set(f"Trovati {len(devices)} sensori (per segnale).{extra}")
            self.refresh_now()
        else:
            self.device_var.set("")
            self.signal_var.set("")
            self.status_var.set("Nessun termometro trovato. Avvicinalo e riprova.")
            self.lcd.show_placeholder()

    def refresh_now(self) -> None:
        device = self._selected_device()
        if device is None:
            self.status_var.set("Nessun sensore selezionato. Esegui una scansione.")
            return

        self.status_var.set(f"Lettura da {device.address}…")
        self._set_busy(True)

        def ok(reading: Reading):
            self.after(0, lambda: self._on_reading(reading))

        def err(exc: BaseException):
            self.after(0, lambda: self._on_error(exc))

        self.worker.submit(read_once(device.address, name=device.name), ok, err)

    def _on_reading(self, reading: Reading) -> None:
        self._set_busy(False)
        self.current = reading
        device = self._selected_device()
        rssi = device.rssi if device else None
        self.lcd.show_reading(reading, rssi=rssi)
        ts = reading.timestamp.strftime("%H:%M:%S") if reading.timestamp else "--"
        self.status_var.set(f"Aggiornato alle {ts}")
        bat = ""
        if reading.battery_percent is not None:
            bat = f"  ·  batteria {reading.battery_percent}%"
        elif reading.voltage is not None:
            bat = f"  ·  {reading.voltage:.3f} V"
        self.detail_var.set(f"{reading.address}{bat}")
        self._update_signal_labels(device)
        if self.auto_var.get():
            self._schedule_auto()

    def _on_error(self, exc: BaseException) -> None:
        self._set_busy(False)
        if self.current is None:
            self.lcd.show_placeholder()
        else:
            device = self._selected_device()
            self.lcd.show_reading(self.current, rssi=device.rssi if device else None)
        self.status_var.set(f"Errore: {exc}")
        if self.auto_var.get():
            self._schedule_auto()

    def enter_compact(self) -> None:
        if self._compact:
            return
        self.update_idletasks()
        self._full_w = max(self.winfo_width(), self.winfo_reqwidth())
        self._full_h = max(self.winfo_height(), self.winfo_reqheight())
        self._geometry_full = self.geometry()
        self._compact = True

        self.top_chrome.pack_forget()
        self.bottom_chrome.pack_forget()
        self.lcd_host.configure(highlightthickness=0)
        self.lcd.pack_configure(padx=0, pady=0)

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=FRAME_PLASTIC)
        self.lcd_host.pack(padx=0, pady=0)
        self.update_idletasks()
        self.geometry("280x200")

        self.lcd.bind("<ButtonPress-1>", self._start_drag)
        self.lcd.bind("<B1-Motion>", self._on_drag)
        self.lcd.bind("<Double-Button-1>", lambda _e: self.exit_compact())
        self.lcd.bind("<Button-3>", lambda _e: self.exit_compact())

    def exit_compact(self) -> None:
        if not self._compact:
            return
        self._compact = False
        # Posizione attuale del mini-LCD (dopo eventuale trascinamento)
        cur_x = self.winfo_rootx()
        cur_y = self.winfo_rooty()

        self.lcd.unbind("<ButtonPress-1>")
        self.lcd.unbind("<B1-Motion>")
        self.lcd.unbind("<Double-Button-1>")
        self.lcd.unbind("<Button-3>")

        self.attributes("-topmost", False)
        self.overrideredirect(False)
        self.configure(bg=BG_APP)
        self.lcd_host.configure(highlightthickness=1)
        self.lcd.pack_configure(padx=12, pady=12)

        self.lcd_host.pack_forget()
        self.top_chrome.pack(fill="x", padx=16, pady=(8, 0))
        self.lcd_host.pack(padx=16, pady=8)
        self.bottom_chrome.pack(fill="x", padx=16, pady=(0, 12))

        # Su Windows, dopo overrideredirect serve un ciclo withdraw/deiconify
        # altrimenti resta bloccata la geometria 280x200.
        self.withdraw()
        self.update_idletasks()
        w = max(self.winfo_reqwidth(), self._full_w)
        h = max(self.winfo_reqheight(), self._full_h)
        self.geometry(f"{w}x{h}+{cur_x}+{cur_y}")
        self.deiconify()
        self.after_idle(self._finalize_full_geometry)

    def _finalize_full_geometry(self) -> None:
        self.update_idletasks()
        w = max(self.winfo_reqwidth(), self._full_w)
        h = max(self.winfo_reqheight(), self._full_h)
        x = self.winfo_x()
        y = self.winfo_y()
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _start_drag(self, event) -> None:
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _on_drag(self, event) -> None:
        self.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

    def _on_auto_toggle(self) -> None:
        if self.auto_var.get():
            self.status_var.set(
                f"Auto-refresh ogni {self.interval_var.get()} min (connessione breve)."
            )
            self._schedule_auto()
        else:
            self._cancel_auto()
            self.status_var.set("Auto-refresh disattivato. Usa Aggiorna a richiesta.")

    def _on_interval_change(self) -> None:
        if self.auto_var.get():
            self._schedule_auto()

    def _cancel_auto(self) -> None:
        if self._auto_job is not None:
            self.after_cancel(self._auto_job)
            self._auto_job = None

    def _schedule_auto(self) -> None:
        self._cancel_auto()
        minutes = max(2, int(self.interval_var.get()))
        self._auto_job = self.after(minutes * 60_000, self._auto_tick)

    def _auto_tick(self) -> None:
        self._auto_job = None
        if self.auto_var.get():
            self.refresh_now()

    def _on_close(self) -> None:
        self._cancel_auto()
        self.worker.shutdown()
        self.destroy()


def main() -> None:
    app = ThermometerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
