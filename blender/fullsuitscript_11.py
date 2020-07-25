# MIT License
# 
# Copyright (c) 2019-2020 Manuel Bottini
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
import threading
import json
import bpy
from mathutils import *
import time
import queue

# This script is made for the FullSuit-11

players_available = (('BlueGuy', 'BlueGuy', ''), ('RedGuy', 'RedGuy', ''))

player_selected = "BlueGuy"

bodynodes_puppet_original_rot = {
	"head" : Quaternion((-3.0908619663705394e-08, 0.7071067690849304, 0.7071068286895752, -3.0908619663705394e-08)),
	"forearm_right" : Quaternion((0.7071068286895752, 0.7071068286895752, 0.0, 0.0)),
	"forearm_left" : Quaternion((-3.0908619663705394e-08, 3.090862676913275e-08, 0.7071068286895752, 0.7071068286895752)),
	"upperleg_left" : Quaternion((0.0, 0.7071070075035095, 0.7071070075035095, 0.0)),
	"lowerleg_right" : Quaternion((0.0, 0.7071070075035095, 0.7071070075035095, 0.0)),
	"lowerleg_left" : Quaternion((0.0, 0.7071070075035095, 0.7071070075035095, 0.0)),
	"upperleg_right" : Quaternion((-3.0908619663705394e-08, 0.7071070075035095, 0.7071067690849304, 3.0908619663705394e-08)),
	"upperarm_right" : Quaternion((0.7071068286895752, 0.7071068286895752, 0.0, 0.0)),
	"upperarm_left" : Quaternion((-3.0908619663705394e-08, 3.090862676913275e-08, 0.7071068286895752, 0.7071068286895752)),
	"lowerbody" : Quaternion((0.0, 0.707107, 0.707107, 0.0)),
	"upperbody" : Quaternion((0.7071070075035095, 0.0, 0.0, 0.7071068286895752)),
	"fullbody" : Quaternion((0.7071070075035095, 0.0, 0.0, 0.7071068286895752))
}

bodynodes_puppet_saved_rot = {}

bodynodes_puppet_saved_change_anim = {}


bodynodes_sensor_axis = {
	"head" : {
		"new_w_val" : 0,
		"new_x_val" : 2,
		"new_y_val" : 3,
		"new_z_val" : 1,
		
		"new_w_sign" : 1,
		"new_x_sign" : 1,
		"new_y_sign" : -1,
		"new_z_sign" : -1
	},
	"forearm_right" : {
		"new_w_val" : 0,
		"new_x_val" : 2,
		"new_y_val" : 3,
		"new_z_val" : 1,
		
		"new_w_sign" : 1,
		"new_x_sign" : 1,
		"new_y_sign" : 1,
		"new_z_sign" : 1
	},
	"forearm_left" : {
		"new_w_val" : 0,
		"new_x_val" : 2,
		"new_y_val" : 3,
		"new_z_val" : 1,
		
		"new_w_sign" : 1,
		"new_x_sign" : 1,
		"new_y_sign" : 1,
		"new_z_sign" : 1
	},
	"upperleg_left" : {
		"new_w_val" : 0,
		"new_x_val" : 1,
		"new_y_val" : 3,
		"new_z_val" : 2,
		
		"new_w_sign" : 1,
		"new_x_sign" : 1,
		"new_y_sign" : -1,
		"new_z_sign" : 1
	},
	"lowerleg_right" : {
		"new_w_val" : 0,
		"new_x_val" : 1,
		"new_y_val" : 3,
		"new_z_val" : 2,
		
		"new_w_sign" : 1,
		"new_x_sign" : 1,
		"new_y_sign" : -1,
		"new_z_sign" : 1
	},
	"lowerleg_left" : {
		"new_w_val" : 0,
		"new_x_val" : 1,
		"new_y_val" : 3,
		"new_z_val" : 2,
		
		"new_w_sign" : 1,
		"new_x_sign" : 1,
		"new_y_sign" : -1,
		"new_z_sign" : 1
	},
	"upperleg_right" : {
		"new_w_val" : 0,
		"new_x_val" : 1,
		"new_y_val" : 3,
		"new_z_val" : 2,
		
		"new_w_sign" : 1,
		"new_x_sign" : 1,
		"new_y_sign" : -1,
		"new_z_sign" : 1
	},
	"upperarm_right" : {
		# To reinstate once the original node is fixed
		#"new_w_val" : 0,
		#"new_x_val" : 2,
		#"new_y_val" : 3,
		#"new_z_val" : 1,
		
		#"new_w_sign" : 1,
		#"new_x_sign" : -1,
		#"new_y_sign" : 1,
		#"new_z_sign" : -1
		
		"new_w_val" : 0,
		"new_x_val" : 1,
		"new_y_val" : 3,
		"new_z_val" : 2,
		
		"new_w_sign" : -1,
		"new_x_sign" : -1,
		"new_y_sign" : 1,
		"new_z_sign" : -1
	},
	"upperarm_left" : {
		"new_w_val" : 0,
		"new_x_val" : 2,
		"new_y_val" : 3,
		"new_z_val" : 1,
		
		"new_w_sign" : 1,
		"new_x_sign" : -1,
		"new_y_sign" : 1,
		"new_z_sign" : -1
	},
	"lowerbody" : {
		"new_w_val" : 0,
		"new_x_val" : 2,
		"new_y_val" : 3,
		"new_z_val" : 1,
		
		"new_w_sign" : 1,
		"new_x_sign" : 1,
		"new_y_sign" : -1,
		"new_z_sign" : -1
	},
	"upperbody" : {
		"new_w_val" : 0,
		"new_x_val" : 2,
		"new_y_val" : 3,
		"new_z_val" : 1,
		
		"new_w_sign" : 1,
		"new_x_sign" : 1,
		"new_y_sign" : 1,
		"new_z_sign" : 1
	}
}

bodynodes_data = {
	"targetQuat": {},
	"changed": {},
	"startQuat": {},
	"offsetQuat": {},
	"readQuat": {},
	"reoriQuat": {},
	"recording": False,
	"take": None,
	"track" : True
}

bodynodes_panel = {
	"server_status": "Server not running",
	"anim_status": "Start Server",
	"track_status": "Tracking Enabled"
}

bodynodes_server = {
	"host": "192.168.137.1",
	"port": 12345,
	"buffer_size": 1024,
	"socket": None,
	"connection": None
}

bodynodes_takes = [{}, {}, {}]

def main_read_orientations():
	global player_selected
	for bodypart in bodynodes_data["readQuat"]:
		if bodypart in bodynodes_data["changed"] and bodynodes_data["changed"][bodypart]:
			player_bodypart = get_bodypart_blobj(player_selected, bodypart)
			if bodypart not in bodynodes_data["startQuat"]:
				bodynodes_data["startQuat"][bodypart] = Quaternion((player_bodypart.rotation_quaternion))

			bodynodes_data["targetQuat"][bodypart] = bodynodes_data["startQuat"][bodypart] @ bodynodes_data["offsetQuat"][bodypart] @ bodynodes_data["readQuat"][bodypart] 
			player_bodypart.rotation_mode = 'QUATERNION'
			player_bodypart.rotation_quaternion = bodynodes_data["targetQuat"][bodypart]

			if bodynodes_data["recording"]:
				recordOrientation(player_bodypart, bodypart)

			bodynodes_data["changed"][bodypart] = False

	return 0.02

def reinit_bn_data():
	global bodynodes_data
	bodynodes_data["targetQuat"] = {}
	bodynodes_data["startQuat"] = {}
	bodynodes_data["offsetQuat"] = {}
	bodynodes_data["readQuat"] = {}
	bodynodes_data["reoriQuat"] = {}
	bodynodes_data["initOrieZ"] = {}
	
def get_bodypart_blobj(player, bodypart):
	# print("get_bodypart_blobj")
	return bpy.data.objects[player+"_"+bodypart]
	
def change_bodypart(bodypart):
	# print("change_bodypart")
	
	#if bodypart == "lowerleg_left":
	#	return "upperarm_right"
	
	return bodypart

def reset_puppets_original_rotations():
	# print("reset_puppets_original_rotations")
	global players_available
	for player_obj in players_available:
		player = player_obj[0]
		for bodypart in bodynodes_puppet_original_rot.keys():
			get_bodypart_blobj(player, bodypart).rotation_quaternion = bodynodes_puppet_original_rot[bodypart]

def load_puppet_rotations():
	# print("load_puppet_rotations")
	global player_selected
	global bodynodes_puppet_saved_rot
	for bodypart in bodynodes_puppet_saved_rot.keys():
		get_bodypart_blobj(player_selected, bodypart).rotation_quaternion = bodynodes_puppet_saved_rot[bodypart]

def save_puppet_rotations():
	# print("save_rotations")
	global player_selected
	global bodynodes_puppet_saved_rot
	bodynodes_puppet_saved_rot = {}
	for bodypart in bodynodes_puppet_original_rot.keys():
		obj_quat = get_bodypart_blobj(player_selected, bodypart).rotation_quaternion
		bodynodes_puppet_saved_rot[bodypart] = Quaternion((obj_quat))

def createQuanternion(bodypart, values):
	#print("createQuanternion")
	quat = Quaternion((
		bodynodes_sensor_axis[bodypart]["new_w_sign"] * float(values[bodynodes_sensor_axis[bodypart]["new_w_val"]]),
		bodynodes_sensor_axis[bodypart]["new_x_sign"] * float(values[bodynodes_sensor_axis[bodypart]["new_x_val"]]),
		bodynodes_sensor_axis[bodypart]["new_y_sign"] * float(values[bodynodes_sensor_axis[bodypart]["new_y_val"]]),
		bodynodes_sensor_axis[bodypart]["new_z_sign"] * float(values[bodynodes_sensor_axis[bodypart]["new_z_val"]])
	))
	print("bodypart = "+str(bodypart)+" - quat = "+str(quat))
	return quat

def read_orientations(bodypart, values_str):
	# print("read_orientations")
	# print(bodynodes_data)
	if not bodynodes_data["track"]:
		return
	
	values = values_str.split("|")
	if bodypart not in bodynodes_sensor_axis:
		print("Bodypart "+str(bodypart)+" not in bodynodes configuration")
		return
	
	bodynodes_data["readQuat"][bodypart] = createQuanternion(bodypart, values)

	if bodypart not in bodynodes_data["offsetQuat"]:
		bodynodes_data["offsetQuat"][bodypart] =  bodynodes_data["readQuat"][bodypart].inverted()
		# print(bodynodes_data["offsetQuat"][bodypart])
		# print(bodynodes_data["readQuat"][bodypart])

	bodynodes_data["changed"][bodypart] = True


def recordOrientation(player_bodypart, bodypart):
	global bodynodes_data
	global bodynodes_takes
	# print("recordOrientation")
	keyframe_info = {}
	keyframe_info["frame_current"] = bpy.context.scene.frame_current
	keyframe_info["orientation"] = Quaternion((player_bodypart.rotation_quaternion))
	player_bodypart.keyframe_insert(data_path='rotation_quaternion', frame=(keyframe_info["frame_current"]))

	if bodypart not in bodynodes_takes[bodynodes_data["take"]]:
		bodynodes_takes[bodynodes_data["take"]][bodypart] = []	

	bodynodes_takes[bodynodes_data["take"]][bodypart].append(keyframe_info)

def readOFromSingleJson(data_json):
	global player_selected
	# print("readOFromSingleJson")
	if "bodypart" not in data_json:
		print("bodypart key missing in json")
		return

	if "type" not in data_json:
		print("type key missing in json")
		return

	if "value" not in data_json:
		print("value key missing in json")
		return

	bodypart = change_bodypart(data_json["bodypart"])

	if player_selected + "_" + bodypart not in bpy.data.objects:
		print(bodypart+" bodypart has not been found in Puppet Object")
		return

	#[w,x,y,z]
	read_orientations(bodypart, data_json["value"])
		

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
					readOFromSingleJson(data_json_single)
			else:
				readOFromSingleJson(data_json)

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

def remove_animation(which):
	global bodynodes_data
	global bodynodes_takes
	if "start" not in bodynodes_takes[which]:
		return

	start = bodynodes_takes[which]["start"]
	end = bodynodes_takes[which]["end"]
	for fc in range(start, end+1):
		for bodypart in bodynodes_takes[which].keys():
			if bodypart == "start" or bodypart == "end":
				continue
			player_bodypart = get_bodypart_blobj(player_selected, bodypart)
			player_bodypart.keyframe_delete(data_path='rotation_quaternion', frame=(fc))


def take_animation():
	global bodynodes_data
	global bodynodes_takes
	# print("take_animation")
	if bodynodes_data["take"]==None:
		print("Select which Take first")
		return
	
	time.sleep(4)
	enable_tracking()
	reinit_bn_data()
	remove_animation(0)
	remove_animation(1)
	remove_animation(2)
	# Sync, Drop frames to maintain framerate
	bpy.ops.screen.animation_play(sync=True)
	bodynodes_panel["anim_status"] = "Animation started"

	bodynodes_takes[bodynodes_data["take"]] = {}
	bodynodes_takes[bodynodes_data["take"]]["start"] = bpy.context.scene.frame_start
	bodynodes_takes[bodynodes_data["take"]]["end"] = bpy.context.scene.frame_end
	bodynodes_data["recording"] = True


def apply_animation():
	global bodynodes_data
	global bodynodes_takes
	print(bodynodes_data["take"])
	if bodynodes_data["take"]==None:
		print("None Take is selected")
		return
	
	which = bodynodes_data["take"]
	which_str = str(which+1)
	if "start" not in bodynodes_takes[which]:
		print("Take "+which_str+" not done")
		return

	remove_animation(which)
	
	for bodypart in bodynodes_takes[which].keys():
		if bodypart == "start" or bodypart == "end":
			continue
		bodypart_keyframes = bodynodes_takes[which][bodypart]
		for keyframe_info in bodypart_keyframes:
			player_bodypart = get_bodypart_blobj(player_selected, bodypart)
			player_bodypart.rotation_quaternion = keyframe_info["orientation"]
			player_bodypart.keyframe_insert(data_path='rotation_quaternion', frame=(keyframe_info["frame_current"]))

def stop_animation():
	global bodynodes_data
	global bodynodes_takes
	bodynodes_data["recording"] = False
	bpy.ops.screen.animation_cancel(False)
	bodynodes_panel["anim_status"] = "Animation stopped"

def start_change_animation():
	global player_selected
	global bodynodes_puppet_saved_change_anim
	bodynodes_puppet_saved_rot = {}
	for bodypart in bodynodes_puppet_original_rot.keys():
		obj_quat = get_bodypart_blobj(player_selected, bodypart).rotation_quaternion
		bodynodes_puppet_saved_change_anim[bodypart] = Quaternion((obj_quat))

def end_change_animation():
	global player_selected
	global bodynodes_puppet_saved_change_anim
	puppet_diff_anim = {}
	for bodypart in bodynodes_puppet_saved_change_anim.keys():
		obj_quat = get_bodypart_blobj(player_selected, bodypart).rotation_quaternion
		if bodynodes_puppet_saved_change_anim[bodypart] != obj_quat:
			puppet_diff_anim[bodypart] = obj_quat @ bodynodes_puppet_saved_change_anim[bodypart].inverted()
		
	start = bpy.context.scene.frame_current
	end = bpy.context.scene.frame_end
	bpy.context.scene.frame_set(start-1)

	for frame in range(start, end+1):
		bpy.context.scene.frame_set(frame)
		for bodypart in puppet_diff_anim.keys():
			player_bodypart = get_bodypart_blobj(player_selected, bodypart)
			player_bodypart.rotation_quaternion = puppet_diff_anim[bodypart] @ player_bodypart.rotation_quaternion
			if player_bodypart.keyframe_delete(data_path='rotation_quaternion', frame=(frame)):
				player_bodypart.keyframe_insert(data_path='rotation_quaternion', frame=(frame))

	bpy.context.scene.frame_set(start)

def start_server():
	# print("start_server")
	if bodynodes_server["socket"]:
		print("Socket is already there...")
		return

	reinit_bn_data()

	print("Creating socket ...")
	bodynodes_server["socket"] = socket(AF_INET, SOCK_DGRAM)
	print("Binding socket ...")

	try:
		print("Now running ...")
		bodynodes_server["socket"].bind((bodynodes_server["host"], bodynodes_server["port"]))	
		# bodynodes_server["socket"].listen(1)
	except:
		bodynodes_panel["server_status"] = "Error starting server"
		bodynodes_server["socket"] = None
		print("Have you forgotten to create the hotspot?")
		raise

	print("Starting connection")
	bodynodes_server["connection"] = AcceptConnection("accepter", bodynodes_server["socket"])
	bodynodes_server["connection"].start()
	bodynodes_panel["server_status"] = "Server running"
	bodynodes_panel["anim_status"] = "Start animation and take position"

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
		
	bodynodes_panel["server_status"] = "Server not running"
	bodynodes_panel["anim_status"] = "Start Server"

def enable_tracking():
	bodynodes_data["track"] = True
	bodynodes_panel["track_status"] = "Tracking Enabled"

def take_animation_fun(self, context):
	bodynodes_data["take"] = int(self.take_animation_list)
	if bodynodes_data["take"] > 2:
		bodynodes_data["take"] = None

# Example to move the mover where the Hip of the player is
# bpy.data.objects["RedGuy_mover"].location = bpy.data.objects["RedGuy"].matrix_world @ bpy.data.objects["RedGuy"].pose.bones["Hip"].matrix @ bpy.data.objects["RedGuy"].pose.bones["Hip"].location

def get_global_location(player, bone_name):
	return bpy.data.objects[player].matrix_world @ bpy.data.objects[player].pose.bones[bone_name].matrix @ bpy.data.objects[player].pose.bones[bone_name].location

def apply_walk_ref():
	global player_selected
	print("player_selected = "+player_selected)
	start = bpy.context.scene.frame_start
	end = bpy.context.scene.frame_end
	player_bones = bpy.data.objects[player_selected].pose.bones
	player_mover = get_bodypart_blobj(player_selected, "mover")
	
	bpy.context.scene.frame_set(start-1)
	ref_foot = bpy.data.objects[player_selected].data.bones.active.name
	ref_foot_prev_glocation = get_global_location(player_selected, ref_foot)

	for frame in range(start, end+1):
		bpy.context.scene.frame_set(frame)

		diff_glocation = get_global_location(player_selected, ref_foot) - ref_foot_prev_glocation
		player_mover.location[0] -= diff_glocation[0]
		player_mover.location[1] -= diff_glocation[1]		
		player_mover.keyframe_insert(data_path='location', frame=(frame))

def apply_walk_auto():
	global player_selected
	print("player_selected = "+player_selected)
	start = bpy.context.scene.frame_start
	end = bpy.context.scene.frame_end
	player_bones = bpy.data.objects[player_selected].pose.bones
	player_mover = get_bodypart_blobj(player_selected, "mover")

	ref_foot = None
	other_foot = None
	ref_foot_prev_glocation = None
	walking_vector = None
	
	for frame in range(start, end+1):
		if ref_foot == None:
			# The first reference foot will be found by looking at which foot is moving faster
			# the other foot will be used as reference
			bpy.context.scene.frame_set(frame-1)
			lfoot_glocation_prev = get_global_location(player_selected, "Toe_L")
			rfoot_glocation_prev = get_global_location(player_selected, "Toe_R")
			bpy.context.scene.frame_set(frame)

			lfoot_diff_glocation = get_global_location(player_selected, "Toe_L") - lfoot_glocation_prev
			rfoot_diff_glocation = get_global_location(player_selected, "Toe_R") - rfoot_glocation_prev
			
			lfoot_movement_vec = Vector((lfoot_diff_glocation[0], lfoot_diff_glocation[1]))
			rfoot_movement_vec = Vector((rfoot_diff_glocation[0], rfoot_diff_glocation[1]))
			lfoot_mov = lfoot_movement_vec @ lfoot_movement_vec
			rfoot_mov = rfoot_movement_vec @ rfoot_movement_vec
			
			if lfoot_mov > 0.001 or rfoot_mov > 0.001:
				if lfoot_mov > rfoot_mov:
					ref_foot = "Toe_R"
					other_foot = "Toe_L"
					ref_foot_prev_glocation = rfoot_glocation_prev
					other_foot_prev_glocation = lfoot_glocation_prev
				else:
					ref_foot = "Toe_L"
					other_foot = "Toe_R"
					ref_foot_prev_glocation = lfoot_glocation_prev
					other_foot_prev_glocation = rfoot_glocation_prev

				other_diff_glocation = get_global_location(player_selected, other_foot) - other_foot_prev_glocation
				walking_vector = Vector((other_diff_glocation[0], other_diff_glocation[1], 0))
				#print("First ref_foot = "+ref_foot)
				
			else:
				continue
				
		bpy.context.scene.frame_set(frame-1)
		ref_foot_prev_glocation = get_global_location(player_selected, ref_foot)
		bpy.context.scene.frame_set(frame)
		diff_glocation = get_global_location(player_selected, ref_foot) - ref_foot_prev_glocation
		player_mover.location[0] -= diff_glocation[0]
		player_mover.location[1] -= diff_glocation[1]
		player_mover.keyframe_insert(data_path='location', frame=(frame))


		bpy.context.scene.frame_set(frame-1)
		other_foot_prev_glocation = get_global_location(player_selected, other_foot)
		bpy.context.scene.frame_set(frame)
		other_foot_now_glocation = get_global_location(player_selected, other_foot)
		bpy.context.scene.frame_set(frame+1)		
		other_diff_glocation_next = get_global_location(player_selected, other_foot) - other_foot_now_glocation
		other_walking_vector = Vector((other_diff_glocation_next[0], other_diff_glocation_next[1], 0))

		#print("frame = "+str(frame))
		if walking_vector @ other_walking_vector < 0:
			#print("We confirmed that the other foot is going backwards")
			ref_glocation_value = walking_vector @ ref_foot_prev_glocation 
			other_glocation_value = walking_vector @ other_foot_prev_glocation 
			if ref_glocation_value < other_glocation_value:
				#print("We confirmed that ref foot is behind the other foot")
				if ref_foot == "Toe_L":
					ref_foot = "Toe_R"
					other_foot = "Toe_L"
				else:
					ref_foot = "Toe_L"
					other_foot = "Toe_R"
				print("new ref_foot = "+ref_foot)
				

bpy.types.Scene.take_animation_list = bpy.props.EnumProperty(items = (
	('0','Take 1',''),
	('1','Take 2',''),
	('2','Take 3',''),
	('3','None',''),
	), default = '3', update=take_animation_fun)

bpy.context.scene.take_animation_list = '3'

class PANEL_PT_Bodynodes(bpy.types.Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'View'
	bl_label = "Bodynodes"

	def draw(self, context):
		layout = self.layout

		row = layout.row()
		row.operator("bodynodes.select_player", icon = "MESH_CUBE")		

		# Big render button
		layout.label(text="Server:   "  + bodynodes_panel["server_status"])
		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.operator("bodynodes.start_server", icon='MESH_CUBE', text="Start")
		col1.enabled = True
		col2 = row.column()
		col2.operator("bodynodes.stop_server", icon='MESH_CUBE', text="Stop")
		col2.enabled = True

		layout.label(text="Animation:   " + bodynodes_panel["anim_status"])
		row = layout.row()
		row.prop(context.scene, 'take_animation_list', expand=True)
		
		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.operator("bodynodes.take_animation", text="Take")
		col1.enabled = True
		col2 = row.column()
		col2.operator("bodynodes.apply_animation", text="Apply")
		col2.enabled = True

		row = layout.row()
		row.scale_y = 1.0
		row.operator("bodynodes.stop_animation", text="Stop")

		layout.label(text="Edit Animation")
		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.operator("bodynodes.start_change_animation", text="Start Change")
		col1.enabled = True
		col2 = row.column()
		col2.operator("bodynodes.end_change_animation", text="End Change")
		col2.enabled = True

		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.operator("bodynodes.apply_walk_auto", text="Auto Walk Auto")
		col1.enabled = True
		col2 = row.column()
		col2.operator("bodynodes.apply_walk_ref", text="Apply Walk Ref")
		col2.enabled = True

		layout.label(text="Tracking:   " + bodynodes_panel["track_status"])
		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.operator("bodynodes.enable_tracking", icon='MESH_CUBE', text="Enable")
		col1.enabled = True
		col2 = row.column()
		col2.operator("bodynodes.disable_tracking", icon='MESH_CUBE', text="Disable")
		col2.enabled = True

		layout.label(text="Puppet Orientation")
		row = layout.row()
		row.scale_y = 1.0
		row.operator("bodynodes.save_puppet_orientation", icon='MESH_CUBE', text="Save")
		row.operator("bodynodes.load_puppet_orientation", icon='MESH_CUBE', text="Load")

		row = layout.row()
		row.operator("bodynodes.reset_puppets", icon = "MESH_CUBE")

		layout.label(text="Axis settings")
		row = layout.row()
		row.operator("bodynodes.change_axis_menu", icon = "PLUGIN")

		row = layout.row()
		row.operator("bodynodes.close", text="Close")

class BodynodesTakeAnimationOperator(bpy.types.Operator):
	bl_idname = "bodynodes.take_animation"
	bl_label = "Take Animation Operator"

	def execute(self, context):
		take_animation()
		return {'FINISHED'}

class BodynodesApplyAnimationOperator(bpy.types.Operator):
	bl_idname = "bodynodes.apply_animation"
	bl_label = "Apply Animation Operator"

	def execute(self, context):
		apply_animation()
		return {'FINISHED'}

class BodynodesStopAnimationOperator(bpy.types.Operator):
	bl_idname = "bodynodes.stop_animation"
	bl_label = "Stop Animation Operator"

	def execute(self, context):
		stop_animation()
		return {'FINISHED'}

class BodynodesStartChangeAnimationOperator(bpy.types.Operator):
	bl_idname = "bodynodes.start_change_animation"
	bl_label = "Start Change Animation Operator"

	def execute(self, context):
		start_change_animation()
		return {'FINISHED'}

class BodynodesEndChangeAnimationOperator(bpy.types.Operator):
	bl_idname = "bodynodes.end_change_animation"
	bl_label = "End Change Animation Operator"

	def execute(self, context):
		end_change_animation()
		return {'FINISHED'}


class BodynodesApplyWalkAutoOperator(bpy.types.Operator):
	bl_idname = "bodynodes.apply_walk_auto"
	bl_label = "Apply Walk Operator"

	def execute(self, context):
		apply_walk_auto()
		return {'FINISHED'}

class BodynodesApplyWalkRefOperator(bpy.types.Operator):
	bl_idname = "bodynodes.apply_walk_ref"
	bl_label = "Apply Walk Operator"

	def execute(self, context):
		apply_walk_ref()
		return {'FINISHED'}

class BodynodesStartServerOperator(bpy.types.Operator):
	bl_idname = "bodynodes.start_server"
	bl_label = "Start Server Operator"

	def execute(self, context):
		bodynodes_panel["anim_status"] = "Take initial position"
		bpy.app.timers.register(start_server, first_interval=4.0)
		return {'FINISHED'}

class BodynodesStopServerOperator(bpy.types.Operator):
	bl_idname = "bodynodes.stop_server"
	bl_label = "Stop Server Operator"
	
	def execute(self, context):
		stop_animation()
		stop_server()
		return {'FINISHED'}

class BodynodesEnableTrackingOperator(bpy.types.Operator):
	bl_idname = "bodynodes.enable_tracking"
	bl_label = "Enable Tracking Operator"

	def execute(self, context):
		enable_tracking()
		return {'FINISHED'}

class BodynodesDisableTrackingOperator(bpy.types.Operator):
	bl_idname = "bodynodes.disable_tracking"
	bl_label = "Disable Tracking Operator"

	def execute(self, context):
		bodynodes_data["track"] = False
		bodynodes_panel["track_status"] = "Tracking Disabled"
		return {'FINISHED'}

class BodynodesSavePuppetOrientationOperator(bpy.types.Operator):
	bl_idname = "bodynodes.save_puppet_orientation"
	bl_label = "Save Puppet Orientation Operator"

	def execute(self, context):
		save_puppet_rotations()
		return {'FINISHED'}

class BodynodesLoadPuppetOrientationOperator(bpy.types.Operator):
	bl_idname = "bodynodes.load_puppet_orientation"
	bl_label = "Load Puppet Orientation Operator"

	def execute(self, context):
		load_puppet_rotations()
		return {'FINISHED'}


class BodynodesCloseOperator(bpy.types.Operator):
	bl_idname = "bodynodes.close"
	bl_label = "Close Panel Operator"
	
	def execute(self, context):
		stop_animation()
		stop_server()
		unregister()
		return {'FINISHED'}

class BodynodesAnimationStatusOperator(bpy.types.Operator):
	bl_idname = "bodynodes.animation_status"
	bl_label = "Animation Status Operator"
	
	def draw(self, context):
		print("Draw called")
		layout = self.layout

class BodynodesResetPuppetOperator(bpy.types.Operator):
	bl_idname = "bodynodes.reset_puppets"
	bl_label = "Reset puppets"
	
	def execute(self, context):
		reset_puppets_original_rotations()
		return {'FINISHED'}

class BodynodesSelectPlayerMenu(bpy.types.Operator) : 
	bl_idname = "bodynodes.select_player"
	bl_label = "Select player"  
	bl_options = {"REGISTER", "UNDO"} 

	global players_available
	player = bpy.props.EnumProperty(items= players_available, name = "Player")

	def execute(self, context):
		global player_selected
		player_selected = self.player
		return {"FINISHED"} 

class BodynodesChangeAxisMenu(bpy.types.Operator) : 
	bl_idname = "bodynodes.change_axis_menu"  
	bl_label = "Change sensor axis"  
	bl_options = {"REGISTER", "UNDO"} 
	
	bodypart_to_change = bpy.props.EnumProperty(items= (('head', 'head', ''),
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
		global bodynodes_sensor_axis
		global bodynodes_data
		new_w_axis = int(self.new_w_axis)
		new_x_axis = int(self.new_x_axis)
		new_y_axis = int(self.new_y_axis)
		new_z_axis = int(self.new_z_axis)
		
		bodypart_change_sensor = str(self.bodypart_to_change)
		print(bodypart_change_sensor)
		if new_w_axis > 3:
			bodynodes_sensor_axis[bodypart_change_sensor]["new_w_sign"] = -1
			new_w_axis -= 4
		else:
			bodynodes_sensor_axis[bodypart_change_sensor]["new_w_sign"] = 1
		
		if new_x_axis > 3:
			bodynodes_sensor_axis[bodypart_change_sensor]["new_x_sign"] = -1
			new_x_axis -= 4
		else:
			bodynodes_sensor_axis[bodypart_change_sensor]["new_x_sign"] = 1
		
		if new_y_axis > 3:
			bodynodes_sensor_axis[bodypart_change_sensor]["new_y_sign"] = -1
			new_y_axis -= 4
		else:
			bodynodes_sensor_axis[bodypart_change_sensor]["new_y_sign"] = 1

		if new_z_axis > 3:
			bodynodes_sensor_axis[bodypart_change_sensor]["new_z_sign"] = -1
			new_z_axis -= 4
		else:
			bodynodes_sensor_axis[bodypart_change_sensor]["new_z_sign"] = 1

		bodynodes_sensor_axis[bodypart_change_sensor]["new_w_val"] = new_w_axis
		bodynodes_sensor_axis[bodypart_change_sensor]["new_x_val"] = new_x_axis
		bodynodes_sensor_axis[bodypart_change_sensor]["new_y_val"] = new_y_axis
		bodynodes_sensor_axis[bodypart_change_sensor]["new_z_val"] = new_z_axis
		
		bodynodes_data["targetQuat"] = {}
		bodynodes_data["startQuat"] = {}
		bodynodes_data["offsetQuat"] = {}
		bodynodes_data["readQuat"] = {}
		bodynodes_data["reoriQuat"] = {}
		bodynodes_data["initOrieZ"] = {}

		reset_puppets_original_rotations()
	
		return {"FINISHED"} 

def register() :
	bpy.utils.register_class(BodynodesStartServerOperator)
	bpy.utils.register_class(BodynodesStopServerOperator)
	bpy.utils.register_class(BodynodesTakeAnimationOperator)
	bpy.utils.register_class(BodynodesApplyAnimationOperator)
	bpy.utils.register_class(BodynodesStopAnimationOperator)
	bpy.utils.register_class(BodynodesStartChangeAnimationOperator)
	bpy.utils.register_class(BodynodesEndChangeAnimationOperator)
	bpy.utils.register_class(BodynodesApplyWalkAutoOperator)
	bpy.utils.register_class(BodynodesApplyWalkRefOperator)
	bpy.utils.register_class(BodynodesEnableTrackingOperator)
	bpy.utils.register_class(BodynodesDisableTrackingOperator)
	bpy.utils.register_class(BodynodesSavePuppetOrientationOperator)
	bpy.utils.register_class(BodynodesLoadPuppetOrientationOperator)
	bpy.utils.register_class(BodynodesSelectPlayerMenu)
	bpy.utils.register_class(BodynodesCloseOperator)
	bpy.utils.register_class(BodynodesResetPuppetOperator)
	bpy.utils.register_class(BodynodesAnimationStatusOperator)
	bpy.utils.register_class(BodynodesChangeAxisMenu)
	
	bpy.utils.register_class(PANEL_PT_Bodynodes)
	bpy.app.timers.register(main_read_orientations)
	bpy.app.handlers.frame_change_pre.append(stop_at_last_frame)

def unregister() :
	bpy.utils.unregister_class(BodynodesStartServerOperator)
	bpy.utils.unregister_class(BodynodesStopServerOperator)
	bpy.utils.unregister_class(BodynodesTakeAnimationOperator)
	bpy.utils.unregister_class(BodynodesApplyAnimationOperator)
	bpy.utils.unregister_class(BodynodesStopAnimationOperator)
	bpy.utils.unregister_class(BodynodesStartChangeAnimationOperator)
	bpy.utils.unregister_class(BodynodesEndChangeAnimationOperator)
	bpy.utils.unregister_class(BodynodesApplyWalkAutoOperator)
	bpy.utils.unregister_class(BodynodesApplyWalkRefOperator)
	bpy.utils.unregister_class(BodynodesEnableTrackingOperator)
	bpy.utils.unregister_class(BodynodesDisableTrackingOperator)
	bpy.utils.unregister_class(BodynodesSavePuppetOrientationOperator)
	bpy.utils.unregister_class(BodynodesLoadPuppetOrientationOperator)
	bpy.utils.unregister_class(BodynodesSelectPlayerMenu)
	bpy.utils.unregister_class(BodynodesCloseOperator)
	bpy.utils.unregister_class(BodynodesResetPuppetOperator)
	bpy.utils.unregister_class(BodynodesAnimationStatusOperator)
	bpy.utils.unregister_class(BodynodesChangeAxisMenu)
	
	bpy.utils.unregister_class(PANEL_PT_Bodynodes)
	bpy.app.timers.unregister(main_read_orientations)
	bpy.app.handlers.frame_change_pre.clear()
	
def stop_at_last_frame(scene):
	if scene.frame_current == scene.frame_end-1:
		stop_animation()

if __name__ == "__main__" :
	save_puppet_rotations()
	register()




