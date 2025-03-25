import socket
import threading

# Configuration (set IP and ports for two peers)
PEER_A_IP = "127.0.0.1"  # Local IP
PEER_A_PORT = 5678        # Port for Peer A
PEER_B_IP = "127.0.0.1"  # Local IP
PEER_B_PORT = 5679        # Port for Peer B

def start_server(port):
    """ Starts a server to receive messages """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", port))
    server_socket.listen(1)
    print(f"Listening on port {port}...")
    
    conn, addr = server_socket.accept()
    print(f"Connected by {addr}")
    
    while True:
        data = conn.recv(1024)		# Receive data from the client up to 1024 bytes
        if not data:
            break
        print(f"\nReceived from {addr}: {data.decode()}")
    conn.close()

def start_client(target_ip, target_port):
    """ Sends messages to the target peer """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((target_ip, target_port))
    
    while True:
        message = input("Enter message: ")
        if message.lower() == "exit":
            print("Exiting chat...")
            break
        client_socket.sendall(message.encode())
    client_socket.close()

# Combine client and server functionality for P2P chat
def start_peer(my_port, peer_ip, peer_port):
    """ Starts a P2P peer with server and client threads """
    threading.Thread(target=start_server, args=(my_port,), daemon=True).start()
    start_client(peer_ip, peer_port)

if __name__ == "__main__":
    print("Choose Peer A or Peer B")
    choice = input("Enter A or B: ").strip().upper()
    
    if choice == "A":
        start_peer(PEER_A_PORT, PEER_B_IP, PEER_B_PORT)
    elif choice == "B":
        start_peer(PEER_B_PORT, PEER_A_IP, PEER_A_PORT)
    else:
        print("Invalid choice. Please restart and choose A or B.")
