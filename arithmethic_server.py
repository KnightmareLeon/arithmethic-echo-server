### NOTE: Run this in the command-line as,
###
###     python3 socket_echo_server.py
###

import socket
import sys
import selectors
import types

sel = selectors.DefaultSelector()

def accept_wrapper(sock):
    connection, client_address = sock.accept()
    print('Accepted connection from ', client_address)
    connection.setblocking(False)
    data = types.SimpleNamespace(addr=client_address, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(connection, events, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(16)
        if recv_data:
            data.outb += recv_data
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(f"Echoing {data.outb!r} to {data.addr}")
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]

# Create a TCP/IP socket
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('127.0.0.1', 14350)
print('starting up on {} port {}'.format(*server_address))
lsock.bind(server_address)

# Listen for incoming connections
lsock.listen()

lsock.setblocking(False)

sel.register(lsock, selectors.EVENT_READ, data=None)

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                service_connection(key,mask)
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close()