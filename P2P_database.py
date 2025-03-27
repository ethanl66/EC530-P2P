import socket
import threading
import json
import os
import time		# for sleep()
import sys		# for exit()
from datetime import datetime 	# for timestamp

debug_prints = True

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


# Session Initiation: Start peer thread
def start_client(ip, port):
    """ Sends messages to the target peer """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((ip, port))
    current_utc_time = datetime.now()
    formatted_datetime = current_utc_time.strftime("%Y-%m-%d %H:%M:%S")

    while True:
        message = input(f"{formatted_datetime} <You>: ")
        try:
            client_socket.sendall(message.encode())
        except KeyboardInterrupt:
            print("Exiting...")
            client_socket.close()
            remove_peer(ip, port)

def start_server(ip, port):
    """ Starts a server to receive messages """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", port))
    server_socket.listen(10)
    print(f"Listening on port {port}...")
    conn, addr = server_socket.accept()
    print(f"Connected by {addr}")

    while True:
        data = conn.recv(1024)		# Receive data from the client up to 1024 bytes
        if not data:
            break
        current_utc_time = datetime.now()
        formatted_datetime = current_utc_time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{formatted_datetime} Received from {addr}: {data.decode()}")
    conn.close()
    
def start_peer(ip, port, dest_ip, dest_port):
    """ Starts a peer thread to listen for incoming messages and send messages. """
    threading.Thread(target=start_server, args=(ip, port), daemon=True).start()
    start_client(dest_ip, dest_port)

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
        start_client(peer_ip, peer_port)
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

