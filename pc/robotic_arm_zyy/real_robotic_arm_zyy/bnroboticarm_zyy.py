#
# MIT License
#
# Copyright (c) 2025-2026 Manuel Bottini
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Robotic Arm ZYY application using a Wifi Bodynodes Host"""

import sys
import os
import time
import math
from dataclasses import dataclass
import numpy as np
import pynput


sys.path.append(
    os.path.dirname(os.path.abspath(__file__)) + "/../../../body-nodes-common/python/"
)
sys.path.append(
    os.path.dirname(os.path.abspath(__file__)) + "/../../../modules/pythonlib/"
)

import bnwifibodynodeshost  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
import bncommon  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
from bncommon import (  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
    BnConstants,
)

import Adeept  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting


bodynodes_axis_config_la = {
    "new_w_sign": 1,
    "new_x_sign": 1,
    "new_y_sign": -1,
    "new_z_sign": -1,
    "new_w_val": 0,
    "new_x_val": 1,
    "new_y_val": 3,
    "new_z_val": 2,
}

bodynodes_axis_config_ua = {
    "new_w_sign": 1,
    "new_x_sign": -1,
    "new_y_sign": -1,
    "new_z_sign": 1,
    "new_w_val": 0,
    "new_x_val": 2,
    "new_y_val": 3,
    "new_z_val": 1,
}


bodynodes_robotic_arm = {
    "event": {"reset": False},
    "pin": {"servo1": 0, "servo2": 1, "servo3": 2, "servo4": 3, "servo5": 4},
}


@dataclass
class Internal:
    """Internal module data dataclass"""

    la_right_first = None
    ua_right_first = None

    la_right_last = [1, 0, 0, 0]
    ua_right_last = [1, 0, 0, 0]


internal = Internal()


def setup_communicator():
    """Setup communicator"""

    return bnwifibodynodeshost.BnWifiHostCommunicator()


def setup_robotic_arm(serial_com):
    """Setup robotic arm"""

    Adeept.com_init(serial_com, 115200, 1)
    print(f"Trying to connect to serial {serial_com}...")
    Adeept.wiat_connect()
    print(f"Connected to serial {serial_com}!")
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo1"], 9)
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo2"], 6)
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo3"], 5)
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo4"], 3)
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo5"], 11)


def setup_robot_tracker():
    """Setup robot tracker"""

    motiontrack = bncommon.BnMotionTracking_2Nodes(
        initialPosition=[0, 0, 1.5], armVector1=[0, 0, -1.2], armVector2=[1.2, 0, 0]
    )

    # The Robot IK will always assume as a starting position the arms to be pointing upwards
    robot_ik = bncommon.BnRobotIK_ArmZYY(
        lengthRA1=0.3,
        lengthRA2=1,
        lengthRA3=1,
        anglesConstraints=np.deg2rad([[-90, 90], [0, 90], [0, 180]]).tolist(),
        units="cm",
    )
    robot_mt = bncommon.BnRobotArm_IKMT(motiontrack, robot_ik)
    return robot_mt


def on_press(key):
    """on press key"""

    try:
        if key.char == "r":
            bodynodes_robotic_arm["event"]["reset"] = True
    except AttributeError:
        pass  # Special keys like shift, ctrl, etc.


def compute_sensor_values(communicator, robot_mt):
    """Compute sensor values"""

    if bodynodes_robotic_arm["event"]["reset"] is True:
        print("Resetting sensors values")
        bodynodes_robotic_arm["event"]["reset"] = False
        internal.la_right_first = None
        internal.ua_right_first = None

        internal.la_right_last = [1, 0, 0, 0]
        internal.ua_right_last = [1, 0, 0, 0]

    la_right = communicator.getMessageValue(
        "1",
        BnConstants.BODYPART_LOWERARM_RIGHT_TAG,
        BnConstants.SENSORTYPE_ORIENTATION_ABS_TAG,
    )
    ua_right = communicator.getMessageValue(
        "1",
        BnConstants.BODYPART_UPPERARM_RIGHT_TAG,
        BnConstants.SENSORTYPE_ORIENTATION_ABS_TAG,
    )

    if ua_right is not None:
        [internal.la_right_last, internal.la_right_first] = (
            bncommon.BnUtils.transform_sensor_quat(
                ua_right,
                internal.ua_right_first,
                [1, 0, 0, 0],
                [1, 0, 0, 0],
                bodynodes_axis_config_ua,
            )
        )

    if la_right is not None:
        [internal.la_right_last, internal.la_right_first] = (
            bncommon.BnUtils.transform_sensor_quat(
                la_right,
                internal.la_right_first,
                [1, 0, 0, 0],
                [1, 0, 0, 0],
                bodynodes_axis_config_la,
            )
        )

    [theta_ra1, gamma_ra2, gamma_ra3] = robot_mt.compute(
        internal.ua_right_last, internal.la_right_last
    )

    # from compute_sensor_values() in virtual3d_robotic_arm_zyy
    value_servo1 = int(math.degrees(theta_ra1)) + 90
    value_servo2 = 90 - int(math.degrees(gamma_ra2))
    value_servo3 = 180 - int(math.degrees(gamma_ra3))

    print([theta_ra1, value_servo1])

    Adeept.three_function(
        "'servo_write'", bodynodes_robotic_arm["pin"]["servo1"], value_servo1
    )
    # bodynodes_robotic_arm["prev_val"]["servo1"] = value_servo1
    Adeept.three_function(
        "'servo_write'", bodynodes_robotic_arm["pin"]["servo2"], value_servo2
    )
    # bodynodes_robotic_arm["prev_val"]["servo2"] = value_servo2
    Adeept.three_function(
        "'servo_write'", bodynodes_robotic_arm["pin"]["servo3"], value_servo3
    )
    # bodynodes_robotic_arm["prev_val"]["servo3"] = value_servo3


def main(serial_com):
    """Main app function"""

    communicator = setup_communicator()
    robot_mt = setup_robot_tracker()
    communicator.start(["BN"])

    listener = pynput.keyboard.Listener(on_press=on_press)
    listener.start()

    try:
        # Serial waits, so I can try to interrupt if I gave the wrong serial port

        # it might crash, add the proper try-catch
        setup_robotic_arm(serial_com)

        while True:
            compute_sensor_values(communicator, robot_mt)
            time.sleep(0.03)  # ~30 FPS
    except KeyboardInterrupt:
        print("Ctrl+C Pressed. Stopping the bnwifibodynodeshost")
    finally:
        print("Stopping everything")

        # it might crash, add the proper try-catch
        Adeept.close_ser()

        communicator.stop()

    sys.exit()


if __name__ == "__main__":
    # Example: python3 bnroboticarm_zyy.py /dev/ttyUSB0

    # Serial path argument has to be provided
    if len(sys.argv) < 2:
        print("Please connect the robotic arm and indicate the serial path")
        sys.exit(1)

    com = sys.argv[1]
    main(com)
