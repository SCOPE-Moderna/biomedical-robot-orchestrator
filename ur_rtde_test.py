import rtde_receive
import rtde_control

"""

#commands to fix nonstatic ip

(UR3_tests) lwitten@lwitten-Precision-3551:~/repos/biomedical-robot-orchestrator$ sudo ip addr add 192.168.1.1/24 dev eno2
(UR3_tests) lwitten@lwitten-Precision-3551:~/repos/biomedical-robot-orchestrator$ ping 192.168.1.10

repo:
https://sdurobotics.gitlab.io/ur_rtde/examples/examples.html#basic-use

pip3 install ur_rtde
"""


print("attempting receive interface")
rtde_r = rtde_receive.RTDEReceiveInterface("192.168.1.10")
print("attempting retrieve jointstates")
actual_q = rtde_r.getActualQ()
print(f"jointstates {actual_q}")

print("about to move robot")
rtde_c = rtde_control.RTDEControlInterface("192.168.1.10")
print("connected to robot move interface")
#rtde_c.moveL([-0.143, -0.435, 0.20, -0.001, 3.12, 0.04], 0.5, 0.3)

#joint_command = [0.0, -1.3, 0.0, -1.3, 0.0, 0.0]
joint_command = [0.0016515760216861963, -1.5747383276568812, 0.002468585968017578, -1.5649493376361292, 0.007608110550791025, 0.0018253473099321127]

rtde_c.moveJ(joint_command)
