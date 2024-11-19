import socket

class deviceConnection:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.sock_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_conn.connect((addr, port))
        self.queue = bytearray()
        print(f"Connected on {addr}:{port}!")

    def send(self, data):
        self.sock_conn.sendall(data)

    def recv(self):
        data = self.sock_conn.recv(1024).decode().strip()
        if len(data) == 0: pass
        else: return data
        
    def queue_put(self):
        pass

    def queue_get(self):
        pass

    def waive_ack(self):
        while(True):
            data = self.recv()
            if data is None: pass
            elif data[1:4] == 'ack': pass
            else: return data

    def status(self):
        self.send("*stat\r\n".encode())
        return self.recv()
    
    def reset(self):
        self.send("*reset\r\n".encode())
        return self.waive_ack()
    
    def seal_check(self):
        self.send("*sealcheck\r\n".encode())
        return self.waive_ack()
    
    def tape_remaining(self):
        self.send("*tapeleft\r\n".encode())
        print("sent tape cmd")
        while(True):
            data = self.recv()
            if 'tape' in data[1:5]: return data
            else: print(data)

    def peel(self, param, adhere):
        self.send(f"*xpeel:{param}{adhere}\r\n".encode())
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
