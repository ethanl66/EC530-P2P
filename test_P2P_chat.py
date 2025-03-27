import socket
import threading
import json
import os
from P2P_chat import *

def test_save_peer():
    save_peer("127.0.0.1", 1234)
    peers = load_peers()
    assert peers == {'127.0.0.1:1234': {'ip': '127.0.0.1', 'port': 1234}}

def test_remove_peer():
    remove_peer("127.0.0.1", 1234)
    peers = load_peers()
    assert peers == {}

def test_send_rcv_msg():
    """Test sending and receiving a message between client and server."""
    # Start the client in a separate thread
    def client_thread():
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("127.0.0.1", 5678))
        client_socket.sendall(b"Hello, Server!")
        client_socket.close()

    client = threading.Thread(target=client_thread, daemon=True)
    client.start()

    # Simulate server receiving the message
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 5678))
    server_socket.listen(1)
    conn, addr = server_socket.accept()
    data = conn.recv(1024)
    assert data == b"Hello, Server!"
    conn.close()
    server_socket.close()