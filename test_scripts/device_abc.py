from __future__ import annotations

#ABC
from abc import ABC, abstractmethod

#UR3
import rtde_receive
import rtde_control
import rtde_io

#xpeel
import socket
from queue import SimpleQueue

class generalized_input:
    x_position = 0
    y_position = 0
    waypoint_number = 0
    string_input = ""
    ip_add = ""
    sub_function_name = ""

class abstractConnector(ABC):

    def __init__(self,ip_addr,port):
        self.ip_addr = ip_addr
        self.port = port
        self.connect_device()

    @abstractmethod
    def connect_device(self):
        pass
    
    def call_node_interface(self,node_name,relevant_data):
        """
        The method with which the orchestrator will call the robot. It will send an "action" to perform

        # if the node function call has output then it will return it
        """

        node_function:function = getattr(self.__class__, node_name)

        data_output = node_function(self,relevant_data)

        if data_output:
            return data_output
        else:
            return None

class UR_Robot(abstractConnector):
    
    waypoint_J1 = [0.0, -1.3, 0.0, -1.3, 0.0, 0.0]
    waypoint_J2 = [0.0016515760216861963, -1.5747383276568812, 0.002468585968017578, -1.5649493376361292, 0.007608110550791025, 0.0018253473099321127]
    waypoints = [waypoint_J1,waypoint_J2]

    #connect device implementation
    def connect_device(self):
        print("attempting receive interface connection")
        self.receive_interface = rtde_receive.RTDEReceiveInterface(self.ip_addr)
        
        print("attempting control interface connection")
        self.control_interface = rtde_control.RTDEControlInterface(self.ip_addr)

    #specific implementations
    def retrieve_state_joint(self,general_input):
        return self.receive_interface.getActualQ()

    def general_control_call(self,general_input):
        #check if this works TODO
        general_control_function = getattr(type(self.control_interface), general_input.string_input)

        return general_control_function(self.control_interface)
    
    def general_receive_call(self,general_input):
        #check if this works TODO
        general_receive_function = getattr(type(self.receive_interface), general_input.string_input)

        return general_receive_function(self.control_interface)

    def retrieve_state_linear(self,general_input:generalized_input):
        return self.receive_interface.getActualTCPPose()
    
    def move_J_waypoint(self,general_input):

        #target = [0.0, -1.3, 0.0, -1.3, 0.0, 0.0]

        target = self.waypoints[general_input.waypoint_number]
        print(f"moving to {target}")
        self.control_interface.moveJ(target,True)


class XPeelConnector(abstractConnector):
    def connect_device(self):
        self.sock_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_conn.connect((self.ip_addr, self.port))
        self.recv_queue = SimpleQueue()
        print(f"Connected on {self.ip_addr}:{self.port}!")

    #helper method. not to be directly called
    def send(self, data: str):
        self.sock_conn.sendall((data + "\r\n").encode())

    #helper method. Not to be called 
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
    
    def waive_ack(self):
        while True:
            msg = self.recv()
            if msg is None or msg[1:4] == "ack":
                continue

            return msg

    def status(self,general_input):
        self.send("*stat")
        return self.recv()

    def reset(self,general_input):
        self.send("*reset")
        return self.waive_ack()

    def seal_check(self,general_input):
        self.send("*sealcheck")
        return self.waive_ack()

    def tape_remaining(self,general_input):
        self.send("*tapeleft")
        print("sent tape cmd")
        while True:
            msg = self.recv()
            if 'tape' in msg[1:5]:
                return msg

    # def peel(self, param, adhere):
    #     self.send(f"*xpeel:{param}{adhere}")
    #     return self.waive_ack()

    def disconnect(self,general_input):
        self.sock_conn.close()







# device_ip = "192.168.0.205"
# my_robot = UR_Robot(device_ip,None)

# print(my_robot.call_node_interface("retrieve_state_joint",None))

# call_input = generalized_input()
# call_input.waypoint_number =0
# call_input.string_input = "isSteady"

# my_robot.call_node_interface("move_J_waypoint",call_input)

# if my_robot.call_node_interface("general_control_call",call_input):
#     print("robot is steady")
# else:
#     print("robot is unsteady")

# call_input.waypoint_number = 1
# my_robot.call_node_interface("move_J_waypoint",call_input)
call_input = generalized_input()

xpeel = XPeelConnector("192.168.0.201", 1628)
print("device connection class created.")
data = xpeel.call_node_interface("seal_check",call_input)
print(f"Recieved {data} from xpeel")
xpeel.call_node_interface("disconnect",call_input)
print('connection closed.')
