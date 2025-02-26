import rtde_receive
import rtde_control
import rtde_io
from backend.device_abc import generalized_input

class UR3_test_controller_1:
    device_ip = "192.168.0.205"

    waypoint_J1 = [0.0, -1.3, 0.0, -1.3, 0.0, 0.0]
    waypoint_J2 = [0.0016515760216861963, -1.5747383276568812, 0.002468585968017578, -1.5649493376361292, 0.007608110550791025, 0.0018253473099321127]

    waypoints = [waypoint_J1,waypoint_J2]
    def __init__(self,ip_addr):
        #ip_addr = "192.168.0.205"
        print("Initializing robot")
        print("attempting receive interface connection")
        self.receive_interface = rtde_receive.RTDEReceiveInterface(ip_addr)
        

        print("attempting control interface connection")
        self.control_interface = rtde_control.RTDEControlInterface(ip_addr)
    
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

    
    #the public interface
    #mappings = {"retrieve_state_joint":retrieve_state_joint,"retrieve_state_linear":retrieve_state_linear}
    def call_node_interface(self,node_name,relevant_data):
        """
        The method with which the orchestrator will call the robot. It will send an "action" to perform

        # if the node function call has output then it will return it
        """

        node_function:function = getattr(UR3_test_controller_1, node_name)

        data_output = node_function(self,relevant_data)

        if data_output:
            return data_output
        else:
            return None

my_robot = UR3_test_controller_1()

print(my_robot.call_node_interface("retrieve_state_joint",None))

call_input = generalized_input()
call_input.waypoint_number =0
call_input.string_input = "isSteady"

my_robot.call_node_interface("move_J_waypoint",call_input)

if my_robot.call_node_interface("general_control_call",call_input):
    print("robot is steady")
else:
    print("robot is unsteady")

call_input.waypoint_number = 1
my_robot.call_node_interface("move_J_waypoint",call_input)
