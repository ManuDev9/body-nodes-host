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

"""Virtual Arm ZYY application using a Wifi Bodynodes Host"""

import sys
import os
from dataclasses import dataclass
import numpy as np

import virtualworld

sys.path.append(
    os.path.dirname(os.path.abspath(__file__)) + "/../../../body-nodes-common/python/"
)
sys.path.append(
    os.path.dirname(os.path.abspath(__file__)) + "/../../../modules/pythonlib/"
)

import bncommon  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
import bnwifibodynodeshost  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting

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
        anglesConstraints=np.deg2rad([[-90, 90], [0, 90], [0, 90]]).tolist(),
        units="cm",
    )
    robot_mt = bncommon.BnRobotArm_IKMT(motiontrack, robot_ik)
    return robot_mt


def compute_sensor_values(communicator, robot_mt, virt3d):
    """Do computations based on bodynodes data"""

    if virt3d["event"]["reset"]:
        virt3d["event"]["reset"] = False
        internal.la_right_first = None
        internal.ua_right_first = None

        internal.la_right_last = [1, 0, 0, 0]
        internal.ua_right_last = [1, 0, 0, 0]

    la_right = communicator.getMessageValue(
        "1",
        bncommon.BnConstants.BODYPART_LOWERARM_RIGHT_TAG,
        bncommon.BnConstants.SENSORTYPE_ORIENTATION_ABS_TAG,
    )
    ua_right = communicator.getMessageValue(
        "1",
        bncommon.BnConstants.BODYPART_UPPERARM_RIGHT_TAG,
        bncommon.BnConstants.SENSORTYPE_ORIENTATION_ABS_TAG,
    )

    if ua_right is not None:
        [internal.ua_right_last, internal.ua_right_first] = (
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

    [point0, point1, point2] = robot_mt.motionTraker.compute(
        internal.ua_right_last, internal.la_right_last
    )
    robot_mt.robot_ik.compute(point2)
    endpoints = robot_mt.robot_ik.getEndpoints()

    virtualworld.set_sensors_arms_points(virt3d, point0, point1, point2)
    virtualworld.set_robotic_arms_points(
        virt3d, [0, 0, 0], endpoints[0], endpoints[1], endpoints[2]
    )


def main():
    """Main application function"""
    communicator = setup_communicator()
    virt3d = virtualworld.setup_virtual3d_environment()
    robot_mt = setup_robot_tracker()
    communicator.start(["BN"])

    try:
        while virtualworld.update_virtual3d_environment(virt3d):
            compute_sensor_values(communicator, robot_mt, virt3d)
            virtualworld.wait(30)  # ~30 FPS
    except KeyboardInterrupt:
        print("Ctrl+C Pressed. Stopping the bnwifibodynodeshost")
    finally:
        virtualworld.quit_world()
        communicator.stop()


if __name__ == "__main__":

    print("-----------------")
    print(
        "This program will show what happens the effects of bodynodes sensor values in a virtual 3d environment."
    )
    print(
        "Use the bnvirtual3d_robotic_arm_zyy.py on your robotic arm to fit how the virtual 3d environment should consider as offset angles."
    )
    print("-----------------")
    main()
    sys.exit()
