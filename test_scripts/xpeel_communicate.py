from __future__ import annotations

import socket
from queue import SimpleQueue


class deviceConnection:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.sock_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_conn.connect((addr, port))
        self.recv_queue = SimpleQueue()
        print(f"Connected on {addr}:{port}!")

    def send(self, data: str):
        self.sock_conn.sendall((data + "\r\n").encode())

    def recv(self) -> str | None:
        if self.recv_queue.qsize() > 0:
            return self.recv_queue.get()

        data = self.sock_conn.recv(1024).decode()
        if len(data) == 0:
            return

        # split data into list of strings
        msgs = data.split("\r\n")
        for msg in msgs:
            self.recv_queue.put(msg.strip())

        return self.recv_queue.get()

    def queue_put(self):
        pass

    def queue_get(self):
        pass

    def waive_ack(self):
        while True:
            msg = self.recv()
            if msg is None or msg[1:4] == "ack":
                continue

            return msg

    def status(self):
        self.send("*stat")
        return self.recv()

    def reset(self):
        self.send("*reset")
        return self.waive_ack()

    def seal_check(self):
        self.send("*sealcheck")
        return self.waive_ack()

    def tape_remaining(self):
        self.send("*tapeleft")
        print("sent tape cmd")
        while True:
            msg = self.recv()
            if 'tape' in msg[1:5]:
                return msg

    def peel(self, param, adhere):
        self.send(f"*xpeel:{param}{adhere}")
        return self.waive_ack()

    def disconnect(self):
        self.sock_conn.close()


def main():
    xpeel = deviceConnection("192.168.0.201", 1628)
    print("device connection class created.")
    data = xpeel.tape_remaining()
    print(f"Recieved {data} from xpeel")
    xpeel.disconnect()
    print('connection closed.')


main()
