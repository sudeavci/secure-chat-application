import os.path
import pickle
import socket
import time

from Actions import Actions
from SocketHandler import SocketHandler

GATEWAY_PORT_TCP = 50000
MSG_SIZE = 64000
DEFAULT_IP = socket.gethostbyname(socket.gethostname())


class Client:
    def __init__(self, user_name: str = None, ip: str = DEFAULT_IP):
        self.user_name = user_name
        self.ip = ip
        self.tcp_address = (self.ip, GATEWAY_PORT_TCP)
        self.udp_address = None
        self.tcp_socket = None
        self.udp_socket = None
        self.connected = False
        self.received_half_file = False
        self.packets_received = {}
        self.is_file_exists = False

    """
        set the username for the client.
    """

    def set_username(self, username):
        self.user_name = username

    """
        set the address of the server the client connects to.
    """

    def is_connected(self):
        return self.connected

    def set_address(self, ip):
        if ip == "localhost" or len(ip) == 0 or ip == "127.0.0.1":
            self.ip = DEFAULT_IP
        else:
            self.ip = ip
        self.tcp_address = (self.ip, GATEWAY_PORT_TCP)

    """
        connects the client with the server
        sends the username for the serve to approve it's free 
    """

    def connect(self):
        try:
            # self.bind_port()
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if not self.connected:
                self.tcp_socket.connect(self.tcp_address)
                SocketHandler.send_msg(self.user_name, self.tcp_socket)
                print(self.tcp_socket.getsockname())
                self.connected = True
        except Exception as e:
            print(e)
            print("No connection")

    """
        this function sends enum to server to disconnect
    """

    def disconnect(self):
        SocketHandler.send_enum(Actions.DISCONNECT.value, self.tcp_socket)
        self.connected = False

    """
        closing the socket
    """

    def close_socket(self):
        self.tcp_socket.close()

    """
        sends enum to server to get users list
    """

    def get_users(self):
        SocketHandler.send_enum(Actions.USER_LIST.value, self.tcp_socket)

    """
        sends private message to a client through server
    """

    def send_private_msg(self, msg, user_name):
        msg = " ".join(msg)
        SocketHandler.send_enum(Actions.PRIVATE_MSG.value, self.tcp_socket)
        SocketHandler.send_msg(user_name, self.tcp_socket)
        SocketHandler.send_msg(msg, self.tcp_socket)

    """
        taking care of commands received from the client
    """

    def action_received(self, msg: str):
        msg = msg.split(" ")
        if msg[0][1:] == "users":
            self.get_users()
        elif msg[0][1:] == "disconnect":
            self.disconnect()
        elif msg[0][1:] == "files":
            self.get_file_list()
        elif msg[0][1:] == "whisper":
            if len(msg) > 2:
                self.send_private_msg(msg[2:], msg[1])
        elif msg[0][1:] == "commands":
            self.get_commands()

    """
        sends message to all clients in the chat
    """

    def send_msg_to_all(self):
        SocketHandler.send_enum(Actions.MESSAGE_ALL.value, self.tcp_socket)

    """
        sends enum to server to get the file list
    """

    def get_file_list(self):
        SocketHandler.send_enum(Actions.FILE_LIST.value, self.tcp_socket)

    """
        sends enum to server to get commands list
    """

    def get_commands(self):
        SocketHandler.send_enum(Actions.COMMANDS.value, self.tcp_socket)

    """
        this function is to find a free port for the client in a specific range
    """

    def bind_port(self):
        taken_ports = 0
        curr_port = 55000
        is_found = False
        while not is_found:
            try:
                self.tcp_socket.bind(('', curr_port))
                is_found = True
            except:
                curr_port += 1
                taken_ports += 1

            if taken_ports > 15:
                print("couldn't find a free port within range - chat room is full")
                exit(1)
        return

    """
        this function opens a UDP socket to get a file from the server
        we use "three way hand shake" method to make sure the server is listening
        and only then transferring the file
    """

    def check_file_name(self, file_name):
        SocketHandler.send_enum(Actions.CHECK_FILE_NAME.value, self.tcp_socket)
        SocketHandler.send_msg(file_name, self.tcp_socket)
        time.sleep(0.1)
        if self.is_file_exists == "True":
            return True
        return False

    def get_msg(self, msg):
        self.is_file_exists = msg

    def download_file(self, file_name):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        SocketHandler.send_enum(Actions.OPEN_UDP.value, self.tcp_socket)
        self.udp_socket.settimeout(0.3)
        if self.check_reliablity():
            try:
                self.udp_socket.sendto(file_name.encode(), self.udp_address)
            except:
                self.close_udp_connection(self.udp_socket)
                return False
        else:
            self.close_udp_connection(self.udp_socket)
            return False
        if not self.get_packets(file_name):
            return False
        self.close_udp_connection(self.udp_socket)
        return True

    """
        this function receiving all the packets from the server that are associated with the file
        if a packet is not received the server sends it again, and we also have a time out.
    """

    def get_packets(self, file_name):
        arrived = 0
        next_expected_seq = 1
        try:
            num_of_pkts = self.udp_socket.recvfrom(MSG_SIZE)[0].decode()
        except:
            return False
        print(f"number of expected packets received from server: {num_of_pkts}")
        while arrived < int(num_of_pkts):
            try:
                curr_pkt = self.udp_socket.recvfrom(MSG_SIZE)[0]
                curr_pkt = pickle.loads(curr_pkt)
                seq_num = curr_pkt[0]
                data_chunk = curr_pkt[1]
                self.udp_socket.sendto(f"{seq_num}".encode(), self.udp_address)
                next_expected_seq += 1
                if self.packets_received.get(seq_num) is None:
                    self.packets_received[seq_num] = data_chunk
                    arrived += 1
                    print(f"packet number {seq_num} received, sending ACK...", )
            except Exception as e:
                print(e)
                continue
        self.udp_socket.sendto(f"-10".encode(), self.udp_address)
        print("RECEIVED ALL PACKETS SUCCESSFULLY")
        if not self.received_half_file:
            self.received_half_file = True
            return True
        else:
            self.write_files(self.packets_received, file_name)
            self.received_half_file = False
            return True

    """
        this function writes the file in the correct order with all the packets we have received
    """

    def write_files(self, packets_received, file_name: str):
        file_name = file_name.split('.')
        file_name = f"{file_name[0]}_copy.{file_name[1]}"
        save_path = 'MyFiles'
        save_in = os.path.join(save_path, file_name)
        f = open(save_in, "wb")
        for _, value in sorted(packets_received.items()):
            f.write(value)
        f.close()
        self.packets_received.clear()

    """
        closes the UDP connection
    """

    def close_udp_connection(self, udp_socket):
        udp_socket.close()

    """
        we use 'three way hand shake' method to make sure the server is listening
        this function makes sure the udp is a little bit more reliable
    """

    def check_reliablity(self):
        time.sleep(0.25)
        try:
            self.udp_socket.sendto("ACK".encode(), self.udp_address)
            msg = self.udp_socket.recvfrom(MSG_SIZE)[0]
            if msg.decode() == "SYN":
                self.udp_socket.sendto("ACK".encode(), self.udp_address)
                return True
        except:
            return False
