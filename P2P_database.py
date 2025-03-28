import socket
import threading
import json
import os
import time		# for sleep()
import sys		# for exit()
from datetime import datetime 	# for timestamp
import sqlite3
import queue

debug_prints = True
messages_in_queue = False
messages_in_queue_queue = queue.Queue()		# Shared queue

# Discovery: Add self to list of peers
PEERS_FILE = "peers.json"

def load_peers():
    """Loads the list of peers from the JSON file."""
    if not os.path.exists(PEERS_FILE):
        return {}
    try:
        with open(PEERS_FILE, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        print(f"Error: Failed to parse {PEERS_FILE}.")
        return {}
    
def save_peer(ip, port):
    """Adds a new peer to the JSON file"""
    peers = load_peers()
    peer_key = f"{ip}:{port}"   # Use IP:Port as the key
    
    if peer_key not in peers:
        peers[peer_key] = {"ip": ip, "port": port}
        with open(PEERS_FILE, "w") as file:
            json.dump(peers, file, indent=4)
        if debug_prints:
            print(f"Peer {peer_key} added to {PEERS_FILE}.")
    else:
        if debug_prints:
            print(f"Peer {peer_key} already exists in {PEERS_FILE}.")

def remove_peer(ip, port):
    """Removes a peer from the JSON file."""
    peers = load_peers()
    peer_key = f"{ip}:{port}"  # Use IP:Port as the unique key

    if peer_key in peers:
        del peers[peer_key]
        with open(PEERS_FILE, "w") as file:
            json.dump(peers, file, indent=4)
        print(f"Peer {peer_key} removed from {PEERS_FILE}.")
    else:
        print(f"Peer {peer_key} not found in {PEERS_FILE}.")

# Data Storage
def start_db(ip, port, database="messages.db"):
    """ Connects to db and creates/adds to table of received and queued messages"""
    con = sqlite3.connect(database)	# Create connection to db, create if doesn't exist
    cur = con.cursor()						# Create cursor object to execute SQL commands
    table_name = f"{ip.replace('.', '_')}_{port}"  # Replace dots in IP with underscores for valid table name
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS Peer_{table_name}(
			id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,			-- Received or Queued
			source TEXT NOT NULL,
			dest TEXT NOT NULL,
			timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
			message TEXT NOT NULL
		)""")
    con.commit()
    con.close()
    
def save_message (type, src_ip, src_port, dest_ip, dest_port, message, database="messages.db"):
    """ Connect to db, open correct table, save message (received or queued) """
    con = sqlite3.connect(database)	
    cur = con.cursor()						
    if type == "received":
        table_name = f"{dest_ip.replace('.', '_')}_{dest_port}"
    elif type == "queued":
        table_name = f"{src_ip.replace('.', '_')}_{src_port}"  
    source = f"{src_ip}:{src_port}"
    dest = f"{dest_ip}:{dest_port}"
    cur.execute(f"INSERT INTO Peer_{table_name} (type, source, dest, message) VALUES (?, ?, ?, ?)", (type, source, dest, message))
    con.commit()
    con.close()


# Session Initiation: Start peer thread

def start_client(ip, port, my_ip, my_port):
    """ Sends messages to the target peer """
    global messages_in_queue
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket.connect((ip, port))
    # Send special message to peer to check if connection is live
    # client_socket.sendall(f"ping from {my_ip}:{my_port}".encode())
    current_utc_time = datetime.now()
    formatted_datetime = current_utc_time.strftime("%Y-%m-%d %H:%M:%S")

    while True:
        """ if messages_in_queue:
            send_queued_messages(client_socket, my_ip, my_port)	# Check for queued messages to send
            messages_in_queue = False """
        if not messages_in_queue_queue.empty():
            signal = messages_in_queue_queue.get()
            if signal == "send_queued_messages":
                send_queued_messages(client_socket, my_ip, my_port)
        message = input(f"{formatted_datetime} <You>: ")
        try:
            client_socket.sendall(message.encode())
        except Exception as e:
            save_message("queued", my_ip, my_port, ip, port, message)
            if debug_prints:
                # print("Saving message to send later...")
                pass
        except KeyboardInterrupt:
            print("Exiting...")
            client_socket.close()
            remove_peer(ip, port)

def start_server(ip, port):
    """ Starts a server to receive messages """
    global messages_in_queue
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", port))
    server_socket.listen(10)
    print(f"Listening on port {port}...")
    # Connect to db and create new table on server start (when you start listening for messages)
    start_db(ip, port)
    conn, addr = server_socket.accept()
    print(f"Connected by {addr}")
    # Check connection is live. 
	# If live, check db for queued messages
	# If queued messages, send them and display on server side and client side
    #threading.Thread(target=send_queued_messages, args=(ip, port), daemon=True).start()	# Start thread to send queued messages
    messages_in_queue = True
    messages_in_queue_queue.put("send_queued_messages")

    while True:
        data = conn.recv(1024)		# Receive data from the client up to 1024 bytes
        if not data:
            break
        current_utc_time = datetime.now()
        formatted_datetime = current_utc_time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{formatted_datetime} \nReceived from {addr}: {data.decode()}")
    conn.close()
    
def start_peer(ip, port, dest_ip, dest_port):
    """ Starts a peer thread to listen for incoming messages and send messages. """
    threading.Thread(target=start_server, args=(ip, port), daemon=True).start()
    start_db(ip, port)
    start_client(dest_ip, dest_port, ip, port)
    
# Communications Synchronization
def send_queued_messages(client_socket, ip, port):
    # Open database table, get all queued messages, send them, soft delete from db
    con = sqlite3.connect('messages.db')
    cur = con.cursor()
    table_name = f"{ip.replace('.', '_')}_{port}"
    cur.execute(f"SELECT * FROM Peer_{table_name} WHERE type='queued'")
    queued_messages = cur.fetchall()
    if queued_messages == []:
        if debug_prints:
            print("No queued messages to send.")
        return
    if debug_prints:
        print(f"Sending queued messages...")
    for message in queued_messages:
        try:
            source_ip, source_port = message[2].split(":")
            dest_ip, dest_port = message[3].split(":")
            source_port = int(source_port)
            dest_port = int(dest_port)
            message_text = message[5]
            if debug_prints:
                print(f"Sending message {message_text} to {dest_ip}:{dest_port}")
            
            #client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #client_socket.connect((dest_ip, dest_port))
            client_socket.sendall(message_text.encode())
            # cur.execute(f"DELETE FROM Peer_{table_name} WHERE id = ?", (message[0], ))
            if debug_prints:
                print("Updating database message status...")
            cur.execute(f"UPDATE Peer_{table_name} SET type='sent' WHERE id=?", (message[0],))		# soft delete
            con.commit()
            #client_socket.close()
        except Exception as e:
            if debug_prints:
                print(f"Failed to send message {message[5]} to {ip}:{port}. Error: {e}")
    con.close()


if __name__ == "__main__":
    try:
        print("Choose IP and port to send from:")
        my_ip = input("Enter IP: ").strip()
        my_port = int(input("Enter port: ").strip())
        # Add self to peers.json
        save_peer(my_ip, my_port)
        threading.Thread(target=start_server, args=(my_ip, my_port), daemon=True).start()
        print("At any time, press Ctrl+C to exit.")

        time.sleep(1)
        print("\nCurrent peers in the network:")
        peers = load_peers()
        for peer_key, info in peers.items():
            print(f"{peer_key}: {info}")
        if len(peers) == 1:
            print("You are the only peer in the network. Waiting for others to join...")
            while True:
                # Every 4 seconds, scan for new peers. If new, print them and continue session init sequence. 
                time.sleep(2)
                peers = load_peers()
                if len(peers) > 1:  # More than one peer in the network
                    print("New peers detected in the network:")
                    for peer_key, info in peers.items():
                        print(f"{peer_key}: {info}")
                    break
        print("Who do you want to connect to?")
        peer_ip = input("Enter IP: ").strip()
        peer_port = int(input("Enter port: ").strip())
        #start_peer(my_ip, my_port, peer_ip, peer_port)
        start_client(peer_ip, peer_port, my_ip, my_port)
    except ConnectionResetError:
        print("Connection with peer has been lost. Exiting...")
        # Add messages to database to send later
        remove_peer(my_ip, my_port)
        sys.exit()
    except Exception as e:
        print(f"An unexpected error occured: {e}")
        remove_peer(my_ip, my_port)
        sys.exit()
    except:
        print("Exiting...")
        remove_peer(my_ip, my_port)
        sys.exit()

