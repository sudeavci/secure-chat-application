class ButtonsActions:
    def __init__(self, display_chat):
        self.display_chat = display_chat
        self.file_name = None

    """
        handle the disconnection button - disconnects the client
    """

    def handle_disconnect(self):
        self.display_chat.user.disconnect()
        self.display_chat.window.destroy()

    """
         handle the file download button - downloading the file for the client
    """

    def handle_file_download(self, file_name, file_window, btn_to_destory, btn_to_create):
        self.file_name = file_name
        if len(file_name) > 0:
            if self.display_chat.user.check_file_name(file_name):
                while not self.display_chat.user.download_file(file_name):
                    continue
                else:
                    file_window.destroy()
                    self.display_chat.swap_buttons(btn_to_destory, btn_to_create)

    """
        handle the proceed button to proceed the file download for the client
    """

    def proceed_download(self):
        while not self.display_chat.user.download_file(self.file_name):
            continue
        self.display_chat.recreate_download_btn()

    """
        letting the server know we are going to open a udp connection
    """

    def handle_udp_connection(self):
        self.display_chat.user.open_udp_connection()

    """
        show all the commands for the client button
    """

    def handle_show_commands(self):
        self.display_chat.user.get_commands()
