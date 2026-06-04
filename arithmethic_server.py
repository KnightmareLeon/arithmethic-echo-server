### NOTE: Run this in the command-line as,
###
###     python3 socket_echo_server.py
###

import socket
import sys
import selectors
import types
import random

sel = selectors.DefaultSelector()

commands = ["ADD","SUB","MUL","DIV","RND","HIST","HELP","QUIT"]

def accept_wrapper(sock: socket.socket):
    """
    Wrapper function for accepting a new connection.
    """
    connection, client_address = sock.accept()
    print('Accepted connection from ', client_address)
    connection.setblocking(False)
    data = types.SimpleNamespace(addr=client_address, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(connection, events, data=data)

def service_connection(key: selectors.SelectorKey, mask):
    sock: socket.socket = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(16)
        if recv_data:
            data.inb += recv_data #Store raw stream

            while b"\n" in data.inb:
                msg, data.inb = data.inb.split(b"\n", 1)

                processed = process_req(msg)   # 👈 PROCESS HERE
                data.outb += processed + b"\n"

        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(f"Echoing {data.outb!r} to {data.addr}")
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]

def process_req(msg: str):
    """"
    Process a client's request for the server.\n

    Client Requests: \n
    ADD <N1> <N2> ->       Add N1 and N2. \n
    SUB <N1> <N2> ->       Subtract N2 from N1. \n
    MUL <N1> <N2> ->       Multiply N1 by N2. \n
    DIV <N1> <N2> ->       Integer-divide N1 by N2. \n
    RND <N> ->             Return a random integer in [1, N]. \n
    HIST ->                Show up to the last 5 valid operations for this connection only. \n
    HELP ->                [command] Show all commands, or detailed help for one command. \n
    QUIT ->                End the session. \n

    Client requests that are successfully processed will return \"OK \<result\>\", otherwise
    \"ERR \<message\>\".
    """

    def success(result: str) -> str:
        return f"OK {result}"
    def error(message: str) -> str:
        return f"ERR {message}"
    def parse_int(param: str):
        try:
            res = int(param)
            return res
        except Exception as e:
            return "ERR"

    command, params = msg.split(" ", 1)

    res = ""
    if command == "ADD":
        if len(params.split(" ")) != 2:
            return error(f"{command} NEEDS EXACTLY TWO PARAMETERS.")
        param1, param2 = params.split(" ")
    elif command == "SUB":
        if len(params.split(" ")) != 2:
            return error(f"{command} NEEDS EXACTLY TWO PARAMETERS.")
        param1, param2 = params.split(" ")
    elif command == "MUL":
        if len(params.split(" ")) != 2:
            return error(f"{command} NEEDS EXACTLY TWO PARAMETERS.")
        param1, param2 = params.split(" ")
    elif command == "DIV":
        if len(params.split(" ")) != 2:
            return error(f"{command} NEEDS EXACTLY TWO PARAMETERS.")
        param1, param2 = params.split(" ")
    elif command == "RND":
        if len(params.split(" ")) != 1:
            return error(f"{command} NEEDS EXACTLY ONE PARAMETER.")
        param = parse_int(params)
        if param == "ERR":
            return error(f"{param} IS NOT AN INTEGER.")
            
        if param < 1:
            return error(f"{param} IS LESSER THAN 1. INTEGER MUST BE LARGER THAN 1.")

        res = f"{random.randint(1,param)}"

    elif command == "HIST":
        if len(params.split(" ")) != 0:
            return error(f"{command} NEEDS NO PARAMETER.")
    elif command == "HELP":
        if len(params.split(" ")) > 1:
            return error(f"{command} NEEDS ONE OR NO PARAMETER.")
    elif command == "QUIT":
        if len(params.split(" ")) != 0:
            return error(f"{command} NEEDS NO PARAMETER.")
    else:
        return error(f"INVALID COMMAND: <{command}>. USE \'HELP\' TO LIST ALL VALID COMMANDS.")
        
    return res
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