import os
import socket

from ServerClient import ServerClient
from SocketHandler import SocketHandler

GATEWAY_PORT = 50000
IP = socket.gethostbyname(socket.gethostname())

"""
    This class handles all the clients requests from the server
"""


class HandleClients:
    def __init__(self):
        self.clients: dict[str, ServerClient] = {}

    """
        adding a client
    """

    def add_client(self, client: ServerClient):
        self.clients[client.user_name] = client

    """
        returns all the clients names
    """

    def get_clients(self):
        return self.clients.keys()

    """
        removes client from the dict
    """

    def remove_client(self, client: ServerClient):
        self.clients.pop(client.user_name, None)

    """
        returns a client by the key value (name)
    """

    def get_client(self, key):
        return self.clients.get(key)

    """
        broadcasting the message to everyone who's connected
    """

    def send_all(self, msg):
        for client in self.clients.values():
            SocketHandler.send_msg(msg, client.client_socket)

    """
        sends the user list to a client
    """

    def send_user_list(self, conn):
        client_list = ""
        for client in self.get_clients():
            client_list += f"{client},"
        client_list = client_list[:len(client_list) - 1]
        SocketHandler.send_msg(f"SERVER: Connected users: {client_list}", conn)

    """
        handles the private message - getting a message from the one client and sending it 
        to other client in private
    """

    def handle_private_msg(self, client: ServerClient):
        dst_client_user_name = SocketHandler.get_msg(client.client_socket)
        if self.clients.get(dst_client_user_name) is None:
            SocketHandler.send_msg(f"SERVER: Client {dst_client_user_name} is not connected", client.client_socket)
        else:
            dst_client_socket = self.get_client(dst_client_user_name).client_socket
            msg = SocketHandler.get_msg(client.client_socket)
            msg_to = f"to {dst_client_user_name}: {msg}"
            SocketHandler.send_msg(msg_to, client.client_socket)
            msg_from = f"from {client.user_name}: {msg}"
            SocketHandler.send_msg(msg_from, dst_client_socket)

    """
        disconnects a client from the servers
    """

    def disconnect(self, client):
        self.remove_client(client)
        client.disconnect()
        self.send_all(f"SERVER: {client.user_name} has disconnected")

    """
        returns True if the username is not taken, else returns False
    """

    def is_user_available(self, name):
        if self.get_client(name) is None:
            return True
        return False

    """
        returns the file list to a client
    """

    def send_file_list(self, client: ServerClient):
        files_path = os.path.abspath("ServerFiles")
        files_list = os.listdir(files_path)
        msg = f"SERVER: Server file list: {str(files_list)}"
        SocketHandler.send_msg(msg, client.client_socket)

    """
       returns the commands list to a client
    """

    def send_commands_list(self, client: ServerClient):
        msg = "SERVER:\n" \
              "/users - get a list of all connected users\n" \
              "/disconnect - disconnect from chat\n" \
              "/files - get a list of all the files\n" \
              "/whisper <client name> <msg> - send a private message to another user"
        SocketHandler.send_msg(msg, client.client_socket)

    """
        checks if a file name exists, return False otherwise
    """

    def check_file_name(self, file_name):
        files_path = os.path.abspath("ServerFiles")
        files_list = os.listdir(files_path)
        if file_name in files_list:
            return True
        else:
            return False

    """
        sends message to a client
    """

    def send_message(self, msg, client_socket):
        SocketHandler.send_msg(msg, client_socket)
