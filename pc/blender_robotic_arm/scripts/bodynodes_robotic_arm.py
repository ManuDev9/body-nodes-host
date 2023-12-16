# MIT License
#
# Copyright (c) 2023 Manuel Bottini
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

import os
import sys
import json
import bpy
import mathutils
import time
import queue
import math
from bpy_extras.io_utils import ExportHelper, ImportHelper

dir_path = os.path.dirname(os.path.realpath(__file__))

# Removing the scripts saved in cache so that Blender uses the last updated version of the scritps
if os.path.isfile(os.path.abspath(__file__)+"/../../scripts/__pycache__/bodynodes_utils.cpython-37.pyc"):
	os.remove(os.path.abspath(__file__)+"/../../scripts/__pycache__/bodynodes_utils.cpython-37.pyc")

sys.path.append(os.path.abspath(__file__)+"/../../pyserial")

if "bodynodes_utils" in sys.modules:
	del sys.modules["bodynodes_utils"]

import bodynodes_utils
import Adeept

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

bodynodes_data = {
	"acceleration_rel" : {
		# Point related
		"point_pos" : None,
	
		# Sensor related
		"rest" : None,
		"decimals" : None,
		"timestamp_ms" : None,
		"timereset_ms" : 1000,
		"threshold" : 0.5,

		# Precise algorithm related
		"prev" : None,
		"velocity" : None,
		"diff_pos" : None
	}
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

bpy.types.Scene.bn_robotic_arm_rescale_pos =  bpy.props.FloatProperty(
	name = "",
	description = "Rescale Positioning Changes",
	min = 0.0,      # Minimum value
	max = 0.2,   	# Maximum value
	)

# Functions

def bnra_main_read_orientations():

	somevalue = bodynodes_utils.get_bone_local_rotation_quaternion("RoboticArmArmature", "BoneRoboticArmServo1").to_euler()
	value_servo1 = int(math.degrees(somevalue[2])) + 90
	somevalue = bodynodes_utils.get_bone_local_rotation_quaternion("RoboticArmArmature", "BoneRoboticArmServo2").to_euler()
	value_servo2 = int(math.degrees(somevalue[0])) + 90
	somevalue = bodynodes_utils.get_bone_local_rotation_quaternion("RoboticArmArmature", "BoneRoboticArmServo3").to_euler()
	value_servo3 = 90 - int(math.degrees(somevalue[0]))
	somevalue = bodynodes_utils.get_bone_local_rotation_quaternion("RoboticArmArmature", "BoneRoboticArmServo4").to_euler()
	value_servo4 = int(math.degrees(somevalue[1])) + 90

	#print("-------------")
	#print("BoneRoboticArmServo1 Z = " + str(value_servo1))
	#print("BoneRoboticArmServo2 X = " + str(value_servo2))
	#print("BoneRoboticArmServo3 X = " + str(value_servo3))
	#print("BoneRoboticArmServo4 Z = " + str(value_servo4))

	value_servo1 = recompute_valueservo( value_servo1, bodynodes_robotic_arm["prev_val"]["servo1"] )
	value_servo2 = recompute_valueservo( value_servo2, bodynodes_robotic_arm["prev_val"]["servo2"] )
	value_servo3 = recompute_valueservo( value_servo3, bodynodes_robotic_arm["prev_val"]["servo3"] )
	value_servo4 = recompute_valueservo( value_servo4, bodynodes_robotic_arm["prev_val"]["servo4"] )

	if not bodynodes_robotic_arm["serial"]["running"]:
		return 1

	try:
		Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo1"], value_servo1)
		bodynodes_robotic_arm["prev_val"]["servo1"] = value_servo1
		Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo2"], value_servo2)
		bodynodes_robotic_arm["prev_val"]["servo2"] = value_servo2
		Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo3"], value_servo3)
		bodynodes_robotic_arm["prev_val"]["servo3"] = value_servo3
		Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo4"], value_servo4)
		bodynodes_robotic_arm["prev_val"]["servo4"] = value_servo4
		#Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo5"], value_servo5)
	except Exception as e:
		# Code to handle the error
		print("An error occurred: " + str(e))

	return 0.02

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
	print(data_json)
	if data_json["sensortype"] == "acceleration_rel" and bpy.context.scene.bn_robotic_arm_sensortype_list == "1":
		read_acceleration(data_json)
	if data_json["sensortype"] == "glove":
		read_glove(data_json)

def read_acceleration(data_json):
	if data_json["bodypart"] != "katana":
		print("Not a Katana bodypart")
		return
	
	acc_values = data_json["value"]
	acc = {}
	acc["x"] = acc_values[0]
	acc["y"] = acc_values[1]
	acc["z"] = acc_values[2]
	#if acc["z"] < 0:
	#	acc["z"] = acc["z"] + 9.8
	#else:
	#	acc["z"] = acc["z"] - 9.8

	timestamp_ms = int( time.time() * 1000) 

	if bodynodes_data["acceleration_rel"]["decimals"] == None or bodynodes_data["acceleration_rel"]["rest"] == None:

		bodynodes_data["acceleration_rel"]["decimals"] = {}
		#bodynodes_data["acceleration_rel"]["decimals"]["x"] = get_decimals(acc["x"])
		#bodynodes_data["acceleration_rel"]["decimals"]["y"] = get_decimals(acc["y"])
		#bodynodes_data["acceleration_rel"]["decimals"]["z"] = get_decimals(acc["z"])
		bodynodes_data["acceleration_rel"]["decimals"]["x"] = 1
		bodynodes_data["acceleration_rel"]["decimals"]["y"] = 1
		bodynodes_data["acceleration_rel"]["decimals"]["z"] = 1

		bodynodes_data["acceleration_rel"]["rest"] = {}
		#bodynodes_data["acceleration_rel"]["rest"]["x"] = get_digit_at_decimal(acc["x"], bodynodes_data["acceleration_rel"]["decimals"]["x"])
		#bodynodes_data["acceleration_rel"]["rest"]["y"] = get_digit_at_decimal(acc["y"], bodynodes_data["acceleration_rel"]["decimals"]["y"])
		#bodynodes_data["acceleration_rel"]["rest"]["z"] = get_digit_at_decimal(acc["z"], bodynodes_data["acceleration_rel"]["decimals"]["z"])
		bodynodes_data["acceleration_rel"]["rest"]["x"] = 0
		bodynodes_data["acceleration_rel"]["rest"]["y"] = 0
		bodynodes_data["acceleration_rel"]["rest"]["z"] = 0

		bodynodes_data["acceleration_rel"]["prev"] = {}
		bodynodes_data["acceleration_rel"]["prev"]["x"] = 0
		bodynodes_data["acceleration_rel"]["prev"]["y"] = 0
		bodynodes_data["acceleration_rel"]["prev"]["z"] = 0

		bodynodes_data["acceleration_rel"]["velocity"] = {}
		bodynodes_data["acceleration_rel"]["velocity"]["x"] = 0
		bodynodes_data["acceleration_rel"]["velocity"]["y"] = 0
		bodynodes_data["acceleration_rel"]["velocity"]["z"] = 0

		bodynodes_data["acceleration_rel"]["diff_pos"] = {}
		bodynodes_data["acceleration_rel"]["diff_pos"]["x"] = 0
		bodynodes_data["acceleration_rel"]["diff_pos"]["y"] = 0
		bodynodes_data["acceleration_rel"]["diff_pos"]["z"] = 0

		bodynodes_data["acceleration_rel"]["timestamp_ms"] = {}
		bodynodes_data["acceleration_rel"]["timestamp_ms"]["x"] = None
		bodynodes_data["acceleration_rel"]["timestamp_ms"]["y"] = None
		bodynodes_data["acceleration_rel"]["timestamp_ms"]["z"] = None


		print("Got acceleration_rel at rest")
		print("raw values = "+str(acc_values))
		print("decimals = "+str(bodynodes_data["acceleration_rel"]["decimals"]))
		print("rest = "+str(bodynodes_data["acceleration_rel"]["rest"]))
		return
	
	# Let's do some clean up
	acc["x"] = clean_up_acc(acc["x"],
		bodynodes_data["acceleration_rel"]["decimals"]["x"],
		bodynodes_data["acceleration_rel"]["rest"]["x"])
	acc["y"] = clean_up_acc(acc["y"],
		bodynodes_data["acceleration_rel"]["decimals"]["y"],
		bodynodes_data["acceleration_rel"]["rest"]["y"])
	acc["z"] = clean_up_acc(acc["z"],
		bodynodes_data["acceleration_rel"]["decimals"]["z"],
		bodynodes_data["acceleration_rel"]["rest"]["z"])
	
	#print( "Acc raw values = "+str(acc_values))
	#print( "Acc cleaned up value = " +str(acc) )
	#moveRoboticArm_heur(acc, timestamp_ms, "x")
	#moveRoboticArm_heur(acc, timestamp_ms, "y")
	#moveRoboticArm_heur(acc, timestamp_ms, "z")
	print("Acceleration needs to be worked on")

# TODO in the future
def moveRoboticArm(acc, timestamp_ms, axis):
	abs_acc = abs(acc[axis])
	if abs_acc	< bodynodes_data["acceleration_rel"]["threshold"]:
		print("Jump calculations because of small values")
		bodynodes_data["acceleration_rel"]["prev"][axis] = acc[axis]
		return

	if bodynodes_data["acceleration_rel"]["timestamp_ms"][axis] == None:
		print("Reset because of timestamp")
		bodynodes_data["acceleration_rel"]["timestamp_ms"][axis] = timestamp_ms
		return

	timestamp_diff_ms = timestamp_ms - bodynodes_data["acceleration_rel"]["timestamp_ms"][axis]
	if timestamp_diff_ms > bodynodes_data["acceleration_rel"]["timereset_ms"]:
		print("Reset because of timestamp is too long")
		bodynodes_data["acceleration_rel"]["velocity"][axis] = 0
		bodynodes_data["acceleration_rel"]["prev"][axis] = acc[axis]
		bodynodes_data["acceleration_rel"]["diff_pos"] = {}
		bodynodes_data["acceleration_rel"]["timestamp_ms"][axis] = timestamp_ms
		return

	# I will make use of what is the timestamp I set on the sensor itself
	timestamp_diff_ms = 30
	timestamp_diff_s = float(timestamp_diff_ms) / 1000.0

	vel_prev = bodynodes_data["acceleration_rel"]["velocity"][axis]

	# Compute velocities: change_in_velocity = ((acceleration2 - acceleration1)/2 + acceleration1 ) * time_difference
	bodynodes_data["acceleration_rel"]["velocity"][axis] = vel_prev + \
		(( acc[axis] - bodynodes_data["acceleration_rel"]["prev"][axis] ) / 2 + bodynodes_data["acceleration_rel"]["prev"][axis] ) \
		* timestamp_diff_s

	# Compute position: change_in_position = 0.5 * (start_velocity + end_velocity) * time_difference
	bodynodes_data["acceleration_rel"]["diff_pos"][axis] = ( vel_prev + bodynodes_data["acceleration_rel"]["velocity"][axis] ) / 2 * timestamp_diff_s
	bodynodes_data["acceleration_rel"]["diff_pos"][axis] = bodynodes_data["acceleration_rel"]["diff_pos"][axis] * bpy.context.scene.bn_robotic_arm_rescale_pos
	
	#print("Rescaling = " +str(bpy.context.scene.bn_robotic_arm_rescale_pos))

	if axis == "x":
		bpy.data.objects["RoboticArmPoint"].location.x = bpy.data.objects["RoboticArmPoint"].location.x + bodynodes_data["acceleration_rel"]["diff_pos"][axis]
	elif axis == "y":
		bpy.data.objects["RoboticArmPoint"].location.y = bpy.data.objects["RoboticArmPoint"].location.y + bodynodes_data["acceleration_rel"]["diff_pos"][axis]
	elif axis == "z":
		bpy.data.objects["RoboticArmPoint"].location.z = bpy.data.objects["RoboticArmPoint"].location.z + bodynodes_data["acceleration_rel"]["diff_pos"][axis]

	bodynodes_data["acceleration_rel"]["prev"][axis] = acc[axis]

	print( "--------------- Axis = " + axis )
	print( "Timestamp_diff_ms = " + str(timestamp_diff_ms) )
	print( "Acceleration = " + str(bodynodes_data["acceleration_rel"]["prev"][axis]) )
	print( "Velocity = " + str(bodynodes_data["acceleration_rel"]["velocity"][axis]) )
	print( "Position Diff = " + str(bodynodes_data["acceleration_rel"]["diff_pos"][axis]) )
	print( "Position Obj = " + str(bpy.data.objects["RoboticArmPoint"].location) )

	return

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
		if glove_values[5] == 1:
			Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo5"], 120)
		else:
			Adeept.three_function("'servo_write'", bodynodes_robotic_arm["pin"]["servo5"], 35)
	except Exception as e:
		# Code to handle the error
		print("An error occurred: " + str(e))




def set_point_pos():
	bodynodes_data["acceleration_rel"]["point_pos"] = mathutils.Vector((bpy.data.objects["RoboticArmPoint"].location))

def reset_point_pos():
	if bodynodes_data["acceleration_rel"]["point_pos"] != None:
		bpy.data.objects["RoboticArmPoint"].location = mathutils.Vector((bodynodes_data["acceleration_rel"]["point_pos"]))
	else:
		print("Cannot reset point position because it was not previously set")

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

		layout.label(text="Rescale Movement:")
		row = layout.row()
		row.prop(context.scene, 'bn_robotic_arm_rescale_pos', expand=True)

		layout.label(text="Point Position:")
		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.operator("bodynodes.bn_robotic_arm_set_point_pos", text="Set")
		col1.enabled = True

		col2 = row.column()
		col2.operator("bodynodes.bn_robotic_arm_reset_point_pos", text="Reset")
		col2.enabled = True

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

class BodynodesRoboticArmSetPointPositionOperator(bpy.types.Operator):
	bl_idname = "bodynodes.bn_robotic_arm_set_point_pos"
	bl_label = "Robotic Arm Set Point Position"
	bl_description = "Set Point Position for the Robotic Arm."

	def execute(self, context):
		set_point_pos()
		return {'FINISHED'}

class BodynodesRoboticArmResetPointPositionOperator(bpy.types.Operator):
	bl_idname = "bodynodes.bn_robotic_arm_reset_point_pos"
	bl_label = "Robotic Arm Reset Point Position"
	bl_description = "Reset Point Position for the Robotic Arm."

	def execute(self, context):
		reset_point_pos()
		return {'FINISHED'}

def register_robotic_arm():
	bpy.utils.register_class(BodynodesRoboticArmStartStopSerialOperator)
	bpy.utils.register_class(BodynodesRoboticArmSetPointPositionOperator)
	bpy.utils.register_class(BodynodesRoboticArmResetPointPositionOperator)
	bpy.utils.register_class(PANEL_PT_BodynodesRoboticArm)

	bpy.app.timers.register(bnra_main_read_orientations)


def unregister_robotic_arm() :
	stop_serial()
	bpy.utils.unregister_class(BodynodesRoboticArmStartStopSerialOperator)
	bpy.utils.unregister_class(BodynodesRoboticArmSetPointPositionOperator)
	bpy.utils.unregister_class(BodynodesRoboticArmResetPointPositionOperator)
	bpy.utils.unregister_class(PANEL_PT_BodynodesRoboticArm)

	bpy.app.timers.unregister(bnra_main_read_orientations)

if __name__ == "__main__" :
	register_robotic_arm()
