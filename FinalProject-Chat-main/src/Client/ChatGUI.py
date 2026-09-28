from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import ButtonActions
import HandleThreads
from Actions import Actions
from SocketHandler import SocketHandler
from Client import Client
import time


class ChatGUI:
    def __init__(self, user: Client):
        self.window = Tk()
        self.window.withdraw()

        # ——— LOGIN WINDOW ———
        self.login = Toplevel()
        self.login.title("Login")
        self.login.resizable(width=False, height=False)
        self.login.configure(width=650, height=400)

        self.login_label = Label(
            self.login,
            text="Please login to continue",
            justify=CENTER,
            font="Helvetica 14 bold"
        )
        self.login_label.place(relheight=0.1, relx=0.35, rely=0.07)

        self.label_name = Label(
            self.login,
            text="Enter your name:",
            font="Helvetica 12"
        )
        self.label_name.place(relheight=0.1, relx=0.03, rely=0.2)

        self.label_address = Label(
            self.login,
            text="Enter server IP:",
            font="Helvetica 12"
        )
        self.label_address.place(relheight=0.1, relx=0.03, rely=0.4)

        self.window.protocol("WM_DELETE_WINDOW", self.close_chat)
        self.login.protocol("WM_DELETE_WINDOW", self.close_login)

        self.entry_name = Entry(
            self.login,
            font="Helvetica 14"
        )
        self.entry_name.place(relwidth=0.4, relheight=0.12, relx=0.35, rely=0.2)

        self.entry_address = Entry(
            self.login,
            font="Helvetica 14"
        )
        self.entry_address.place(relwidth=0.4, relheight=0.12, relx=0.35, rely=0.4)
        self.entry_name.focus()

        self.button_action = ButtonActions.ButtonsActions(self)
        self.thread = HandleThreads.HandleThreads(self, self.button_action)
        self.user = user

        self.btn = Button(
            self.login,
            text="CONTINUE",
            font="Helvetica 14 bold",
            command=lambda: self.validation(
                self.entry_name.get(),
                self.entry_address.get()
            )
        )
        self.btn.place(relx=0.45, rely=0.58)

        # Variables
        self.download_button = None
        self.name = None
        self.text_cons = None
        self.msg = None
        self.user_listbox = None
        self.topology_window = None

        self.window.mainloop()

    def validation(self, name, address):
        if not self.is_valid(name):
            self.error_msg()
            return
        self.user.set_address(address)
        self.user.set_username(name)
        self.user.connect()
        if not self.is_connected():
            self.connect_error_msg()
            return
        if not self.is_name_free():
            self.user.connected = False
            self.taken_name_msg()
            self.user.close_socket()
            return
        # Get UDP port info from server
        self.user.udp_address = (
            self.user.ip,
            int(SocketHandler.get_msg(self.user.tcp_socket))
        )
        self.enter_main_window(name)

    def enter_main_window(self, name):
        self.login.destroy()
        self.layout(name)
        # Start listening for TCP messages
        self.thread.start_receiver()
        # Request active user list
        self.thread.start_sender("/users")

    def layout(self, name):
        self.name = name
        self.window.deiconify()
        self.window.title(f"Welcome, {self.name}")
        self.window.resizable(width=True, height=True)
        self.window.configure(width=800, height=550, bg="#17202A")

        self.add_chat_window()
        self.add_buttons()
        self.text_cons.config(cursor="arrow")
        self.add_scrollbar()

    def update_chat_display(self, message):
        if self.user.connected:
            self.text_cons.config(state=NORMAL)
            self.text_cons.insert(END, message + "\n")
            self.text_cons.config(state=DISABLED)
            self.text_cons.see(END)

    def update_user_list(self, users_csv: str):
        users = [u.strip() for u in users_csv.split(',') if u.strip()]
        self.user_listbox.delete(0, END)
        if not users:
            self.user_listbox.insert(END, "No active users")
        else:
            for u in users:
                self.user_listbox.insert(END, u)

        if self.topology_window and self.topology_window.winfo_exists():
            self.update_topology_display(users)

    def add_buttons(self):
        disconnect_btn = Button(
            self.window,
            text="Disconnect",
            font="Helvetica 10 bold",
            width=15,
            bg="#ABB2B9",
            command=lambda: self.button_action.handle_disconnect()
        )
        disconnect_btn.place(relx=0.78, rely=0.84, relheight=0.04, relwidth=0.20)

        self.download_button = Button(
            self.window,
            text="Download File",
            font="Helvetica 10 bold",
            width=15,
            bg="#ABB2B9",
            command=lambda: self.file_download_window()
        )
        self.download_button.place(relx=0.78, rely=0.88, relheight=0.04, relwidth=0.20)

        show_commands_btn = Button(
            self.window,
            text="Show Commands",
            font="Helvetica 10 bold",
            width=15,
            bg="#ABB2B9",
            command=lambda: self.button_action.handle_show_commands()
        )
        show_commands_btn.place(relx=0.78, rely=0.92, relheight=0.04, relwidth=0.20)

        topology_btn = Button(
            self.window,
            text="Network Topology",
            font="Helvetica 10 bold",
            width=15,
            bg="#ABB2B9",
            command=self.show_topology_window
        )
        topology_btn.place(relx=0.78, rely=0.96, relheight=0.04, relwidth=0.20)

    def show_topology_window(self):
        """
        Creates the network topology window with a star architecture visualization.
        """
        if self.topology_window and self.topology_window.winfo_exists():
            self.topology_window.lift()
            return

        self.topology_window = Toplevel(self.window)
        self.topology_window.title("Network Topology - Star Architecture")
        self.topology_window.configure(width=600, height=500, bg="#17202A")
        self.topology_window.resizable(width=True, height=True)
        self.topology_window.protocol("WM_DELETE_WINDOW", self.close_topology_window)

        main_frame = Frame(self.topology_window, bg="#17202A")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        title_label = Label(
            main_frame,
            text="Network Topology Map",
            font="Helvetica 18 bold",
            bg="#17202A",
            fg="#EAECEE"
        )
        title_label.pack(pady=(0, 20))

        self.create_topology_canvas(main_frame)
        self.create_info_panel(main_frame)

        refresh_btn = Button(
            main_frame,
            text="🔄 Refresh",
            font="Helvetica 12 bold",
            bg="#3498DB",
            fg="white",
            command=self.refresh_topology
        )
        refresh_btn.pack(pady=10)

        self.refresh_topology()

    def create_topology_canvas(self, parent):
        """Creates canvas for topology visualization."""
        canvas_frame = Frame(parent, bg="#1C2833", relief="solid", bd=2)
        canvas_frame.pack(fill="both", expand=True, pady=10)

        self.topology_canvas = Canvas(canvas_frame, bg="#2C3E50", height=300)
        self.topology_canvas.pack(fill="both", expand=True, padx=5, pady=5)

    def create_info_panel(self, parent):
        """Creates the network info panel."""
        info_frame = LabelFrame(
            parent,
            text="Network Info",
            font="Helvetica 12 bold",
            bg="#17202A",
            fg="#EAECEE"
        )
        info_frame.pack(fill="x", pady=10)

        server_ip = getattr(self.user, 'ip', 'Unknown')
        self.server_info_label = Label(
            info_frame,
            text=f"🖥️  Central Server: {server_ip}",
            font="Helvetica 11",
            bg="#17202A",
            fg="#EAECEE"
        )
        self.server_info_label.pack(anchor="w", padx=10, pady=2)

        self.user_count_label = Label(
            info_frame,
            text="👥  Connected Users: 0",
            font="Helvetica 11",
            bg="#17202A",
            fg="#EAECEE"
        )
        self.user_count_label.pack(anchor="w", padx=10, pady=2)

        self.connection_status_label = Label(
            info_frame,
            text="🟢  Status: Connected",
            font="Helvetica 11",
            bg="#17202A",
            fg="#27AE60"
        )
        self.connection_status_label.pack(anchor="w", padx=10, pady=2)

        topology_type_label = Label(
            info_frame,
            text="🌟  Topology Type: Star",
            font="Helvetica 11",
            bg="#17202A",
            fg="#EAECEE"
        )
        topology_type_label.pack(anchor="w", padx=10, pady=2)

    def refresh_topology(self):
        """Refreshes the topology visualization."""
        if not (self.topology_window and self.topology_window.winfo_exists()):
            return

        self.topology_canvas.delete("all")
        connected_users = []
        try:
            users_from_listbox = self.user_listbox.get(0, END)
            if users_from_listbox and users_from_listbox[0] != "No active users":
                connected_users = list(users_from_listbox)
        except:
            pass

        self.draw_star_topology(connected_users)
        self.update_info_labels(connected_users)

    def draw_star_topology(self, users):
        """Draws a star topology."""
        canvas_width = self.topology_canvas.winfo_width()
        canvas_height = self.topology_canvas.winfo_height()

        if canvas_width <= 1:
            canvas_width = 400
        if canvas_height <= 1:
            canvas_height = 250

        center_x = canvas_width // 2
        center_y = canvas_height // 2

        server_radius = 30
        self.topology_canvas.create_oval(
            center_x - server_radius, center_y - server_radius,
            center_x + server_radius, center_y + server_radius,
            fill="#E74C3C", outline="#C0392B", width=3
        )
        self.topology_canvas.create_text(
            center_x, center_y,
            text="SERVER\n🖥️",
            fill="white",
            font="Helvetica 10 bold"
        )

        if users:
            import math
            user_count = len(users)
            client_radius = 20
            circle_radius = min(canvas_width, canvas_height) // 3

            for i, user in enumerate(users):
                angle = 2 * math.pi * i / user_count
                user_x = center_x + circle_radius * math.cos(angle)
                user_y = center_y + circle_radius * math.sin(angle)

                self.topology_canvas.create_line(
                    center_x, center_y, user_x, user_y,
                    fill="#3498DB", width=2, dash=(5, 3)
                )

                color = "#27AE60" if user == self.name else "#3498DB"
                self.topology_canvas.create_oval(
                    user_x - client_radius, user_y - client_radius,
                    user_x + client_radius, user_y + client_radius,
                    fill=color, outline="#2C3E50", width=2
                )

                self.topology_canvas.create_text(
                    user_x, user_y,
                    text=f"👤\n{user[:8]}",
                    fill="white",
                    font="Helvetica 8 bold"
                )
        else:
            self.topology_canvas.create_text(
                center_x, center_y + 80,
                text="No users connected yet",
                fill="#BDC3C7",
                font="Helvetica 12 italic"
            )

    def update_topology_display(self, users):
        if self.topology_window and self.topology_window.winfo_exists():
            self.refresh_topology()

    def update_info_labels(self, users):
        try:
            user_count = len(users) if users else 0
            self.user_count_label.config(
                text=f"👥  Connected Users: {user_count}"
            )
            if self.user.connected:
                self.connection_status_label.config(
                    text="🟢  Status: Connected", fg="#27AE60"
                )
            else:
                self.connection_status_label.config(
                    text="🔴  Status: Disconnected", fg="#E74C3C"
                )
        except:
            pass

    def close_topology_window(self):
        if self.topology_window:
            self.topology_window.destroy()
            self.topology_window = None

    def add_chat_window(self):
        name_label = Label(
            self.window,
            bg="#17202A",
            fg="#EAECEE",
            text=self.name,
            font="Helvetica 13 bold",
            pady=5
        )
        name_label.place(relwidth=1)

        line = Label(self.window, width=450, bg="#ABB2B9")
        line.place(relwidth=1, rely=0.07, relheight=0.012)

        bottom_label = Label(self.window, bg="#ABB2B9", height=80)
        bottom_label.place(relwidth=0.75, rely=0.825)

        self.text_cons = Text(
            self.window,
            width=20,
            height=2,
            bg="#17202A",
            fg="#EAECEE",
            font="Helvetica 14",
            padx=5,
            pady=5
        )
        self.text_cons.place(relheight=0.745, relwidth=0.75, rely=0.08)

        self.user_listbox = Listbox(
            self.window,
            bg="#1C2833",
            fg="#EAECEE",
            font="Helvetica 12"
        )
        self.user_listbox.place(relheight=0.745, relwidth=0.23, relx=0.76, rely=0.08)
        self.user_listbox.insert(END, "No active users")

        entry_msg = Entry(
            bottom_label,
            bg="#2C3E50",
            fg="#EAECEE",
            font="Helvetica 13"
        )
        entry_msg.place(relwidth=0.74, relheight=0.06, rely=0.008, relx=0.011)
        entry_msg.focus()

        self.window.bind(
            '<Return>',
            lambda event: self.send_msg(event, entry_msg.get(), entry_msg)
        )

    def send_msg(self, event, msg, entry_msg):
        self.text_cons.config(state=DISABLED)
        entry_msg.delete(0, END)
        self.thread.start_sender(msg)

    def add_scrollbar(self):
        scrollbar = Scrollbar(self.window)
        scrollbar.place(relheight=1, relx=0.98)
        scrollbar.config(command=self.text_cons.yview)
        self.text_cons.config(state=DISABLED)

    def close_chat(self):
        if messagebox.askokcancel("Quit", "Are you sure you want to disconnect?"):
            self.button_action.handle_disconnect()

    def close_login(self):
        if messagebox.askokcancel("Quit", "Are you sure you want to exit?"):
            quit()

    def error_msg(self):
        error = Label(
            self.login,
            text="---please enter a valid one-word name---",
            font="Helvetica 12"
        )
        error.place(relheight=0.1, relx=0.33, rely=0.7)

    def taken_name_msg(self):
        error = Label(
            self.login,
            text="---Name is taken, please try a different name---",
            font="Helvetica 12"
        )
        error.place(relheight=0.1, relx=0.33, rely=0.7)

    def file_download_window(self):
        file_window = Toplevel(self.window)
        file_label = Label(
            file_window,
            text="Enter file name to download",
            font="Helvetica 14 bold"
        )
        file_label.place(relheight=0.1, relx=0.25, rely=0.07)

        entry_file_name = Entry(
            file_window,
            font="Helvetica 14"
        )
        entry_file_name.place(relwidth=0.5, relheight=0.15, relx=0.27, rely=0.3)

        download_btn = Button(
            file_window,
            text="Download",
            font="Helvetica 14 bold",
            command=lambda: self.button_action.handle_file_download(
                entry_file_name.get(),
                file_window,
                self.download_button,
                None
            )
        )
        download_btn.place(relx=0.40, rely=0.58)

        file_window.title("Download File")
        file_window.configure(width=500, height=150)

    def swap_buttons(self, button_to_destroy, button_to_create):
        button_to_destroy.destroy()
        button_to_create.place(relx=0.78, rely=0.89, relheight=0.04, relwidth=0.15)

    def recreate_download_btn(self):
        self.download_button = Button(
            self.window,
            text="Download File",
            font="Helvetica 10 bold",
            width=20,
            bg="#ABB2B9",
            command=lambda: self.file_download_window()
        )
        self.download_button.place(relx=0.78, rely=0.89, relheight=0.04, relwidth=0.15)

    def is_connected(self):
        return getattr(self.user, "connected", False)

    def is_name_free(self):
        return self.is_available()

    def connect_error_msg(self):
        error = Label(
            self.login,
            text="----------Couldn't connect to server----------",
            font="Helvetica 12"
        )
        error.place(relheight=0.1, relx=0.37, rely=0.7)

    def is_valid(self, name):
        return (len(name) > 1 and name.isalpha() and self.is_english(name) and " " not in name)

    def is_english(self, name):
        try:
            name.encode(encoding='utf-8').decode('ascii')
            return True
        except:
            return False

    def is_available(self):
        return SocketHandler.get_enum(self.user.tcp_socket) == Actions.TRUE.value

    def __del__(self):
        try:
            self.button_action.handle_disconnect()
        except:
            pass
