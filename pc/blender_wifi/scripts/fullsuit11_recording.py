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

from socket import *
import os
import sys
import threading
import json
import bpy
from mathutils import *
import time
import queue
from bpy_extras.io_utils import ExportHelper, ImportHelper

#sys.path.append(os.path.abspath(__file__)+"/../../")
#import bodynodes_utils

# This script is made for the FullSuit-11 and it is required to record bodynodes animations

players_available = (('None', 'None', ''), ('BlueGuy', 'BlueGuy', ''))
player_selected_rec = "None"

bodynodes_armature_config_rec = {}
bodynodes_saved_armature = {}

bodynodes_objs_init = {
	"forearm_left": Quaternion((0.0000, 0.707107, 0.707107, 0.0000)),
	"forearm_right": Quaternion((0.0000, 0.707107, -0.707107, 0.0000)),
	"head": Quaternion((1.0000, 0.0000, 0.0000, 0.0000)),
	"Hip": Quaternion((1.0000, 0.0000, 0.0000, 0.0000)),
	"lowerbody": Quaternion((1.0000, 0.0000, 0.0000, 0.0000)),
	"lowerleg_left": Quaternion((-0.707107, 0.707107, 0.0000, 0.0000)),
	"lowerleg_right": Quaternion((-0.707107, 0.707107, 0.0000, 0.0000)),
	"upperarm_left": Quaternion((0.0000, 0.707107, 0.707107, 0.0000)),
	"upperarm_right": Quaternion((0.0000, 0.707107, -0.707107, 0.0000)),
	"upperbody": Quaternion((1.0000, 0.0000, 0.0000, 0.0000)),
	"upperleg_left": Quaternion((-0.707107, 0.707107, 0.0000, 0.0000)),
	"upperleg_right": Quaternion((-0.707107, 0.707107, 0.0000, 0.0000))
}

bodynodes_tpos = {}

bodynodes_data = {
	"targetQuat": {},
	"changed": {},
	"offsetQuat": {},
	"readQuat": {},
	"reoriQuat": {},
	"recording": False,
	"take": None,
	"track" : True
}

bodynodes_panel_rec = {
	"server" : {
		"running": False,
		"status": "Start server"
	},
	"recording" : {
		"status": ""
	}
}

bodynodes_server = {
	"host": "192.168.137.1",
	"port": 12344,
	"buffer_size": 1024,
	"socket": None,
	"connection": None
}

bodynodes_takes = [{}, {}, {}]

info_dialog_rec_obj = {
	"text" : "",
	"is_visible" : False
}

def main_read_orientations():
	for bodypart in bodynodes_data["readQuat"]:
		if bodypart in bodynodes_data["changed"] and bodynodes_data["changed"][bodypart]:
			player_bodypart = get_bodynodeobj(bodypart)
			if bodypart not in bodynodes_data["offsetQuat"]:			
				bodynodes_data["offsetQuat"][bodypart] = bodynodes_data["readQuat"][bodypart].inverted() @ bpy.data.objects[player_selected_rec+"_ref"].rotation_quaternion.inverted() @ get_bone_global_rotation_quaternion(player_selected_rec, bodypart)

			# Recompute only with what is changing, instead of everything every time
			bodynodes_data["targetQuat"][bodypart] = bpy.data.objects[player_selected_rec+"_ref"].rotation_quaternion @ bodynodes_data["readQuat"][bodypart] @ bodynodes_data["offsetQuat"][bodypart] 
			player_bodypart.rotation_quaternion = bodynodes_data["targetQuat"][bodypart]
			if bodynodes_data["recording"]:
				recordOrientation(player_bodypart, bodypart)

			bodynodes_data["changed"][bodypart] = False

	return 0.02

def reinit_bn_data():
	global bodynodes_data
	bodynodes_data["targetQuat"] = {}
	bodynodes_data["offsetQuat"] = {}
	bodynodes_data["readQuat"] = {}
	bodynodes_data["reoriQuat"] = {}
	bodynodes_data["initOrieZ"] = {}

def load_armature_config_rec(filepath):
	global bodynodes_armature_config_rec
	with open(filepath) as file:
		bodynodes_armature_config_rec = json.load(file)

def load_armature_config_rec_def():
	dir_path = os.path.dirname(os.path.realpath(__file__))
	dir_path = dir_path.split("\\")[:-1]
	dir_path = "\\".join(dir_path)
	conf_file = dir_path+"\configs\\armature_config_rec.json"
	if os.path.isfile(conf_file):
		load_armature_config_rec(conf_file)

def save_armature_config_rec(filepath):
	global bodynodes_armature_config_rec
	with open(filepath, "w") as file:
		file.write(json.dumps(bodynodes_armature_config_rec, indent=4, sort_keys=True))

def load_armature():
	# print("load armature")
	global bodynodes_saved_armature
	for bodypart in bodynodes_armature_config_rec.keys():
		if bodynodes_armature_config_rec[bodypart]["bone_name"] == "":
			continue
		player_bodypart = get_bodynodeobj(bodypart)
		player_bodypart.rotation_quaternion = bodynodes_saved_armature[bodypart]

def save_armature():
	# print("save armature")
	global bodynodes_saved_armature
	bodynodes_saved_armature = {}
	for bodypart in bodynodes_armature_config_rec.keys():
		if bodynodes_armature_config_rec[bodypart]["bone_name"] == "":
			continue
		player_bodypart = get_bodynodeobj(bodypart)
		bodynodes_saved_armature[bodypart] = Quaternion((player_bodypart.rotation_quaternion))

def reset_armature():
	global bodynodes_armature_config_rec
	for bodypart in bodynodes_armature_config_rec.keys():
		if bodynodes_armature_config_rec[bodypart]["bone_name"] == "":
			continue
		player_bodypart = get_bodynodeobj(bodypart)
		player_bodypart.rotation_quaternion = bodynodes_objs_init[bodypart]

def reset_position_1():
	global player_selected_rec
	remove_bodynodes_from_player(player_selected_rec)
	reinit_bn_data()

def reset_position_2():
	time.sleep(5)
	apply_bodynodes_to_player(player_selected_rec)
	info_dialog_rec("Position has been reset")
	
def get_t_position():
	time.sleep(5)
	for bodypart in bodynodes_objs_init.keys():
		if bodypart in bodynodes_data["readQuat"]:
			bodynodes_tpos[bodypart] = bodynodes_objs_init[bodypart] @ bodynodes_data["readQuat"][bodypart].inverted()
	info_dialog_rec("T position taken")

def createQuanternion(bodypart, values):
	#print("createQuanternion")
	if bodypart not in bodynodes_armature_config_rec.keys() or bodynodes_armature_config_rec[bodypart]["bone_name"] == "":
		return

	quat = Quaternion((
		bodynodes_armature_config_rec[bodypart]["new_w_sign"] * float(values[bodynodes_armature_config_rec[bodypart]["new_w_val"]]),
		bodynodes_armature_config_rec[bodypart]["new_x_sign"] * float(values[bodynodes_armature_config_rec[bodypart]["new_x_val"]]),
		bodynodes_armature_config_rec[bodypart]["new_y_sign"] * float(values[bodynodes_armature_config_rec[bodypart]["new_y_val"]]),
		bodynodes_armature_config_rec[bodypart]["new_z_sign"] * float(values[bodynodes_armature_config_rec[bodypart]["new_z_val"]])
	))
	#print("bodypart = "+str(bodypart)+" - quat = "+str(quat))
	return quat

def read_orientations(data_json):
	if "bodypart" not in data_json:
		print("bodypart key missing in json")
		return

	if "type" not in data_json:
		print("type key missing in json")
		return

	if "value" not in data_json:
		print("value key missing in json")
		return
		
	bodypart_o = data_json["bodypart"] 
	values_str = data_json["value"]
	# print("read_orientations")
	# print(bodynodes_data)
	if not bodynodes_data["track"]:
		return
	
	values = values_str.split("|")
	if bodypart_o not in bodynodes_armature_config_rec.keys():
		print("Bodypart "+str(bodypart_o)+" not in bodynodes configuration")
		return

	bodypart = redirect_bodypart(bodypart_o) # bodypart redirection
	if player_selected_rec not in bpy.data.objects:
		print(player_selected_rec + " not found, Blender problem")
		return 
	
	if bodypart not in bpy.data.objects[player_selected_rec].pose.bones:
		print(bodypart+" bone has not been found")
		return

	bodynodes_data["readQuat"][bodypart] = createQuanternion(bodypart_o, values)

	bodynodes_data["changed"][bodypart] = True

def info_dialog_rec(text):
	global info_dialog_rec_obj
	info_dialog_rec_obj["text"] = text
	bpy.ops.object.dialog_rec_operator('INVOKE_DEFAULT')
						
def recordOrientation(player_bodypart, bodypart):
	global bodynodes_data
	global bodynodes_takes
	# print("recordOrientation")
	keyframe_info = {}
	keyframe_info["frame_current"] = bpy.context.scene.frame_current
	keyframe_info["rotation_quaternion"] = Quaternion((player_bodypart.rotation_quaternion))
	player_bodypart.keyframe_insert(data_path='rotation_quaternion', frame=(keyframe_info["frame_current"]))

	if bodypart not in bodynodes_takes[bodynodes_data["take"]]:
		bodynodes_takes[bodynodes_data["take"]][bodypart] = []	

	bodynodes_takes[bodynodes_data["take"]][bodypart].append(keyframe_info)

def readOFromConnection(data_str):
	# print("readOFromConnection")
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
					read_orientations(data_json_single)
			else:
				read_orientations(data_json)

class AcceptConnection(threading.Thread):
	def __init__(self, name, socket):
		threading.Thread.__init__(self, target=self.run, name=name, args=())
		self.socket = socket

	def run(self):
		# print("AcceptConnection ready")
		self.killed = False
		self.handleConnection = {}
		while not self.killed:

			bytesAddressPair = self.socket.recvfrom(bodynodes_server["buffer_size"])
			message = bytesAddressPair[0]
			address = bytesAddressPair[1]
			message_str = message.decode("utf-8").rstrip('\x00')
			clientMsg = "Message from Client:{}".format(message)
			clientIP  = "Client IP Address:{}".format(address)

			if "ACK" in message_str:
				print("ACK Message received ...")
				print(clientMsg)
				print(clientIP)
				print("Sending ACK to address = "+clientIP)
				self.socket.sendto(str.encode("ACK"), address)
			else:
				readOFromConnection(message_str)
		# print("AcceptConnection stopping")
	def stop(self):
		self.killed = True

def clear_any_recording():
	global bodynodes_data
	start = bpy.context.scene.frame_start
	end = bpy.context.scene.frame_end
	for fc in range(start, end+1):
		for bodypart in bodynodes_data["readQuat"].keys():
			player_bodypart = get_bodynodeobj(bodypart)
			try:
				player_bodypart.keyframe_delete(data_path='rotation_quaternion', frame=(fc))
			except:
				pass

def take_recording():
	global bodynodes_data
	global bodynodes_takes
	global bodynodes_panel_rec
	
	# print("take_recording")
	if bodynodes_data["take"]==None:
		print("Select which Take first")
		return

	time.sleep(4)
	enable_tracking()
	clear_any_recording()
	# Sync, Drop frames to maintain framerate
	bpy.ops.screen.animation_play(sync=True)
	bodynodes_panel_rec["recording"]["status"] = "Started"

	bodynodes_takes[bodynodes_data["take"]] = {}
	bodynodes_takes[bodynodes_data["take"]]["start"] = bpy.context.scene.frame_start
	bodynodes_takes[bodynodes_data["take"]]["end"] = bpy.context.scene.frame_end
	bodynodes_data["recording"] = True

def apply_recording(which):
	global bodynodes_data
	global bodynodes_takes
	if which==None:
		print("None Take is selected")
		return

	which_str = str(which+1)
	if "start" not in bodynodes_takes[which]:
		print("Take "+which_str+" not done")
		return

	for bodypart in bodynodes_takes[which].keys():
		if bodypart == "start" or bodypart == "end":
			continue
		bodypart_keyframes = bodynodes_takes[which][bodypart]
		for keyframe_info in bodypart_keyframes:
			player_bodypart = get_bodynodeobj(bodypart)
			player_bodypart.rotation_quaternion = keyframe_info["rotation_quaternion"]
			player_bodypart.keyframe_insert(data_path='rotation_quaternion', frame=(keyframe_info["frame_current"]))

def stop_animation():
	global bodynodes_data
	global bodynodes_panel_rec
	bodynodes_data["recording"] = False
	bpy.ops.screen.animation_cancel(False)
	bodynodes_panel_rec["recording"]["status"] = "Stopped"

def clear_recordings():
	global bodynodes_takes
	bodynodes_takes = [{}, {}, {}]

def who_got_bodynodes():
	for player in players_available:
		player_name = player[0]
		if player_name in bpy.data.objects:
			if "Copy Rotation" in bpy.data.objects[player_name].pose.bones["lowerleg_left"].constraints:
				return player_name
	return "None"

def remove_bodynodes_from_player(player_selected_rec):
	if player_selected_rec not in bpy.data.objects:
		return
	for bodypart in bodynodes_objs_init.keys():
		if "Copy Rotation" in bpy.data.objects[player_selected_rec].pose.bones[bodypart].constraints:
			bpy.data.objects[player_selected_rec].pose.bones[bodypart].constraints.remove(
				bpy.data.objects[player_selected_rec].pose.bones[bodypart].constraints["Copy Rotation"]
			)
		
def apply_bodynodes_to_player(player_selected_rec):
	if player_selected_rec not in bpy.data.objects:
		return
	for bodypart in bodynodes_armature_config_rec.keys():
		if bodynodes_armature_config_rec[bodypart]["bone_name"] == "":
			continue
			
		bpy.data.objects[bodypart].rotation_quaternion = get_bone_global_rotation_quaternion(player_selected_rec, bodypart)
		if "Copy Rotation" not in bpy.data.objects[player_selected_rec].pose.bones[bodypart].constraints:
			bpy.data.objects[player_selected_rec].pose.bones[bodypart].constraints.new(type = 'COPY_ROTATION')
			bpy.data.objects[player_selected_rec].pose.bones[bodypart].constraints["Copy Rotation"].target = bpy.data.objects[bodypart]

def start_server():
	# print("start_server")
	if bodynodes_server["socket"]:
		print("Socket is already there...")
		return

	# Sets the reference to be correctly read in main_read_orientations
	bpy.data.objects[player_selected_rec+"_ref"].rotation_mode = "QUATERNION"

	reinit_bn_data()

	print("Creating socket ...")
	bodynodes_server["socket"] = socket(AF_INET, SOCK_DGRAM)
	print("Binding socket ...")

	try:
		print("Now running ...")
		bodynodes_server["socket"].bind((bodynodes_server["host"], bodynodes_server["port"]))	
		# bodynodes_server["socket"].listen(1)
	except:
		bodynodes_panel_rec["server"]["status"] = "Error starting server"
		bodynodes_server["socket"] = None
		print("Have you forgotten to create the hotspot?")
		raise

	print("Starting connection")
	bodynodes_server["connection"] = AcceptConnection("accepter", bodynodes_server["socket"])
	bodynodes_server["connection"].start()
	bodynodes_panel_rec["server"]["running"] = True
	bodynodes_panel_rec["server"]["status"] = "Running"
	info_dialog_rec("Server has started")


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
		
	bodynodes_panel_rec["server"]["status"] = "Server not running"
	bodynodes_panel_rec["server"]["running"] = False
	bodynodes_panel_rec["recording"]["status"] = "Start Server"

def enable_tracking():
	bodynodes_data["track"] = True

def enabledisable_tracking():
	bodynodes_data["track"] = not bodynodes_data["track"]

def take_recording_fun(self, context):
	which = int(self.take_recording_list)
	if which > 2:
		which = None
	clear_any_recording()
	bodynodes_data["take"] = which
	apply_recording(which)
		
def change_recording_player_fun(self, context):
	global player_selected_rec
	remove_bodynodes_from_player(player_selected_rec)
	player_selected_rec = self.players_list_recording
	apply_bodynodes_to_player(player_selected_rec)

def save_animation_rec(filepath):
	start = bpy.context.scene.frame_start
	end = bpy.context.scene.frame_end
	animation_json = {}
	for bodypart in bodynodes_armature_config_rec.keys():
		if bodynodes_armature_config_rec[bodypart]["bone_name"] == "":
			continue
		animation_json[bodypart] = []

	for bodypart in animation_json.keys():
		for frame in range(start, end+1):
			bpy.context.scene.frame_set(frame)
			obj_quat = Quaternion((get_bodynode_rotation_quaternion(bodypart)))
			keyframe_info = {
				"rotation_quaternion" : [ obj_quat.w, obj_quat.x, obj_quat.y, obj_quat.z ],
				"frame_current" : frame - start
			}
			animation_json[bodypart].append(keyframe_info)

	with open(filepath, "w") as file:
		file.write(json.dumps(animation_json, indent=4, sort_keys=True))

def redirect_bodypart(bodypart):
	# print("redirect_bodypart")
	global bodynodes_armature_config_rec
	if bodypart in bodynodes_armature_config_rec.keys() and bodynodes_armature_config_rec[bodypart]["bone_name"] != "":
		return bodynodes_armature_config_rec[bodypart]["bone_name"]
	return "none"

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

bpy.types.Scene.take_recording_list = bpy.props.EnumProperty(items = (
	('0','Take 1',''),
	('1','Take 2',''),
	('2','Take 3',''),
	('3','None',''),
	),
	default = '3',
	description = "Animation take considered",
	update=take_recording_fun)

bpy.types.Scene.players_list_recording = bpy.props.EnumProperty(items= players_available,
	name = "Player",
	description = "Player to consider for recording",
	update = change_recording_player_fun)

bpy.context.scene.take_recording_list = '3'
bpy.context.scene.players_list_recording = "None"

class PANEL_PT_BodynodesRecording(bpy.types.Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'View'
	bl_label = "Bodynodes Recording"

	def draw(self, context):
		layout = self.layout

		row = layout.row()
		row.operator("bodynodes.load_armature_config_rec", text="Load Bones Config")
		row.enabled = True
			
		if not bodynodes_armature_config_rec:
			row = layout.row()
			row.scale_y = 1.0
			col1 = row.column()
			col1.label(text="Load a configuration file")
			return

		row = layout.row()
		row.prop(context.scene, 'players_list_recording')

		if player_selected_rec not in bpy.data.objects:
			row = layout.row()
			row.scale_y = 1.0
			col1 = row.column()
			col1.label(text="Select a player")
			return

		# Big render button
		layout.label(text="Server:   "  + bodynodes_panel_rec["server"]["status"])
		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.operator("bodynodes.startstop_server",
			text="Stop" if bodynodes_panel_rec["server"]["running"] else "Start")
		col1.enabled = True

		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.label(text="Tracking:")
		col2 = row.column()
		col2.operator("bodynodes.enabledisable_tracking", 
			text="Disable" if bodynodes_data["track"] else "Enable")
		col2.enabled = True
	
		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.label(text="Armature:")
		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.operator("bodynodes.save_armature", text="Save")
		col1.enabled = True
		col2 = row.column()
		col2.operator("bodynodes.load_armature", text="Load")
		col2.enabled = True
		col3 = row.column()
		col3.operator("bodynodes.reset_armature", text="Reset")
		col3.enabled = True
		
		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.label(text="Bones Config:")
		col1.ui_units_x = 15
		col2 = row.column()
		col2.operator("bodynodes.change_armature_config", text="Change")
		col2.enabled = True
		col3 = row.column()
		col3.operator("bodynodes.save_armature_config_rec", text="Save")
		col3.enabled = True

		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.label(text="Reset position")
		col2 = row.column()
		col2.operator("bodynodes.reset_position_1", text="Step 1")
		col2.enabled = True
		col3 = row.column()
		col3.operator("bodynodes.reset_position_2", text="Step 2")
		col3.enabled = True

		layout.label(text="Recording:   " + bodynodes_panel_rec["recording"]["status"])
		row = layout.row()
		row.prop(context.scene, 'take_recording_list', expand=True)
		
		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.operator("bodynodes.take_recording", text="Take")
		col1.enabled = bodynodes_panel_rec["server"]["running"]
		col2 = row.column()
		col2.operator("bodynodes.clear_recordings", text="Clear")
		col2.enabled = True

		row = layout.row()
		col1 = row.column()
		col1.operator("bodynodes.save_animation_rec", text="Save Anim")
		col1.enabled = True

		row = layout.row()
		row.operator("bodynodes.close_recording", text="Close")

class BodynodesStartStopServerOperator(bpy.types.Operator):
	bl_idname = "bodynodes.startstop_server"
	bl_label = "StartStop Server Operator"
	bl_description = "Starts/Stop the local server. It resets position of the sensors at every start"

	def execute(self, context):
		if bodynodes_panel_rec["server"]["running"]:
			stop_animation()
			stop_server()
		else:
			bpy.app.timers.register(start_server, first_interval=4.0)

		return {'FINISHED'}

class BodynodesTakeRecordingOperator(bpy.types.Operator):
	bl_idname = "bodynodes.take_recording"
	bl_label = "Take Recording Operator"
	bl_description = "Start taking recording. The recording starts after 4 seconds. Recording is saved in selected take"

	def execute(self, context):
		take_recording()
		return {'FINISHED'}

class BodynodesClearRecordingsOperator(bpy.types.Operator):
	bl_idname = "bodynodes.clear_recordings"
	bl_label = "Clear Recordings Operator"
	bl_description = "Clears all the taken recordings"

	def execute(self, context):
		clear_recordings()
		return {'FINISHED'}

class BodynodesEnableDisableTrackingOperator(bpy.types.Operator):
	bl_idname = "bodynodes.enabledisable_tracking"
	bl_label = "Toggle Tracking Operator"
	bl_description = "Enable/Disable the tracking bodynodes-bones"

	def execute(self, context):
		enabledisable_tracking()
		return {'FINISHED'}

class BodynodesSaveArmatureOperator(bpy.types.Operator):
	bl_idname = "bodynodes.save_armature"
	bl_label = "Save Armature Operator"
	bl_description = "Save armature posture temporarily"

	def execute(self, context):
		save_armature()
		return {'FINISHED'}

class BodynodesLoadArmatureOperator(bpy.types.Operator):
	bl_idname = "bodynodes.load_armature"
	bl_label = "Load Armature Operator"
	bl_description = "Load armature posture temporarily"

	def execute(self, context):
		load_armature()
		return {'FINISHED'}

class BodynodesResetArmatureOperator(bpy.types.Operator):
	bl_idname = "bodynodes.reset_armature"
	bl_label = "Reset Armature Operator"
	bl_description = "Reset armature posture"

	def execute(self, context):
		reset_armature()
		return {'FINISHED'}

class BodynodesResetPosition1Operator(bpy.types.Operator):
	bl_idname = "bodynodes.reset_position_1"
	bl_label = "Reset Position 1 Operator"
	bl_description = "Reset position bodynodes step 1"

	def execute(self, context):
		reset_position_1()
		return {'FINISHED'}

class BodynodesResetPosition2Operator(bpy.types.Operator):
	bl_idname = "bodynodes.reset_position_2"
	bl_label = "Reset Position 2 Operator"
	bl_description = "Reset position bodynodes step 2"

	def execute(self, context):
		reset_position_2()
		return {'FINISHED'}

class BodynodesGetTPositionOperator(bpy.types.Operator):
	bl_idname = "bodynodes.get_t_position"
	bl_label = "Get T Position Operator"
	bl_description = "Get T position bodynodes"

	def execute(self, context):
		get_t_position()
		return {'FINISHED'}

class BodynodesChangeArmatureConfigMenu(bpy.types.Operator) : 
	bl_idname = "bodynodes.change_armature_config"  
	bl_label = "Change Armature Config"  
	bl_description = "Change the armature configuration for axis, bodypart, Bodynodes sensor"
	bl_options = {"REGISTER", "UNDO"} 
	
	bodypart_to_change = bpy.props.EnumProperty(items= (
												 ('none', 'none', ''),
												 ('head', 'head', ''),
												 ('forearm_right', 'forearm_right', ''),
												 ('forearm_left', 'forearm_left', ''),
												 ('upperleg_left', 'upperleg_left', ''),
												 ('lowerleg_right', 'lowerleg_right', ''),
												 ('lowerleg_left', 'lowerleg_left', ''),
												 ('upperleg_right', 'upperleg_right', ''),
												 ('upperarm_right', 'upperarm_right', ''),
												 ('upperarm_left', 'upperarm_left', ''),
												 ('lowerbody', 'lowerbody', ''),
												 ('upperbody', 'upperbody', '')),
												 name = "Bodypart")

	global player_selected_rec
	bones_items = ( )

	bones_items = bones_items + (('none', 'none', ''),)
	for bone in bodynodes_objs_init.keys():
		bones_items = bones_items + ((bone, bone, ''),)
		
	new_bone_name = bpy.props.EnumProperty(items= bones_items,
												 name = "Bone Name")
	
	new_w_axis = bpy.props.EnumProperty(items= (('0', 'W', ''),
												 ('1', 'X', ''),
												 ('2', 'Y', ''),
												 ('3', 'Z', ''),
												 ('4', '-W', ''),
												 ('5', '-X', ''),
												 ('6', '-Y', ''),
												 ('7', '-Z', '')),
												 name = "Axis W")

	new_x_axis = bpy.props.EnumProperty(items= (('1', 'X', ''),
												 ('0', 'W', ''),
												 ('2', 'Y', ''),
												 ('3', 'Z', ''),
												 ('5', '-X', ''),
												 ('4', '-W', ''),
												 ('6', '-Y', ''),
												 ('7', '-Z', '')),
												 name = "Axis X")

	new_y_axis = bpy.props.EnumProperty(items= (('2', 'Y', ''),
												 ('0', 'W', ''),
												 ('1', 'X', ''),
												 ('3', 'Z', ''),
												 ('6', '-Y', ''),												 ('1', 'X', ''),
												 ('4', '-W', ''),
												 ('5', '-X', ''),
												 ('7', '-Z', '')),
												 name = "Axis Y")



	new_z_axis = bpy.props.EnumProperty(items= (('3', 'Z', ''),
												 ('1', 'X', ''),
												 ('2', 'Y', ''),
												 ('0', 'W', ''),
												 ('7', '-Z', ''),
												 ('5', '-X', ''),
												 ('6', '-Y', ''),
												 ('4', '-W', '')),
												 name = "Axis Z")

	def execute(self, context):
		global bodynodes_armature_config_rec
		global bodynodes_data
		
		bodypart_to_change = str(self.bodypart_to_change)
		new_bone_name = str(self.new_bone_name)
		if bodypart_to_change == "none" or new_bone_name == "none":
			return {"FINISHED"} 
		
		new_w_axis = int(self.new_w_axis)
		new_x_axis = int(self.new_x_axis)
		new_y_axis = int(self.new_y_axis)
		new_z_axis = int(self.new_z_axis)

		if new_w_axis > 3:
			bodynodes_armature_config_rec[bodypart_to_change]["new_w_sign"] = -1
			new_w_axis -= 4
		else:
			bodynodes_armature_config_rec[bodypart_to_change]["new_w_sign"] = 1
		
		if new_x_axis > 3:
			bodynodes_armature_config_rec[bodypart_to_change]["new_x_sign"] = -1
			new_x_axis -= 4
		else:
			bodynodes_armature_config_rec[bodypart_to_change]["new_x_sign"] = 1
		
		if new_y_axis > 3:
			bodynodes_armature_config_rec[bodypart_to_change]["new_y_sign"] = -1
			new_y_axis -= 4
		else:
			bodynodes_armature_config_rec[bodypart_to_change]["new_y_sign"] = 1

		if new_z_axis > 3:
			bodynodes_armature_config_rec[bodypart_to_change]["new_z_sign"] = -1
			new_z_axis -= 4
		else:
			bodynodes_armature_config_rec[bodypart_to_change]["new_z_sign"] = 1

		bodynodes_armature_config_rec[bodypart_to_change]["new_w_val"] = new_w_axis
		bodynodes_armature_config_rec[bodypart_to_change]["new_x_val"] = new_x_axis
		bodynodes_armature_config_rec[bodypart_to_change]["new_y_val"] = new_y_axis
		bodynodes_armature_config_rec[bodypart_to_change]["new_z_val"] = new_z_axis		
		bodynodes_armature_config_rec[bodypart_to_change]["bone_name"] = new_bone_name

		bodynodes_data["targetQuat"] = {}
		bodynodes_data["offsetQuat"] = {}
		bodynodes_data["readQuat"] = {}
		bodynodes_data["reoriQuat"] = {}
		bodynodes_data["initOrieZ"] = {}
	
		return {"FINISHED"} 

class BodynodesSaveArmatureConfigRecOperator(bpy.types.Operator, ExportHelper):
	bl_idname = "bodynodes.save_armature_config_rec"
	bl_label = "Save Armature Config Operator"
	bl_description = "Save the armature configuration in a json file"

	# ExportHelper mixin class uses this
	filename_ext = ".json"

	filter_glob: bpy.props.StringProperty(
		default="*.json",
		options={'HIDDEN'},
		maxlen=255,  # Max internal buffer length, longer would be clamped.
	)
	
	def execute(self, context):
		save_armature_config_rec(self.filepath)
		return {'FINISHED'}

class BodynodesLoadArmatureConfigRecOperator(bpy.types.Operator, ImportHelper):
	bl_idname = "bodynodes.load_armature_config_rec"
	bl_label = "Load Armature Configuration Operator"
	bl_description = "Load armature configuration from a json file"

	filter_glob: bpy.props.StringProperty( 
		default='*.json',
		options={'HIDDEN'}
	)

	def execute(self, context):
		load_armature_config_rec(self.filepath)
		return {'FINISHED'}

class BodynodesSaveAnimationRecOperator(bpy.types.Operator, ExportHelper):
	bl_idname = "bodynodes.save_animation_rec"
	bl_label = "Save Animation Operator"
	bl_description = "Save animation in a json file"

	# ExportHelper mixin class uses this
	filename_ext = ".json"

	filter_glob: bpy.props.StringProperty(
		default="*.json",
		options={'HIDDEN'},
		maxlen=255,  # Max internal buffer length, longer would be clamped.
	)
	
	def execute(self, context):
		save_animation_rec(self.filepath)
		return {'FINISHED'}

class InfoDialogRecOperator(bpy.types.Operator):
	bl_idname = "object.dialog_rec_operator"
	bl_label = "Info"

	def execute(self, context):
		# Invoked when Ok is clicked
		global info_dialog_rec_obj
		info_dialog_rec_obj["is_visible"] = False
		return {'FINISHED'}

	def invoke(self, context, event):
		global info_dialog_rec_obj
		if not info_dialog_rec_obj["is_visible"]:
			info_dialog_rec_obj["is_visible"] = True
			wm = context.window_manager
			return wm.invoke_props_dialog(self)
		else:
			return {'FINISHED'}

		
	def draw(self, context):
		global info_dialog_rec_obj
		layout = self.layout
		col = layout.column()
		col.label(text=info_dialog_rec_obj["text"])

class BodynodesCloseRecordingOperator(bpy.types.Operator):
	bl_idname = "bodynodes.close_recording"
	bl_label = "Close Recording Panel Operator"
	bl_description = "Close the Bodynodes recording panel"

	def execute(self, context):
		stop_animation()
		stop_server()
		unregister_recording()
		return {'FINISHED'}

def register_recording() :
	bpy.utils.register_class(BodynodesStartStopServerOperator)
	bpy.utils.register_class(BodynodesTakeRecordingOperator)
	bpy.utils.register_class(BodynodesClearRecordingsOperator)
	bpy.utils.register_class(BodynodesEnableDisableTrackingOperator)
	bpy.utils.register_class(BodynodesResetPosition1Operator)
	bpy.utils.register_class(BodynodesResetPosition2Operator)
	bpy.utils.register_class(BodynodesSaveArmatureOperator)
	bpy.utils.register_class(BodynodesLoadArmatureOperator)
	bpy.utils.register_class(BodynodesResetArmatureOperator)
	bpy.utils.register_class(BodynodesChangeArmatureConfigMenu)
	bpy.utils.register_class(BodynodesSaveArmatureConfigRecOperator)
	bpy.utils.register_class(BodynodesLoadArmatureConfigRecOperator)
	bpy.utils.register_class(BodynodesSaveAnimationRecOperator)
	bpy.utils.register_class(BodynodesCloseRecordingOperator)
	
	bpy.utils.register_class(PANEL_PT_BodynodesRecording)
	bpy.utils.register_class(InfoDialogRecOperator)
	
	bpy.app.timers.register(main_read_orientations)
	bpy.app.handlers.frame_change_pre.append(stop_at_last_frame)

def unregister_recording() :
	bpy.utils.unregister_class(BodynodesStartStopServerOperator)
	bpy.utils.unregister_class(BodynodesTakeRecordingOperator)
	bpy.utils.unregister_class(BodynodesClearRecordingsOperator)
	bpy.utils.unregister_class(BodynodesEnableDisableTrackingOperator)
	bpy.utils.unregister_class(BodynodesResetPosition1Operator)
	bpy.utils.unregister_class(BodynodesResetPosition2Operator)
	bpy.utils.unregister_class(BodynodesSaveArmatureOperator)
	bpy.utils.unregister_class(BodynodesLoadArmatureOperator)
	bpy.utils.unregister_class(BodynodesResetArmatureOperator)
	bpy.utils.unregister_class(BodynodesChangeArmatureConfigMenu)
	bpy.utils.unregister_class(BodynodesSaveArmatureConfigRecOperator)
	bpy.utils.unregister_class(BodynodesLoadArmatureConfigRecOperator)
	bpy.utils.unregister_class(BodynodesSaveAnimationRecOperator)
	bpy.utils.unregister_class(BodynodesCloseRecordingOperator)
	
	bpy.utils.unregister_class(PANEL_PT_BodynodesRecording)
	bpy.utils.unregister_class(InfoDialogRecOperator)
	
	bpy.app.timers.unregister(main_read_orientations)
	bpy.app.handlers.frame_change_pre.clear()

def stop_at_last_frame(scene):
	if scene.frame_current == scene.frame_end-1:
		stop_animation()

if __name__ == "__main__" :
	player_selected_rec = who_got_bodynodes()
	remove_bodynodes_from_player(player_selected_rec)
	bpy.context.scene.players_list_recording = player_selected_rec
	save_armature()
	register_recording()
	load_armature_config_rec_def()
	




