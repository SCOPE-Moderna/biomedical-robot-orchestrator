from backend.devices.ur_robot import UrRobot
from backend.devices.xpeel import XPeelConnector

"""
This file contains a dictionary that maps instrument types from the database to their respective instrument classes.
The keys in the dictionary are the instrument types, and the values are the corresponding classes.
This dictionary is used in the orchestrator to create instances of the appropriate instrument class based on the instrument type.
This dictionary should contain all of the instruments in the database.
"""

device_dict = {"XPeel": XPeelConnector, "UrRobot": UrRobot}
