#
# MIT License
#
# Copyright (c) 2023-2024 Manuel Bottini
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

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
import bpy
import mathutils
import time
import queue
import math
from bpy_extras.io_utils import ExportHelper, ImportHelper

import glob
import os
import sys

# pip install pyserial 

# Removing the scripts saved in cache so that Blender uses the last updated version of the scritps
[os.remove(file) for file in glob.glob(os.path.join(os.path.abspath(__file__ + "/../../scripts/__pycache__"), "bodynodes_robotic_arm.cpython*.pyc"))]
[os.remove(file) for file in glob.glob(os.path.join(os.path.abspath(__file__ + "/../../../common/__pycache__"), "bnblenderutils.cpython*.pyc"))]
[os.remove(file) for file in glob.glob(os.path.join(os.path.abspath(__file__ + "/../../../common/__pycache__"), "bnblenderconnect.cpython*.pyc"))]
[os.remove(file) for file in glob.glob(os.path.join(os.path.abspath(__file__ + "/../../../common/__pycache__"), "bnblenderrecording.cpython*.pyc"))]
[os.remove(file) for file in glob.glob(os.path.join(os.path.abspath(__file__ + "/../../../common/__pycache__"), "bnblenderaxis.cpython*.pyc"))]
[os.remove(file) for file in glob.glob(os.path.join(os.path.abspath(__file__ + "/../../../../modules/pythonlib_wifi/__pycache__"), "bnwifibodynodeshost.cpython*.pyc"))]

sys.path.append(os.path.abspath(__file__)+"/../../scripts")
sys.path.append(os.path.abspath(__file__)+"/../../pyserial")
sys.path.append(os.path.abspath(__file__)+"/../../../BlenderCommon")
sys.path.append(os.path.abspath(__file__)+"/../../../../../modules/pythonlib")

if "serial" in sys.modules:
    del sys.modules["serial"]
if "bnblenderconnect" in sys.modules:
    del sys.modules["bnblenderconnect"]
if "bnblenderrecording" in sys.modules:
    del sys.modules["bnblenderrecording"]
if "bnblenderaxis" in sys.modules:
    del sys.modules["bnblenderaxis"]
if "bnblenderutils" in sys.modules:
    del sys.modules["bnblenderutils"]

import Adeept
import bnblenderutils
import bnblenderconnect
import bnblenderaxis
import bnblenderrecording

# This script is made for the Bodynodes Robotic Arm

# Objects

bodynodes_robotic_arm = {
    "serial" : {
        "running": False,
        "status": "Start Serial"
    },
    "pin" : {
        "servo1" : 0,
        "servo2" : 1,
        "servo3" : 2,
        "servo4" : 3,
        "servo5" : 4
    },
    "prev_val" : {
        "servo1" : None,
        "servo2" : None,
        "servo3" : None,
        "servo4" : None,
        "servo5" : None
    },
    "max_degr_change" : 3
}

bpy.types.Scene.bn_robotic_arm_com_serial_port =  bpy.props.StringProperty(
    name = "",
    description = "COM Serial Port Robotic Arm",
    default = "",
    maxlen = 10,
    )

bpy.types.Scene.bn_robotic_arm_sensortype_list = bpy.props.EnumProperty(items = (
    ('0','Abs Ori',''),
    ('1','Rel Acc',''),
    ),
    default = '0',
    description = "Sensor Type to use"
    )

# Functions

def bnra_main_read_orientations():

    somevalue = bnblenderutils.get_bone_local_rotation_quaternion("RoboticArmArmature", "BoneRoboticArmServo1").to_euler()
    value_servo1 = int(math.degrees(somevalue[2])) + 90
    somevalue = bnblenderutils.get_bone_local_rotation_quaternion("RoboticArmArmature", "BoneRoboticArmServo2").to_euler()
    value_servo2 = 90 - int(math.degrees(somevalue[0]))
    somevalue = bnblenderutils.get_bone_local_rotation_quaternion("RoboticArmArmature", "BoneRoboticArmServo3").to_euler()
    value_servo3 = 90 - int(math.degrees(somevalue[0]))
    #somevalue = bnblenderutils.get_bone_local_rotation_quaternion("RoboticArmArmature", "BoneRoboticArmServo4").to_euler()
    #value_servo4 = int(math.degrees(somevalue[1])) + 90

    #print("-------------")
    #print("BoneRoboticArmServo1 Z = " + str(value_servo1))
    #print("BoneRoboticArmServo2 X = " + str(value_servo2))
    #print("BoneRoboticArmServo3 X = " + str(value_servo3))
    #print("BoneRoboticArmServo4 Z = " + str(value_servo4))

    #value_servo1 = recompute_valueservo( value_servo1, bodynodes_robotic_arm["prev_val"]["servo1"] )
    #value_servo2 = recompute_valueservo( value_servo2, bodynodes_robotic_arm["prev_val"]["servo2"] )
    #value_servo3 = recompute_valueservo( value_servo3, bodynodes_robotic_arm["prev_val"]["servo3"] )
    #value_servo4 = recompute_valueservo( value_servo4, bodynodes_robotic_arm["prev_val"]["servo4"] )

    if not bodynodes_robotic_arm["serial"]["running"]:
        return 1

    try:
        Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo1"], value_servo1)
        bodynodes_robotic_arm["prev_val"]["servo1"] = value_servo1
        Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo2"], value_servo2)
        bodynodes_robotic_arm["prev_val"]["servo2"] = value_servo2
        Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo3"], value_servo3)
        bodynodes_robotic_arm["prev_val"]["servo3"] = value_servo3
        #Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo4"], value_servo4)
        #bodynodes_robotic_arm["prev_val"]["servo4"] = value_servo4
        #Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo5"], value_servo5)
    except Exception as e:
        # Code to handle the error
        print("An error occurred: " + str(e))

    return 0.1

def recompute_valueservo( value, value_prev ):

    if value_prev == None:
        return value

    if value - value_prev >= 0:
        if value - value_prev > bodynodes_robotic_arm["max_degr_change"]:
            return value_prev + bodynodes_robotic_arm["max_degr_change"]
        else:
            return value
    else:
        if value - value_prev < - bodynodes_robotic_arm["max_degr_change"]:
            return value_prev - bodynodes_robotic_arm["max_degr_change"]
        else:
            return value
        

def read_sensordata(data_json):
    if "bodypart" not in data_json:
        print("bodypart key missing in json")
        return

    if "sensortype" not in data_json:
        print("type key missing in json")
        return

    if "value" not in data_json and "quat" not in data_json:
        print("value or quat key missing in json")
        return

    #if data_json["sensortype"] == "orientation_abs":
        # No need to use orientation here since recording at the moment will do it 
        # read_orientations(data_json)
    if data_json["sensortype"] == "glove":
        #print("roba " + str(data_json))
        read_glove(data_json)




# Given a number < 1, it returns the number of decimals in order to reach a value != 0
def get_decimals(number):
    if number == 0:
        return 0
    decimal = 0
    if number < 0:
        number = -number;
    while number < 1:
        number = number * 10
        decimal = decimal + 1
    return decimal

# Returns the number at a particular decimal
def get_digit_at_decimal(number, decimal):
    val = round( number * pow(10, decimal))
    if val < 0:
        val = -val
    return val

def clean_up_acc(acc_value, decimal, digit):
    acc_value_sign = 1
    if acc_value < 0:
        acc_value_sign = -1
        acc_value = -acc_value

    move_comma = pow(10, decimal)
    return acc_value_sign * round(acc_value * move_comma - digit) / move_comma

def read_glove(data_json):
    
    glove_values = data_json["value"]
    print(glove_values)
    
    if not bodynodes_robotic_arm["serial"]["running"]:
        return

    try:
        # Extrema are 30 and 100
        if glove_values[bnblenderutils.GLOVE_TOUCH_INDICE] == 1:
            Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo5"], 120)
        else:
            Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo5"], 35)
    except Exception as e:
        # Code to handle the error
        print("An error occurred: " + str(e))

def start_serial():
    com = bpy.context.scene.bn_robotic_arm_com_serial_port
    print("Connecting to " + com)
    bodynodes_robotic_arm["serial"]["status"] = "Running"
    Adeept.com_init(com,115200,1)
    Adeept.wiat_connect()
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo1"], 9)
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo2"], 6)
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo3"], 5)
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo4"], 3)
    Adeept.three_function("'servo_attach'", bodynodes_robotic_arm["pin"]["servo5"], 11)
    bodynodes_robotic_arm["serial"]["running"] = True

    return

def stop_serial():
    if not bodynodes_robotic_arm["serial"]["running"]:
        return

    Adeept.close_ser()
    bodynodes_robotic_arm["serial"]["running"] = False
    bodynodes_robotic_arm["serial"]["status"] = "Start Serial"
    return

# UI

class PANEL_PT_BodynodesRoboticArm(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'View'
    bl_label = "Bodynodes Robotic Arm"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.label(text="COM Port:")

        row = layout.row()
        row.prop(context.scene, 'bn_robotic_arm_com_serial_port')
        row.enabled = True

        # Big render button
        layout.label(text="Serial:   "  + bodynodes_robotic_arm["serial"]["status"])
        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator("bodynodes.robotic_arm_startstop_serial",
            text="Stop" if bodynodes_robotic_arm["serial"]["running"] else "Start")
        col1.enabled = True
    
        #layout.label(text="Sensor Type:")
        #row = layout.row()
        #row.prop(context.scene, 'bn_robotic_arm_sensortype_list', expand=True)

        row = layout.row()
        row.operator("bodynodes.close_main", text="Close")

class BodynodesRoboticArmStartStopSerialOperator(bpy.types.Operator):
    bl_idname = "bodynodes.robotic_arm_startstop_serial"
    bl_label = "Robotic Arm StartStop Serial Operator"
    bl_description = "Starts/Stop the serial of the Robotic Arm."

    def execute(self, context):
        if bodynodes_robotic_arm["serial"]["running"]:
            stop_serial()
        else:
            start_serial()

        return {'FINISHED'}


class BodynodesCloseMainOperator(bpy.types.Operator):
    bl_idname = "bodynodes.close_main"
    bl_label = "Close Main Panel Operator"
    bl_description = "Close all the Bodynodes panels"

    def execute(self, context):
        unregister_robotic_arm()
        return {'FINISHED'}

class BnConnectListener:
    def read_sensordata_callback(self, data_json):
        bnblenderrecording.read_sensordata(data_json)
        read_sensordata(data_json)

    def reinit_bn_data(self):
        bnblenderrecording.reinit_bn_data()

connectListener = BnConnectListener()  

def register_robotic_arm():
    bpy.utils.register_class(BodynodesRoboticArmStartStopSerialOperator)
    bpy.utils.register_class(BodynodesCloseMainOperator)
    bpy.utils.register_class(PANEL_PT_BodynodesRoboticArm)

    bpy.app.timers.register(bnra_main_read_orientations)
    bnblenderconnect.register_connect(connectListener)
    bnblenderrecording.register_recording()
    bnblenderaxis.register_axis()

    bnblenderaxis.load_axis_config_default(os.path.realpath(__file__))

def unregister_robotic_arm() :
    stop_serial()
    bpy.utils.unregister_class(BodynodesRoboticArmStartStopSerialOperator)
    bpy.utils.unregister_class(BodynodesCloseMainOperator)
    bpy.utils.unregister_class(PANEL_PT_BodynodesRoboticArm)

    bpy.app.timers.unregister(bnra_main_read_orientations)
    bnblenderconnect.unregister_connect()
    bnblenderrecording.unregister_recording()
    bnblenderaxis.unregister_axis()

if __name__ == "__main__" :
    register_robotic_arm()
