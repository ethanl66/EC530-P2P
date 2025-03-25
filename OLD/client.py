"""
	python3 client.py 127.0.0.1 12345
"""

import socket
import select
import sys

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

if len(sys.argv) != 3:
	print("Correct usage: script, IP address, port number")
	exit()

IP_address = str(sys.argv[1])
Port = int(sys.argv[2])

try:
	server.connect((IP_address, Port))
except Exception as e:
	print("Error connecting to server: ", str(e))
	exit()

while True:
	# Maintain a list of possible input streams
	sockets_list = [sys.stdin, server]

	# Check if server socket still valid
	if server.fileno() == -1:
		print("Server socket is invalid")
		exit()

	# Get the list of sockets which are readable
	print(select(sockets_list, [], []))
	print(select.select(sockets_list, [], []))
	read_sockets, write_socket, error_socket = select.select(sockets_list, [], [])

	for socks in read_sockets:
		if socks == server:
			try:
				message = socks.recv(2048)
				if not message:
					print("Disconnected from server")
					server.close()
					exit()
				print(message.decode())
			except Exception as e:
				print(f"Error receiving message: {e}")
				server.close()
				exit()
		else:
			message = sys.stdin.readline()
			try:
				server.send(message.encode())
				sys.stdout.write("<You>")
				sys.stdout.write(message)
				sys.stdout.flush()
			except Exception as e:
				print(f"Error sending message: {e}")
				server.close()
				exit()

server.close()