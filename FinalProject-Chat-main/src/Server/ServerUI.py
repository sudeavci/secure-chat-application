# -*- coding: utf-8 -*-
"""
Server Control UI (v1.4)
========================
* Otomatik testler **varsayılan olarak devre dışı**; yalnızca
  komut satırında `--selftest` bayrağı verilirse çalışır.
* Testler, soket bağlama/port çakışması sorununu `socket.socket.bind`
  ve `listen` metodlarını **mock** ederek önler; böylece gerçek porta
  dokunulmaz.

Kullanım
~~~~~~~~
python ServerUI.py              # GUI/CLI doğrudan açılır, test yok
python ServerUI.py --selftest   # Önce test, sonra başarılıysa GUI/CLI
"""
from __future__ import annotations

import builtins
import queue
import sys
import threading
from datetime import datetime
from typing import Callable

# --------------------------------------------------------------------------- #
#                           Sunucu Entegrasyonu                               #
# --------------------------------------------------------------------------- #
try:
    # Projendeki gerçek sunucu sınıfını içe aktar
    from Server import Server
except ImportError:  # Sandbox / koddan bağımsız deneme

    class Server:  # type: ignore
        """Basit mock sunucu (print tabanlı log)."""

        def __init__(self) -> None:
            self.clients: list[str] = []

        def start(self) -> None:
            print("[MOCK] Sunucu başlatıldı …")

        def stop(self) -> None:
            print("[MOCK] Sunucu durduruldu.")

        def broadcast(self, msg: str) -> None:
            print(f"[MOCK] Broadcast: {msg}")


# --------------------------------------------------------------------------- #
#                           GUI Modu (Tkinter)                                #
# --------------------------------------------------------------------------- #
try:
    import tkinter as tk
    from tkinter import messagebox, scrolledtext, ttk

    TK_AVAILABLE = True
except ModuleNotFoundError:      # Tkinter kurulu değilse CLI'ye düşülür
    TK_AVAILABLE = False


if TK_AVAILABLE:

    class ServerGUI(tk.Tk):
        """Tkinter tabanlı grafik kontrol paneli."""

        def __init__(self) -> None:
            super().__init__()
            self.title("Sunucu Kontrol Paneli")
            self.geometry("740x480")
            self.minsize(640, 400)

            # Sunucu örneği ve yardımcılar
            self.server: Server | None = None
            self._log_q: "queue.Queue[str]" = queue.Queue()
            self._orig_print: Callable = builtins.print  # stdout yedeği

            self._build_widgets()
            self.after(200, self._drain_log)
            self.after(1000, self._refresh_clients)

        # --------------------------- Arayüz ---------------------------- #
        def _build_widgets(self) -> None:
            top = ttk.Frame(self)
            top.pack(fill="x", padx=10, pady=6)

            self.btn_start = ttk.Button(top, text="Başlat", command=self._start)
            self.btn_start.pack(side="left", padx=4)

            self.btn_stop = ttk.Button(
                top, text="Durdur", state="disabled", command=self._stop
            )
            self.btn_stop.pack(side="left", padx=4)

            ttk.Label(top, text="Durum:").pack(side="left", padx=(20, 3))
            self.status = tk.StringVar(value="Kapalı")
            ttk.Label(top, textvariable=self.status, foreground="red").pack(side="left")

            # Orta alan – istemci listesi + log
            mid = ttk.Frame(self)
            mid.pack(fill="both", expand=True, padx=10, pady=(0, 6))

            lf_clients = ttk.Labelframe(mid, text="Bağlı İstemciler")
            lf_clients.pack(side="left", fill="y", ipadx=4, padx=(0, 10))
            self.lst_clients = tk.Listbox(lf_clients, width=28)
            self.lst_clients.pack(fill="both", expand=True, padx=6, pady=6)

            lf_log = ttk.Labelframe(mid, text="Sunucu Günlüğü")
            lf_log.pack(side="left", fill="both", expand=True)
            self.txt_log = scrolledtext.ScrolledText(
                lf_log, state="disabled", wrap="word"
            )
            self.txt_log.pack(fill="both", expand=True, padx=6, pady=6)

            # Alt alan – broadcast
            bot = ttk.Frame(self)
            bot.pack(fill="x", padx=10, pady=6)
            self.ent_msg = ttk.Entry(bot)
            self.ent_msg.pack(side="left", fill="x", expand=True, padx=(0, 6))
            self.ent_msg.bind("<Return>", lambda *_: self._broadcast())
            ttk.Button(bot, text="Yayınla", command=self._broadcast).pack(side="left")

        # ----------------------- Sunucu kontrol ------------------------ #
        def _start(self) -> None:
            if self.server:
                return
            try:
                # Sunucu log_cb parametresini destekliyorsa kullan
                self.server = Server(log_cb=self._enqueue)  # type: ignore[arg-type]
            except TypeError:
                # Desteklemiyorsa print yakalama moduna geç
                self.server = Server()
                self._patch_print()
            except OSError as e:
                messagebox.showerror("Port hatası", f"Sunucu başlatılamadı:\n{e}")
                return

            try:
                threading.Thread(target=self.server.start, daemon=True).start()
            except OSError as e:
                messagebox.showerror("Sunucu hatası", f"Sunucu çalıştırılamadı:\n{e}")
                return

            self.status.set("Çalışıyor")
            self.btn_start.config(state="disabled")
            self.btn_stop.config(state="normal")

        def _stop(self) -> None:
            if not self.server:
                return
            try:
                self.server.stop()
            finally:
                self.server = None
                self.status.set("Kapalı")
                self.btn_start.config(state="normal")
                self.btn_stop.config(state="disabled")
                self.lst_clients.delete(0, tk.END)
                self._restore_print()

        def _broadcast(self) -> None:
            if self.server and (msg := self.ent_msg.get().strip()):
                self.server.broadcast(msg)
                self.ent_msg.delete(0, tk.END)

        # ----------------------- Log yakalama -------------------------- #
        def _enqueue(self, msg: str) -> None:
            self._log_q.put(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

        def _drain_log(self) -> None:
            while not self._log_q.empty():
                line = self._log_q.get_nowait()
                self.txt_log.config(state="normal")
                self.txt_log.insert("end", line + "\n")
                self.txt_log.config(state="disabled")
                self.txt_log.yview_moveto(1.0)
            self.after(200, self._drain_log)

        def _patch_print(self) -> None:
            if builtins.print is self._enqueue:
                return  # zaten patch'li

            def print_to_gui(*args, **kwargs):
                self._orig_print(*args, **kwargs)           # terminale de bas
                self._enqueue(" ".join(map(str, args)))     # GUI'ye yaz

            builtins.print = print_to_gui  # type: ignore[assignment]

        def _restore_print(self) -> None:
            builtins.print = self._orig_print  # type: ignore[assignment]

        # ------------------------- İstemciler --------------------------- #
        def _refresh_clients(self) -> None:
            if self.server and hasattr(self.server, "clients"):
                self.lst_clients.delete(0, tk.END)
                for c in list(self.server.clients):
                    self.lst_clients.insert(tk.END, str(c))
            self.after(1000, self._refresh_clients)

        # ---------------------------- Çıkış ---------------------------- #
        def on_close(self) -> None:
            if self.server and messagebox.askokcancel(
                "Çıkış", "Sunucuyu durdurup çıkmak ister misin?"
            ):
                self._stop()
            self.destroy()


# --------------------------------------------------------------------------- #
#                        CLI Modu (stdin)                                     #
# --------------------------------------------------------------------------- #
def _stdin_is_interactive() -> bool:
    return sys.stdin and sys.stdin.isatty()


class ServerCLI:
    PROMPT = "\nKomutlar: start | stop | clients | broadcast <mesaj> | quit\n> "

    def __init__(self) -> None:
        self.server: Server | None = None
        self.running = True
        self.interactive = _stdin_is_interactive()

    # Yardımcı log
    def _log(self, msg: str) -> None:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    # Komut işleyicileri
    def _cmd_start(self) -> None:
        if self.server:
            print("Sunucu zaten çalışıyor.")
            return
        try:
            self.server = Server()
            threading.Thread(target=self.server.start, daemon=True).start()
            self._log("Sunucu başlatılıyor …")
        except OSError as e:
            print(f"Sunucu başlatılamadı: {e}")

    def _cmd_stop(self) -> None:
        if not self.server:
            print("Sunucu zaten kapalı.")
            return
        self.server.stop()
        self.server = None
        self._log("Sunucu durduruldu.")

    def _cmd_clients(self) -> None:
        if not self.server:
            print("Sunucu kapalı.")
            return
        print("Bağlı istemciler:", list(self.server.clients))

    def _cmd_broadcast(self, msg: str) -> None:
        if not self.server:
            print("Sunucu kapalı.")
            return
        self.server.broadcast(msg)

    # Ana döngü
    def cmdloop(self) -> None:
        if not self.interactive:
            print("(stdin interaktif değil → CLI döngüsü atlandı)")
            return
        print("Etkileşimli Konsol Sunucu Arayüzü")
        while self.running:
            try:
                raw = input(self.PROMPT).strip()
            except (EOFError, KeyboardInterrupt):
                raw = "quit"
            if not raw:
                continue
            cmd, *args = raw.split(maxsplit=1)
            arg = args[0] if args else ""
            match cmd:
                case "start":
                    self._cmd_start()
                case "stop":
                    self._cmd_stop()
                case "clients":
                    self._cmd_clients()
                case "broadcast":
                    self._cmd_broadcast(arg)
                case "quit" | "exit":
                    self._cmd_stop()
                    self.running = False
                case _:
                    print("Bilinmeyen komut.")

# --------------------------------------------------------------------------- #
#                    İsteğe Bağlı Mini Self-Test                              #
# --------------------------------------------------------------------------- #
def _run_selftests() -> bool:        # → True = tüm testler geçti
    import unittest
    import socket
    from unittest import mock

    # ---- socket.bind / listen mock'lanıyor (port çakışmaz) ---- #
    dummy = lambda *a, **k: None
    with mock.patch("socket.socket.bind", dummy), mock.patch(
        "socket.socket.listen", dummy
    ):

        class _Tests(unittest.TestCase):
            def test_server_init(self):
                self.assertIsInstance(Server(), Server)

            def test_tk_flag_valid(self):
                self.assertIn(TK_AVAILABLE, (True, False))

            @unittest.skipUnless(TK_AVAILABLE, "Tk yok")
            def test_gui_start(self):
                gui = ServerGUI()
                try:
                    gui._start()  # mock sayesinde gerçek porta dokunmaz
                finally:
                    gui.destroy()

        result = unittest.TextTestRunner(
            stream=sys.stderr, verbosity=0
        ).run(unittest.defaultTestLoader.loadTestsFromTestCase(_Tests))
        return result.wasSuccessful()

# --------------------------------------------------------------------------- #
#                                Main                                         #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.argv.remove("--selftest")
        if not _run_selftests():
            sys.exit(1)

    if TK_AVAILABLE:
        app = ServerGUI()
        app.protocol("WM_DELETE_WINDOW", app.on_close)  # graceful close
        app.mainloop()
    else:
        ServerCLI().cmdloop()
