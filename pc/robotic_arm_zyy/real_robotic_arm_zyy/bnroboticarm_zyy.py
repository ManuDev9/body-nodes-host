#
# MIT License
# 
# Copyright (c) 2025 Manuel Bottini
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

import sys
import os
import time
import numpy as np
import math
import pynput

import Adeept

sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../../body-nodes-common/python/")
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../../modules/pythonlib/")

import bnwifibodynodeshost
import bncommon
import bnconstants

bodynodes_axis_config_la = {
    "new_w_sign" : 1,
    "new_x_sign" : 1,
    "new_y_sign" : -1,
    "new_z_sign" : -1,
    
    "new_w_val" : 0,
    "new_x_val" : 1,
    "new_y_val" : 3,
    "new_z_val" : 2
}

bodynodes_axis_config_ua = {
    "new_w_sign" : 1,
    "new_x_sign" : -1,
    "new_y_sign" : -1,
    "new_z_sign" : 1,
    
    "new_w_val" : 0,
    "new_x_val" : 2,
    "new_y_val" : 3,
    "new_z_val" : 1
}


bodynodes_robotic_arm = {
    "event" : {
        "reset" : False
    },
    "pin" : {
        "servo1" : 0,
        "servo2" : 1,
        "servo3" : 2,
        "servo4" : 3,
        "servo5" : 4
    }
}


def setupCommunicator():
    return bnwifibodynodeshost.BnWifiHostCommunicator()


def setupRoboticArm(com):
    robotArm = {}

    Adeept.com_init(com,115200,1)
    print(f"Trying to connect to serial {com}...")
    Adeept.wiat_connect()
    print(f"Connected to serial {com}!")
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo1"], 9)
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo2"], 6)
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo3"], 5)
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo4"], 3)
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo5"], 11)

    return robotArm

def setupRobotTracker():
    motiontrack = bncommon.BnMotionTracking_2Nodes(
        initialPosition = [0,0,1.5], armVector1 = [0,0,-1.2], armVector2 = [1.2,0,0] )
    # The Robot IK will always assume as a starting position the arms to be pointing upwards
    robotIK = bncommon.BnRobotArmZYY_IK(
        lengthRA1 = 0.3, lengthRA2 = 1, lengthRA3 = 1,
        anglesConstraints = np.deg2rad([ [ -90, 90 ], [0 , 90], [0, 180 ] ]).tolist(),
        units = "cm")
    robotMT =  bncommon.BnRobotArm_MT( motiontrack, robotIK )
    return robotMT


def on_press(key):
    try:
        if key.char == 'r':
            bodynodes_robotic_arm["event"]["reset"] = True
    except AttributeError:
        pass  # Special keys like shift, ctrl, etc.

la_right_first = None
ua_right_first = None

la_right_last = [1,0,0,0]
ua_right_last = [1,0,0,0]


def computeSensorValues(communicator, robotMT):

    global la_right_last
    global ua_right_last
    global ua_right_first
    global la_right_first

    
    if bodynodes_robotic_arm["event"]["reset"] == True:
        print("Resetting sensors values")
        bodynodes_robotic_arm["event"]["reset"] = False
        la_right_first = None
        ua_right_first = None

        la_right_last = [1,0,0,0]
        ua_right_last = [1,0,0,0]

    la_right = communicator.getMessageValue( "1", bnconstants.BODYPART_LOWERARM_RIGHT_TAG , bnconstants.SENSORTYPE_ORIENTATION_ABS_TAG )
    ua_right = communicator.getMessageValue( "1", bnconstants.BODYPART_UPPERARM_RIGHT_TAG , bnconstants.SENSORTYPE_ORIENTATION_ABS_TAG )

    if ua_right != None:
        [ua_right_last, ua_right_first] = bncommon.transform_sensor_quat(
            ua_right,
            ua_right_first,
            [1, 0, 0, 0], 
            [1, 0, 0, 0], 
            bodynodes_axis_config_ua
        )

    if la_right != None:
        [la_right_last, la_right_first] = bncommon.transform_sensor_quat(
            la_right,
            la_right_first,
            [1, 0, 0, 0], 
            [1, 0, 0, 0], 
            bodynodes_axis_config_la
        )

    [theta_RA1, gamma_RA2, gamma_RA3 ] = robotMT.compute(ua_right_last, la_right_last)


    # from computeSensorValues() in virtual3d_robotic_arm_zyy
    value_servo1 = int(math.degrees(theta_RA1))+90
    value_servo2 = 90-int(math.degrees(gamma_RA2))
    value_servo3 = 180-int(math.degrees(gamma_RA3))

    print([theta_RA1, value_servo1])

    Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo1"], value_servo1)
    #bodynodes_robotic_arm["prev_val"]["servo1"] = value_servo1
    Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo2"], value_servo2)
    #bodynodes_robotic_arm["prev_val"]["servo2"] = value_servo2
    Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo3"], value_servo3)
    #bodynodes_robotic_arm["prev_val"]["servo3"] = value_servo3


def main(com):

    communicator = setupCommunicator()
    robotMT =  setupRobotTracker()
    communicator.start(["BN"])

    listener = pynput.keyboard.Listener(on_press=on_press)
    listener.start()
    
    try:
        # Serial waits, so I can try to interrupt if I gave the wrong serial port
        robotArm = setupRoboticArm(com)

        while True:
            computeSensorValues(communicator, robotMT)
            time.sleep(0.03)  # ~30 FPS
    except KeyboardInterrupt:
        print("Ctrl+C Pressed. Stopping the bnwifibodynodeshost")
    except Exception as ex:
        print(ex)
    finally:
        print("Stopping everything")
        try:
            Adeept.close_ser()
        except Exception as ex:
            print(ex)

        communicator.stop()

    exit()


if __name__=="__main__":
    # Example: python3 bnroboticarm_zyy.py /dev/ttyUSB0

    # Serial path argument has to be provided
    if len(sys.argv) < 2:
        print("Please connect the robotic arm and indicate the serial path")
        sys.exit(1)

    com = sys.argv[1]
    main(com)


