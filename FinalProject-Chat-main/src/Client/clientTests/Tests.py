import multiprocessing
import time
from unittest import TestCase

from Client import Client
from FakeServer import FakeServer
from SocketHandler import SocketHandler

"""
those tests check both the client and the server and the communication between them
the FakeServer has the same functions as the original one
The GUI is tested as well with error messages
"""


class Tests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = FakeServer()
        cls.first_user = Client("Ori")
        cls.second_user = Client("Avi")
        cls.server_thread = multiprocessing.Process(target=cls.server.start, daemon=True)
        cls.server_thread.start()

    def test_connect(cls):
        cls.first_user.connect()
        time.sleep(0.1)
        cls.assertTrue(cls.first_user.is_connected())
        cls.first_user.disconnect()
        time.sleep(0.5)

    def test_disconnect(cls):
        cls.first_user.connect()
        cls.first_user.disconnect()
        time.sleep(0.1)
        cls.assertFalse(cls.first_user.is_connected())
        time.sleep(0.5)

    def test_set_username(cls):
        cls.first_user.connect()
        time.sleep(0.1)
        cls.first_user.set_username("Shlomi")
        cls.assertEqual("Shlomi", cls.first_user.user_name)
        cls.first_user.set_username("Ori")
        cls.assertEqual("Ori", cls.first_user.user_name)

    def test_get_commands(cls):
        cls.second_user.connect()
        time.sleep(0.1)
        try:
            junk = SocketHandler.get_msg(cls.second_user.tcp_socket)
        except:
            print()
        cls.second_user.get_commands()
        time.sleep(0.1)
        commands = SocketHandler.get_msg(cls.second_user.tcp_socket)
        expected = "SERVER:\n" \
                   "/users - get a list of all connected users\n" \
                   "/disconnect - disconnect from chat\n" \
                   "/files - get a list of all the files\n" \
                   "/whisper <client name> <msg> - send a private message to another user"
        cls.assertEqual(expected, commands)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server_thread.terminate()
