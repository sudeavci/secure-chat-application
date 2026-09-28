# 💬 Multi-Threaded TCP/UDP Chat Application

[![Python Version](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)]()
[![Sockets](https://img.shields.io/badge/sockets-TCP%20%2F%20UDP-orange.svg)]()

A multi-threaded client-server chat application built with Python. Features a custom Tkinter GUI, private messaging, and a fast, reliable file-transfer engine running over UDP via the Selective Repeat Algorithm.

<p align="center">
  <img src="[https://media.giphy.com/media/0SVFGSQcWrFPL0cxcQ/giphy.gif](https://media.giphy.com/media/0SVFGSQcWrFPL0cxcQ/giphy.gif)" width="600" alt="Chat Application Demo" />
</p>

---

### 💻 System Overview

This project implements a centralized server architecture that handles multiple client connections simultaneously. While standard messages flow over a stable TCP socket, file downloads use a custom-built, reliable UDP protocol to guarantee both speed and delivery success.

* **Chat Channel (TCP):** Multi-threaded connection architecture where the server generates a dedicated thread for every online user.
* **File Channel (UDP):** Implements a custom 3-Way Handshake and the Selective Repeat Algorithm to handle packet losses seamlessly without choking the main chat stream.

---

### 📁 Project Architecture

```text
FinalProject-Chat/
│
├── src/
│   ├── Client/              # Client application layer
│   │   ├── ChatGUI.py       # Tkinter user interface
│   │   ├── SocketHandler.py # Client-side dynamic socket I/O
│   │   └── RunClient.py     # Main client entry point
│   │
│   └── Server/              # Server management layer
│       ├── HandleClients.py # Request routing and multi-threading
│       ├── SocketHandler.py # Server-side socket controller
│       └── RunServer.py     # Main server bootstrap point
│
├── .gitignore
└── README.md

🚀 Getting Started
Prerequisites
Python 3.10+
GUI Dependencies:
  Windows: pip install tk
  Linux: sudo apt-get install python-tk

How to Run
Start the Server:
python3 RunServer.py

Launch the Client:
python3 RunClient.py

Simulate Concurrency (Optional):
python3 RunMultipleClients.py


🎨 In-App TerminalCommands
Command                Action
/users                 Lists all online members in the chatroom.
/files                 Fetches downloadable files hosted on the server.
/whisper <name> <msg>  Sends a private direct message to a specific user.
/disconnectTerminals   the app session and closes sockets safely.

Original implementation codebase structured by Ori Howard.
