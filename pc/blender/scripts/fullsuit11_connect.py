# MIT License
# 
# Copyright (c) 2019-2021 Manuel Bottini
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

# Implements Specification version 1.0

from socket import *
import os
import sys
import threading
import json
import bpy
from mathutils import *
import struct

dir_path = os.path.dirname(os.path.realpath(__file__))

# Removing the scripts saved in cache so that Blender uses the last updated version of the scritps
if os.path.isfile(os.path.abspath(__file__)+"/../../scripts/__pycache__/fullsuit11_animation.cpython-37.pyc"):
	os.remove(os.path.abspath(__file__)+"/../../scripts/__pycache__/fullsuit11_animation.cpython-37.pyc")
if os.path.isfile(os.path.abspath(__file__)+"/../../scripts/__pycache__/fullsuit11_recording.cpython-37.pyc"):
	os.remove(os.path.abspath(__file__)+"/../../scripts/__pycache__/fullsuit11_recording.cpython-37.pyc")

sys.path.append(os.path.abspath(__file__)+"/../../scripts")

if "fullsuit11_recording" in sys.modules:
	del sys.modules["fullsuit11_recording"]
if "fullsuit11_animation" in sys.modules:
	del sys.modules["fullsuit11_animation"]

import fullsuit11_recording
import fullsuit11_animation
#import bodynodes_utils

fullsuit_keys = [
	"lowerarm_left",
	"lowerarm_right",
	"head",
	"lowerbody",
	"lowerleg_left",
	"lowerleg_right",
	"upperarm_left",
	"upperarm_right",
	"upperbody",
	"upperleg_left",
	"upperleg_right"
]

# This script is made for the FullSuit-11 and it is required to create connections with the nodes

bodynodes_panel_connect = {
	"server" : {
		"running": False,
		"status": "Start server"
	}
}

bodynodes_server = {
	"host": "192.168.137.1",
	"port": 12345,
	"buffer_size": 1024,
	"socket": None,
	"connection": None
}

def parse_message(data_str):
	#print("data_str = " +data_str)
	data_str_a = data_str.split("\n")
	for index in range(0, len(data_str_a)):
		data_json = None
		try:
			data_json = json.loads(data_str_a[index])
		except json.decoder.JSONDecodeError as err:
			print("not a valid json: ",err)

		if data_json != None:
			if isinstance(data_json, list):
				for data_json_single in data_json:
					fullsuit11_recording.read_orientations(data_json_single)
			else:
				fullsuit11_recording.read_orientations(data_json)

class ServerConnection(threading.Thread):
	def __init__(self, name, socket):
		threading.Thread.__init__(self, target=self.run, name=name, args=())
		self.socket = socket

	def run(self):
		# print("ServerConnection ready")
		self.killed = False
		parsing = False
		while not self.killed:

			# If you are not receiving anything, check the port 12345
			bytesAddressPair = self.socket.recvfrom(bodynodes_server["buffer_size"])
			message_rec = bytesAddressPair[0]
			address = bytesAddressPair[1]
			
			clientMsg = "Message from Client:{}".format(message_rec)
			clientIP  = "Client IP Address:{}".format(address)
			#print(message_str)
			if len(message_rec) >= 3 and message_rec[0] == 65 and message_rec[1] == 67 and message_rec[2] == 75: # ACK ascii values
				print("ACK Message received ...")
				print(clientIP)
				print("Sending ACK to address = "+clientIP)
				self.socket.sendto(str.encode("ACK"), address)
			else:
				#print(clientMsg)
				message_str = message_rec.decode("utf-8")
				parse_message(message_str)
			
		# print("AcceptConnection stopping")
	def stop(self):
		self.killed = True

def start_server():
	# print("start_server")
	if bodynodes_server["socket"]:
		print("Socket is already there...")
		return

	fullsuit11_recording.reinit_bn_data()

	print("Creating socket ...")
	bodynodes_server["socket"] = socket(AF_INET, SOCK_DGRAM)
	print("Binding socket ...")

	try:
		print("Now running ...")
		bodynodes_server["socket"].bind((bodynodes_server["host"], bodynodes_server["port"]))	
		# bodynodes_server["socket"].listen(1)
	except:
		bodynodes_panel_connect["server"]["status"] = "Error starting server"
		bodynodes_server["socket"] = None
		print("Have you forgotten to create the hotspot?")
		raise

	print("Starting connection")
	bodynodes_server["connection"] = ServerConnection("accepter", bodynodes_server["socket"])
	bodynodes_server["connection"].start()
	bodynodes_panel_connect["server"]["running"] = True
	bodynodes_panel_connect["server"]["status"] = "Running"

def stop_server():
	print("stop_server")
	if bodynodes_server["connection"]:
		print("Stopping connection")
		bodynodes_server["connection"].stop()
		bodynodes_server["connection"] = None
	else:
		print("Connection already stopped")
		
	print("Closing socket")		
	if bodynodes_server["socket"]:
		bodynodes_server["socket"].close()
		bodynodes_server["socket"] = None
	else:
		print("Socket already stopped")
		
	bodynodes_panel_connect["server"]["status"] = "Server not running"
	bodynodes_panel_connect["server"]["running"] = False


def redirect_bodypart(bodypart):
	# print("redirect_bodypart")
	global bodynodes_armature_config_rec
	if bodypart in bodynodes_armature_config_rec.keys() and bodynodes_armature_config_rec[bodypart]["bone_name"] != "":
		return bodynodes_armature_config_rec[bodypart]["bone_name"]
	return "none"

def create_bodynodesobjs():
	global fullsuit_keys
	for bodypart in fullsuit_keys:
		if bodypart not in bpy.data.objects:
			bpy.ops.object.add()
			bpy.context.active_object.name = bodypart
			bpy.context.active_object.location = Vector((0,0,-10))
			bpy.context.active_object.rotation_mode = "QUATERNION"

def get_bodynodeobj(bodypart):
	if bodypart not in bpy.data.objects:
		print(bodypart+" bodynodeobj has not been found")
		return None
	return bpy.data.objects[bodypart]

def get_bone_global_rotation_quaternion(player_selected, bone):
	if bone not in bpy.data.objects[player_selected].pose.bones:
		print(bodypart+" bone has not been found")
		return None
	return (bpy.data.objects[player_selected].matrix_world @ bpy.data.objects[player_selected].pose.bones[bone].matrix).to_quaternion()

def get_bodynode_rotation_quaternion(bodypart):
	if bodypart not in bpy.data.objects:
		print(bodypart+" hasn't been found")
		return None
	return bpy.data.objects[bodypart].rotation_quaternion

def set_bodynode_rotation_quaternion(bodypart, rotation_quaternion):
	if bodypart not in bpy.data.objects:
		print(bodypart+" hasn't been found")
		return
	bpy.data.objects[bodypart].rotation_quaternion = rotation_quaternion

class PANEL_PT_BodynodesConnect(bpy.types.Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'View'
	bl_label = "Bodynodes Connect"

	def draw(self, context):
		layout = self.layout
		
		layout.label(text="Server:   "  + bodynodes_panel_connect["server"]["status"])
		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.operator("bodynodes.startstop_server",
			text="Stop" if bodynodes_panel_connect["server"]["running"] else "Start")
		col1.enabled = True

		row = layout.row()
		row.operator("bodynodes.close_connect", text="Close")

class BodynodesStartStopServerOperator(bpy.types.Operator):
	bl_idname = "bodynodes.startstop_server"
	bl_label = "StartStop Server Operator"
	bl_description = "Starts/Stop the local server. It resets position of the sensors at every start"

	def execute(self, context):
		if bodynodes_panel_connect["server"]["running"]:
			stop_server()
		else:
			bpy.app.timers.register(start_server, first_interval=4.0)

		return {'FINISHED'}

class BodynodesCloseConnectOperator(bpy.types.Operator):
	bl_idname = "bodynodes.close_connect"
	bl_label = "Close Connect Panel Operator"
	bl_description = "Close the Bodynodes connect panel"

	def execute(self, context):
		unregister_connect()
		return {'FINISHED'}

def register_connect():
	bpy.utils.register_class(BodynodesStartStopServerOperator)
	bpy.utils.register_class(BodynodesCloseConnectOperator)

	bpy.utils.register_class(PANEL_PT_BodynodesConnect)
	create_bodynodesobjs()

def unregister_connect() :
	bpy.utils.unregister_class(BodynodesStartStopServerOperator)
	bpy.utils.unregister_class(BodynodesCloseConnectOperator)

	bpy.utils.unregister_class(PANEL_PT_BodynodesConnect)

	fullsuit11_recording.unregister_recording()
	fullsuit11_animation.unregister_animation()


def stop_at_last_frame(scene):
	if scene.frame_current == scene.frame_end-1:
		stop_animation()

if __name__ == "__main__" :
	register_connect()
	fullsuit11_recording.register_recording()
	fullsuit11_animation.register_animation()
	




