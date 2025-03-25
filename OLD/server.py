"""
	python3 server.py 127.0.0.1 12345
"""


# Server side of chat room
import socket
import select
import sys
from _thread import *

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Check if correct number of arguments are passed
if len(sys.argv) != 3:
	print("Correct usage: script, IP address, port number")
	exit()

# Get IP address and port number
IP_address = str(sys.argv[1])
Port = int(sys.argv[2])

# Bind the server to the IP address and port number
server.bind((IP_address, Port))

# Listen for 100 active connections
server.listen(100)

list_of_clients = []

def clientthread(conn, addr):
	# Send welcome message to newly connected client
	conn.send("Welcome to this chatroom!".encode())

	while True:
		try:
			message = conn.recv(2048)
			if message:
				# Print message received from client
				print("<" + addr[0] + "> " + message.decode())

				# Calls broadcast function to send message to all clients
				message_to_send = "<" + addr[0] + "> " + message.decode()
				broadcast(message_to_send, conn)
			else:
				remove(conn)

		except:
			continue

# Broadcast message to all clients
def broadcast(message, connection):
	for clients in list_of_clients:
		if clients != connection:
			try:
				clients.send(message.encode())
			except:
				clients.close()
				# If connection is broken, remove the client
				remove(clients)

# Remove client from list of clients
def remove(connection):
	if connection in list_of_clients:
		list_of_clients.remove(connection)

while True:
	# Accept new connection and store sockt object and address
	conn, addr = server.accept()

	# Append new connection to list of clients
	list_of_clients.append(conn)

	# Print address of new connection
	print(addr[0] + " connected")

	# Create new thread for new connection
	start_new_thread(clientthread, (conn, addr))

conn.close()
server.close()