### NOTE: Run this in the command-line as,
###
###     python3 socket_echo_server.py
###

import socket
import selectors
import types
import random
import argparse

sel = selectors.DefaultSelector()

def accept_wrapper(sock: socket.socket):
    """
    Wrapper function for accepting a new connection.
    """
    connection, client_address = sock.accept()
    print('Accepted connection from ', client_address)
    connection.setblocking(False)
    data = types.SimpleNamespace(
        addr=client_address,
        inb=b"",
        outb=b"",
        closing=False,
        hist=[]
    )
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(connection, events, data=data)

def service_connection(key: selectors.SelectorKey, mask):
    sock: socket.socket = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(16)
        if recv_data:
            data.inb += recv_data # Store raw stream

            while b"\n" in data.inb:
                msg, data.inb = data.inb.split(b"\n", 1)

                response = process_req(msg, data.hist)  # Process
                data.outb += (response[0] + "\n").encode()

                if response[1]: # Sets connection to close
                    data.closing = True
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(f"Echoing {data.outb!r} to {data.addr}")
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]
        if data.closing and not data.outb:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()

def process_req(msg: str, hist : list[str]):
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

    def success(result: str, closing: bool = False) -> tuple[str,bool]:
        return f"OK {result}\r", closing
    def error(message: str, closing: bool = False) -> tuple[str,bool]:
        return f"ERR {message}\r", closing
    def valid_param_count(count: int, exact: bool = True) -> bool:
        if not exact:
            return len(params.split(" ")) < count
        return params == "" if count == 0 else len(params.split(" ")) == count and params != ""
    def invalid_param_count_error(command: str):
        return error(f"Invalid number of arguments to {command}")
    def upd_hist(log: str):
        hist.append(log)
        if len(hist) > 5:
            hist.pop(0)
    def parse_int(param: str):
        try:
            res = int(param)
            return res
        except Exception as e:
            return "ERR"

    msg = msg.decode().strip()
    parts = msg.split(" ", 1)
    command = parts[0]
    params = parts[1] if len(parts) > 1 else ""

    if command in ["ADD","SUB","MUL","DIV"]:
        if not valid_param_count(2):
            return invalid_param_count_error(command)
        param1, param2 = params.split(" ")

        param1_parsed = parse_int(param=param1)
        param2_parsed = parse_int(param=param2)

        if param1_parsed == "ERR":
            return error(f"{param1} is not an integer.")
        if param2_parsed == "ERR":
            return error(f"{param2} is not an integer.")

        if param2_parsed == 0 and command == "DIV":
            return error(f"Division by 0.")

        if command == "ADD":
            res = param1_parsed + param2_parsed
        elif command == "SUB":
            res = param1_parsed - param2_parsed
        elif command == "MUL":
            res = param1_parsed * param2_parsed
        else:
            res = param1_parsed // param2_parsed
        
        upd_hist(f"{command} {param1_parsed} {param2_parsed} -> {res}")

        return success(f"{res}")

    elif command == "RND":
        if not valid_param_count(1):
            return invalid_param_count_error(command)
        param = parse_int(params)
        if param == "ERR":
            return error(f"{params} is not an integer.")
            
        if param < 1:
            return error(f"{param} is lesser than 1. Argument integer must be larger than  1.")

        res = random.randint(1,param)

        upd_hist(f"{command} {param} -> {res}")

        return success(f"{res}")

    elif command == "HIST":
        if not valid_param_count(0):
            return invalid_param_count_error(command)

        res = "\r\n".join(hist)
        return success("The last valid operations from this session (up to 5) are:\r\n" + res)

    elif command == "HELP":
        if not valid_param_count(2, exact=False):
            return invalid_param_count_error(command)
        if params == "":
            lines = [
                "The following commands are available:",
                "ADD <N1> <N2> - to add N1 and N2",
                "SUB <N1> <N2> - to subtract N2 from N1",
                "MUL <N1> <N2> - to multiply N1 by N2",
                "DIV <N1> <N2> - to divide N1 by N2",
                "RND <N> - to generate a random number between 1 and N, inclusive",
                "HIST - to show the last 5 valid operations in the session",
                "HELP [command] - to display syntax and semantics of a specific command.",
                "If no command is specified, it will display all available commands and meanings",
                "QUIT - to end the current session of the arithmetic server"
            ]
            help_msg = "\r\n".join(lines)
            return success(help_msg)

        if params not in ["ADD","SUB","MUL","DIV","RND","HIST","HELP","QUIT"]:
            return error(f"INVALID COMMAND NAME. USE \'HELP\' TO LIST ALL VALID COMMANDS.")

        if params == "ADD":
            res = "ADD <N1> <N2> - to add N1 and N2"
        elif params == "SUB":
            res = "SUB <N1> <N2> - to subtract N2 from N1"
        elif params == "MUL":
            res = "MUL <N1> <N2> - to multiply N1 by N2"
        elif params == "DIV":
            res = "DIV <N1> <N2> - to divide N1 by N2"
        elif params == "RND":
            res = "RND <N> - to generate a random number between 1 and N, inclusive"
        elif params == "HIST":
            res = "HIST - to show the last 5 valid operations in the session"
        elif params == "HELP":
            res = "HELP [command] - to display syntax and semantics of a specific command. \r\n If no command is specified, it will display all available commands and meanings"
        elif params == "QUIT":
            res = "QUIT - to end the current session of the arithmetic server"
        
        return success(res)

    elif command == "QUIT":
        if not valid_param_count(0):
            return invalid_param_count_error(command)
        return success("bye", closing=True)

    else:
        return error(f"Unknown operation {command}.")

if __name__ == "__main__":

    # Create a TCP/IP socket
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=14350)
    args = parser.parse_args()

    # Bind the socket to the port
    server_address = ('127.0.0.1', args.port)
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