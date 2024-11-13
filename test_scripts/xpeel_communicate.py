import socket

class deviceConnection:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port

        self.sock_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_conn.connect((addr, port))
        print(f"Connected on {addr}:{port}!")

    def send(self, data):
        self.sock_conn.sendall(data)

    def recv(self):
        while True:
            data = self.sock_conn.recv(1024)
            if not data: break
            print(data.decode())
    
    def disconnect(self):
        self.sock_conn.close()

def main():
    xpeel = deviceConnection("192.168.0.201", 1628)
    print("device connection class created.")
    xpeel.send("*stat\r\n".encode())
    print('test message sent.')
    data = xpeel.sock_conn.recv(1024)
    print(f"Recieved {data.decode()} from xpeel")
    xpeel.disconnect()
    print('connection closed.')

main()
