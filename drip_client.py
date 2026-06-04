import socket
import time
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=14350)
    parser.add_argument("--host", type=str, default="localhost")

    args = parser.parse_args()

    s = socket.create_connection((args.host, args.port))

    msg = b"ADD 1 2\n"

    for b in msg:
        s.send(bytes([b]))
        time.sleep(0.3)

    print(s.recv(1024).decode())
    s.close()