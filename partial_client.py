import socket
import time
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=14350)
    parser.add_argument("--host", type=str, default="localhost")

    args = parser.parse_args()

    parts = [
        b"AD",
        b"D 1",
        b" 2\n"
    ]

    with socket.create_connection((args.host, args.port)) as s:
        for chunk in parts:
            s.sendall(chunk)
            time.sleep(0.5)

        response = s.recv(1024)
        print("Server response:", response.decode().strip())