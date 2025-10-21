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

import virtualworld
import Adeept

sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../../body-nodes-common/python/")

import bncommon
import bnconstants


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
        initialPosition = [0,0,2], armVector1 = [0,0,-1.5], armVector2 = [1.5,0,0] )
    # The Robot IK will always assume as a starting position the arms to be pointing upwards
    robotIK = bncommon.BnRobotArmZYY_IK(
        lengthRA1 = 0.3, lengthRA2 = 1, lengthRA3 = 1,
        anglesConstraints = np.deg2rad([ [ -90, 90 ], [0 , 90], [0, 180 ] ]).tolist(),
        units = "cm")
    robotMT =  bncommon.BnRobotArm_MT( motiontrack, robotIK )
    return robotMT


def computeSensorValues(virt3d, robotMT):

    [offtheta_RA1, offgamma_RA2, offgamma_RA3] = virtualworld.getOffsets(virt3d)
    [theta_RA1, gamma_RA2, gamma_RA3] = virtualworld.getAngles(virt3d)

    valtheta_RA1 = (theta_RA1-offtheta_RA1)
    valgamma_RA2 = -(gamma_RA2-offgamma_RA2)
    valgamma_RA3 = -(gamma_RA3-offgamma_RA3)

    # Forcing values on the robotIK and make it calculate the Arms Endpoints
    robotMT.robotIK.theta_RA1 = math.radians(valtheta_RA1)
    robotMT.robotIK.gamma_RA2 = math.radians(valgamma_RA2)
    robotMT.robotIK.gamma_RA3 = math.radians(valgamma_RA3)

    #print( [theta_RA1, gamma_RA2, gamma_RA3] )

    endpoints = robotMT.robotIK.getEndpoints()

    virtualworld.setRoboticArmsPoints(virt3d, [0,0,0], endpoints[0], endpoints[1], endpoints[2])

    Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo1"], theta_RA1)
    Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo2"], gamma_RA2)
    Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo3"], gamma_RA3)


def main(com):

    virt3d = virtualworld.setupVirtual3dEnvironment()
    robotMT =  setupRobotTracker()
    
    try:
        # Serial waits, so I can try to interrupt if I gave the wrong serial port
        robotArm = setupRoboticArm(com)

        while virtualworld.updateVirtual3dEnvironment(virt3d):
            computeSensorValues(virt3d, robotMT)
            virtualworld.wait(30)  # ~30 FPS
    except KeyboardInterrupt:
        print("Ctrl+C Pressed. Stopping the bnwifibodynodeshost")
    finally:
        print("Stopping everything")
        try:
            Adeept.close_ser()
        except Exception as ex:
            print(ex)

        virtualworld.quit()

    exit()

if __name__=="__main__":
    # Example: python3 bnvirtual3d_roboticarm_zyy.py /dev/ttyUSB0

    # Serial path argument has to be provided
    if len(sys.argv) < 2:
        print("Please connect the robotic arm and indicate the serial path")
        sys.exit(1)

    com = sys.argv[1]
    main(com)


