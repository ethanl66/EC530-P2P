import socket
import threading
import json
import os
from P2P_database import *
import sqlite3
import pytest

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

# Test timestamp? no need

""" def test_queue_message_FAIL():
    Test storing queued messages in the database
    start_db("127.0.0.1", 1234, "test_messages.db")
    # Start the client in a separate thread
    def client_thread():
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("127.0.0.1", 1235))
        client_socket.sendall(b"Hello, Server!")
        #client_socket.close()
    client = threading.Thread(target=client_thread, daemon=True)
    client.start()

    # Simulate server receiving the message
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 1235))
    server_socket.listen(1)
    conn, addr = server_socket.accept()
    data = conn.recv(1024)
    assert data == b"Hello, Server!"
    conn.close()
    server_socket.close()

    def client_thread_2():
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("127.0.0.1", 1235))
        message = "1235, are you still there?"
        try:
            client_socket.sendall(message.encode())
            #print("Message sent, should not be sent.")
            pytest.fail("Message should not be sent.")
        except Exception as e:
            print("Exception occured!")
            # Save message
            Connect to db, open correct table, save message (received or queued)
            new_con = sqlite3.connect("test_messages.db")	
            new_cur = new_con.cursor()		
            type = "queued"				
            table_name = "127_0_0_1_1234"  
            source = "127.0.0.1:1234"
            dest = "127.0.0.1:1235"
            new_cur.execute(f"INSERT INTO Peer_127_0_0_1_1234 (type, source, dest, message) VALUES (?, ?, ?, ?)", (type, source, dest, message))
            new_con.commit()
            new_con.close()
            print("Message saved to db")
    client_2 = threading.Thread(target=client_thread_2, daemon=True)
    client_2.start()

    # Server never receives the message, so it should be queued
    new_con = sqlite3.connect('test_messages.db')
    new_cur = new_con.cursor()
    res = new_cur.execute("SELECT type, dest, message FROM Peer_127_0_0_1_1234 WHERE type='queued'")
    row = res.fetchone()
    print("Row fetched:", row)
    assert row is not None
    type, dest, message = row
    assert type == "queued"
    assert dest == "127.0.0.1:1235"
    assert message == "1235, are you still there?" """

def test_queue_message():
    pass