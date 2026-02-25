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

"""Virtual Arm ZYY application connected to a robotic arm"""

import sys
import os
import math
import numpy as np

import virtualworld
import Adeept

sys.path.append(
    os.path.dirname(os.path.abspath(__file__)) + "/../../../body-nodes-common/python/"
)

import bncommon  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting


bodynodes_robotic_arm = {
    "event": {"reset": False},
    "pin": {"servo1": 0, "servo2": 1, "servo3": 2, "servo4": 3, "servo5": 4},
}


def setup_robotic_arm(com_serial):
    """Setup robotic arm"""

    Adeept.com_init(com_serial, 115200, 1)
    print(f"Trying to connect to serial {com_serial}...")
    Adeept.wiat_connect()
    print(f"Connected to serial {com_serial}!")
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo1"], 9)
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo2"], 6)
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo3"], 5)
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo4"], 3)
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo5"], 11)


def setup_robot_tracker():
    """Setup robot tracker"""

    motiontrack = bncommon.BnMotionTracking_2Nodes(
        initialPosition=[0, 0, 2], armVector1=[0, 0, -1.5], armVector2=[1.5, 0, 0]
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


def compute_sensor_values(virt3d, robot_mt):
    """Sensor data computation and move arm"""

    [offtheta_ra1, offgamma_ra2, offgamma_ra3] = virtualworld.get_offsets(virt3d)
    [theta_ra1, gamma_ra2, gamma_ra3] = virtualworld.get_angles(virt3d)

    valtheta_ra1 = theta_ra1 - offtheta_ra1
    valgamma_ra2 = -(gamma_ra2 - offgamma_ra2)
    valgamma_ra3 = -(gamma_ra3 - offgamma_ra3)

    # Forcing values on the robotIK and make it calculate the Arms Endpoints
    robot_mt.robotIK.theta_RA1 = math.radians(valtheta_ra1)
    robot_mt.robotIK.gamma_RA2 = math.radians(valgamma_ra2)
    robot_mt.robotIK.gamma_RA3 = math.radians(valgamma_ra3)

    # print( [theta_RA1, gamma_RA2, gamma_RA3] )

    endpoints = robot_mt.robotIK.getEndpoints()

    virtualworld.set_robotic_arms_points(
        virt3d, [0, 0, 0], endpoints[0], endpoints[1], endpoints[2]
    )

    Adeept.three_function(
        "'servo_write'", bodynodes_robotic_arm["pin"]["servo1"], theta_ra1
    )
    Adeept.three_function(
        "'servo_write'", bodynodes_robotic_arm["pin"]["servo2"], gamma_ra2
    )
    Adeept.three_function(
        "'servo_write'", bodynodes_robotic_arm["pin"]["servo3"], gamma_ra3
    )


def main(com_serial):
    """Main application function"""

    virt3d = virtualworld.setup_virtual3d_environment()
    robot_mt = setup_robot_tracker()

    try:
        # Serial waits, so I can try to interrupt if I gave the wrong serial port
        setup_robotic_arm(com_serial)

        while virtualworld.update_virtual3d_environment(virt3d):
            compute_sensor_values(virt3d, robot_mt)
            virtualworld.wait(30)  # ~30 FPS
    except KeyboardInterrupt:
        print("Ctrl+C Pressed. Stopping the bnwifibodynodeshost")
    finally:
        print("Stopping everything")
        # It might trigger an exception, add the proper try-catch
        Adeept.close_ser()

        virtualworld.quit_world()


if __name__ == "__main__":
    # Example: python3 bnvirtual3d_roboticarm_zyy.py /dev/ttyUSB0

    # Serial path argument has to be provided
    if len(sys.argv) < 2:
        print("Please connect the robotic arm and indicate the serial path")
        sys.exit(1)

    com = sys.argv[1]
    main(com)
    sys.exit()
