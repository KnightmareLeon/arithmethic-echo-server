import socket
import time
import statistics
import argparse

def sequential_client(s):
    rtts = []

    for _ in range(1000):
        start = time.perf_counter()

        s.sendall(b"ADD 1 2\n")

        data = b""
        while not data.endswith(b"\n"):
            data += s.recv(1024)

        end = time.perf_counter()
        rtts.append((end - start) * 1000)

    print("Mean RTT (ms):", statistics.mean(rtts))
    print("Median RTT (ms):", statistics.median(rtts))


def pipelined_client(s):
    start = time.perf_counter()

    # send all requests
    for _ in range(1000):
        s.sendall(b"ADD 1 2\n")

    buffer = b""
    count = 0

    while count < 1000:
        chunk = s.recv(4096)
        if not chunk:
            raise RuntimeError("Connection closed early")

        buffer += chunk

        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            if line:
                count += 1

    end = time.perf_counter()

    elapsed = end - start

    print("Total time (ms):", elapsed * 1000)
    print("Throughput (ops/sec):", 1000 / elapsed)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=14350)
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--mode", choices=["sequential", "pipeline"], required=True)

    args = parser.parse_args()

    with socket.create_connection((args.host, args.port)) as s:
        s.settimeout(5)

        if args.mode == "sequential":
            sequential_client(s)
        else:
            pipelined_client(s)