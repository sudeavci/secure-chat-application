import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import os
import sys
import inspect
import io

# Dynamically include project src directory in module search path
tree = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(tree, '..'))
sys.path.insert(0, project_root)

# Import Server class and patch destructor to avoid missing server attribute
try:
    from Server.Server import Server
except ImportError:
    try:
        from Server import Server
    except ImportError:
        from Server import Server

# Monkey-patch Server.__del__ to ignore missing attributes
if hasattr(Server, '__del__'):
    orig_del = Server.__del__
    def __safe_del__(self):
        try:
            orig_del(self)
        except Exception:
            pass
    Server.__del__ = __safe_del__

class GuiStream(io.TextIOBase):
    def __init__(self, gui):
        super().__init__()
        self.gui = gui
    def write(self, s):
        s = s.rstrip()
        if s:
            self.gui.log(s)
    def flush(self):
        pass

class ServerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Server Control Panel")
        self.root.geometry("600x400")

        # --- Port Configuration ---
        port_frame = tk.Frame(self.root)
        port_frame.pack(pady=10)
        tk.Label(port_frame, text="Port:").pack(side=tk.LEFT)
        self.port_entry = tk.Entry(port_frame)
        self.port_entry.insert(0, "50000")
        self.port_entry.pack(side=tk.LEFT)

        # --- Control Buttons ---
        self.start_btn = tk.Button(self.root, text="Start Server", command=self.start_server)
        self.start_btn.pack(pady=5)
        self.stop_btn = tk.Button(self.root, text="Stop Server", state=tk.DISABLED, command=self.stop_server)
        self.stop_btn.pack(pady=5)

        # --- Log Display ---
        self.log_area = scrolledtext.ScrolledText(self.root, state=tk.DISABLED)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.server = None
        self.server_thread = None

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def start_server(self):
        port = int(self.port_entry.get())
        # Instantiate server with various signatures
        for attempt in [
            lambda: Server(port=port, log_callback=self.log),
            lambda: Server(port),
            lambda: Server()
        ]:
            try:
                self.server = attempt()
                break
            except TypeError:
                continue
        else:
            messagebox.showerror("Error", "Cannot instantiate Server with provided arguments.")
            return

        # Attach log_callback if supported
        if hasattr(self.server, 'log_callback'):
            try:
                setattr(self.server, 'log_callback', self.log)
            except Exception:
                pass

        # Determine start parameters
        sig = inspect.signature(self.server.start)
        start_params = []
        if len(sig.parameters) == 2:
            start_params = [port]

        # Prepare thread target to capture prints
        def run_server():
            old_out, old_err = sys.stdout, sys.stderr
            sys.stdout = GuiStream(self)
            sys.stderr = GuiStream(self)
            try:
                self.server.start(*start_params)
            finally:
                sys.stdout, sys.stderr = old_out, old_err

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

        self.log(f"Server started on port {port}")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

    def stop_server(self):
        if not self.server:
            return
        # Attempt to stop or shutdown
        if hasattr(self.server, 'stop'):
            try:
                self.server.stop()
            except Exception:
                pass
        elif hasattr(self.server, 'shutdown'):
            try:
                self.server.shutdown()
            except Exception:
                pass
        self.log("Server stopped")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def log(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"{message}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def on_closing(self):
        self.stop_server()
        self.root.destroy()

if __name__ == "__main__":
    ServerGUI()
