from __future__ import annotations

import logging

import rtde_control
import rtde_receive

import asyncio

from backend.devices.device_abc import AbstractConnector, ABCRobotCommand

logger = logging.getLogger(__name__)


class UrRobot(AbstractConnector):
    """
    Implementation of the UR3 robot as an AbstractConnector.
    """

    waypoints = [
        [0.0, -1.3, 0.0, -1.3, 0.0, 0.0],
        [
            0.0016515760216861963,
            -1.5747383276568812,
            0.002468585968017578,
            -1.5649493376361292,
            0.007608110550791025,
            0.0018253473099321127,
        ],
        [
            4.058738708496094,
            -0.9063304106341761,
            -0.6854398886310022,
            -6.27735418478121,
            0.5326774716377258,
            2.0456624031066895,
        ],
        [
            3.423715353012085,
            -0.3620103041278284,
            -1.4064410368548792,
            -0.7819817701922815,
            -1.2245267073260706,
            2.8527207374572754,
        ],
        [
            1.570734977722168,
            -1.5708444754229944,
            -1.57080585161318,
            -1.570820156727926,
            -1.5708907286273401,
            -1.5707791487323206,
        ],
    ]

    # connect device implementation
    async def connect_device(self):
        logger.debug("ur3: attempting receive interface connection")
        print("UR3 IP ADDRESS", self.ip_addr)
        self.receive_interface = rtde_receive.RTDEReceiveInterface(self.ip_addr)

        logger.debug("ur3: attempting control interface connection")
        self.control_interface = rtde_control.RTDEControlInterface(self.ip_addr)
        logger.debug("ur3: attempting interface connections OK")

    # specific implementations
    def retrieve_state_joint(self, _: ABCRobotCommand):
        return self.receive_interface.getActualQ()

    def general_control_call(self, general_input: ABCRobotCommand):
        # check if this works TODO
        if "string_input" not in general_input:
            raise Exception("No string input provided")

        general_control_function = getattr(
            type(self.control_interface), general_input["string_input"]
        )

        return general_control_function(self.control_interface)

    def general_receive_call(self, general_input: ABCRobotCommand):
        if "string_input" not in general_input:
            raise Exception("No string input provided")

        general_receive_function = getattr(
            type(self.receive_interface), general_input["string_input"]
        )

        return general_receive_function(self.control_interface)

    def retrieve_state_linear(self, general_input: ABCRobotCommand):
        return self.receive_interface.getActualTCPPose()

    # NODE
    async def move_to_joint_waypoint(self, waypoint_number: int):
        logger.info(f"ur3: moving to waypoint #{waypoint_number}")
        self.control_interface.moveJ(waypoint_number, True)

    async def move(
        self,
        source_waypoint_number: int,
        destination_waypoint_number: int,
        delay_between_movements: float,
    ) -> None:
        logger.info(f"move: moving to source waypoint {source_waypoint_number}")
        self.control_interface.moveJ(self.waypoints[source_waypoint_number], True)
        logger.info(
            f"move: move to source ({source_waypoint_number}) completed, waiting {delay_between_movements} seconds..."
        )
        await asyncio.sleep(delay_between_movements)
        logger.info(
            f"move: moving to destination waypoint {destination_waypoint_number}"
        )
        self.control_interface.moveJ(self.waypoints[destination_waypoint_number], True)
