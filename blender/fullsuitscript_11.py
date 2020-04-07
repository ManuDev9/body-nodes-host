from socket import *
import threading
import json
import bpy
from mathutils import *
import time

# This script is made for the FullSuit-11
# bpy.ops.object.mode_set(mode='POSE')

# https://b3d.interplanety.org/en/creating-panels-for-placing-blender-add-ons-user-interface-ui/

# https://docs.blender.org/api/2.49/Mathutils.Quaternion-class.html

bodynodes_puppet_initial_rot = {
	"head" : Quaternion((-3.0908619663705394e-08, 0.7071067690849304, 0.7071068286895752, -3.0908619663705394e-08)),
	"forearm_right" : Quaternion((0.7071068286895752, 0.7071068286895752, 0.0, 0.0)),
	"forearm_left" : Quaternion((-3.0908619663705394e-08, 3.090862676913275e-08, 0.7071068286895752, 0.7071068286895752)),
	"upperleg_left" : Quaternion((0.0, 0.7071070075035095, 0.7071070075035095, 0.0)),
	"lowerleg_right" : Quaternion((0.0, 0.7071070075035095, 0.7071070075035095, 0.0)),
	"lowerleg_left" : Quaternion((0.0, 0.7071070075035095, 0.7071070075035095, 0.0)),
	"upperleg_right" : Quaternion((-3.0908619663705394e-08, 0.7071070075035095, 0.7071067690849304, 3.0908619663705394e-08)),
	"upperarm_right" : Quaternion((0.7071068286895752, 0.7071068286895752, 0.0, 0.0)),
	"upperarm_left" : Quaternion((-3.0908619663705394e-08, 3.090862676913275e-08, 0.7071068286895752, 0.7071068286895752)),
	"lowerbody" : Quaternion((0.0, 1.0, 0.0, 0.0)),
	"upperbody" : Quaternion((0.7071070075035095, 0.0, 0.0, 0.7071068286895752))
}

bodynodes_sensor_axis = {
	"head" : {
		"new_w_val" : 0,
		"new_x_val" : 1,
		"new_y_val" : 2,
		"new_z_val" : 3,
		
		"new_w_sign" : 1,
		"new_x_sign" : 1,
		"new_y_sign" : 1,
		"new_z_sign" : 1
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
	    # To reinstante once the original node is fixed
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
		"new_y_val" : 1,
		"new_z_val" : 3,
		
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
	"startQuat": {},
	"offsetQuat": {},
	"readQuat": {},
	"reoriQuat": {},
	"record": False
}

bodynodes_server = {
	"panel_status": "Stopped",
	"host": "192.168.137.1",
	"port": 12345,
	"buffer_size": 1024,
	"socket": None,
	"connection": None
}

def reset_puppet_init_rotations():
	for bodypart in bodynodes_puppet_initial_rot.keys():
		bpy.data.objects[bodypart].rotation_quaternion = bodynodes_puppet_initial_rot[bodypart]


def createQuanternion(bodypart, values):
	quat = Quaternion((
		bodynodes_sensor_axis[bodypart]["new_w_sign"] * float(values[bodynodes_sensor_axis[bodypart]["new_w_val"]]),
		bodynodes_sensor_axis[bodypart]["new_x_sign"] * float(values[bodynodes_sensor_axis[bodypart]["new_x_val"]]),
		bodynodes_sensor_axis[bodypart]["new_y_sign"] * float(values[bodynodes_sensor_axis[bodypart]["new_y_val"]]),
		bodynodes_sensor_axis[bodypart]["new_z_sign"] * float(values[bodynodes_sensor_axis[bodypart]["new_z_val"]])
	))
	#print("bodypart = "+str(bodypart)+" - quat = "+str(quat))
	return quat

def setOrientation(data_json):
	bodypart = data_json["bodypart"]
	values = data_json["value"].split("|")
	if bodypart not in bodynodes_sensor_axis:
		print("Bodypart "+str(bodypart)+" not in bodynodes configuration")
		return
	
	bodynodes_data["readQuat"][bodypart] = createQuanternion(bodypart, values)

	if bodypart not in bodynodes_data["offsetQuat"]:
		bodynodes_data["offsetQuat"][bodypart] =  bodynodes_data["readQuat"][bodypart].inverted()
		print(bodynodes_data["offsetQuat"][bodypart])
		print(bodynodes_data["readQuat"][bodypart])

	if bodypart not in bodynodes_data["startQuat"]:
		obj_quat = bpy.data.objects[bodypart].rotation_quaternion
		bodynodes_data["startQuat"][bodypart] = Quaternion((
			obj_quat.w,
			obj_quat.x,
			obj_quat.y,
			obj_quat.z
		))

	bodynodes_data["targetQuat"][bodypart] = bodynodes_data["startQuat"][bodypart] @ bodynodes_data["offsetQuat"][bodypart] @ bodynodes_data["readQuat"][bodypart] 
	bpy.data.objects[bodypart].rotation_mode = 'QUATERNION'
	bpy.data.objects[bodypart].rotation_quaternion = bodynodes_data["targetQuat"][bodypart]

def recordOrientation(bodypart):
	fc = bpy.context.scene.frame_current
	bpy.data.objects[bodypart].keyframe_insert(data_path='rotation_quaternion', frame=(fc))

def readOFromSingleJson(data_json):
	if "bodypart" not in data_json:
		print("bodypart key missing in json")
		return

	if "type" not in data_json:
		print("type key missing in json")
		return

	if "value" not in data_json:
		print("value key missing in json")
		return
	
	if data_json["bodypart"] not in bpy.data.objects:
		print(data_json["bodypart"]+" bodypart has not been found in Puppet Object")
		return

	#[w,x,y,z]
	setOrientation(data_json)
	if bodynodes_data["record"]:
		recordOrientation(data_json["bodypart"])

def readOFromConnection(data_str):
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
		print("AcceptConnection ready")
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
				

		print("AcceptConnection stopping")

	def stop(self):
		self.killed = True

def start_server():
	if bodynodes_server["socket"]:
		print("Socket is already there...")
		return

	print("Resetting Puppet positioning")
	reset_puppet_init_rotations()
	
	# Wait for 5 seconds
	time.sleep(5)
	global bodynodes_data
	bodynodes_data = {
		"targetQuat": {},
		"startQuat": {},
		"offsetQuat": {},
		"readQuat": {},
		"reoriQuat": {},
		"initOrieZ": {},
		"record": True
	}

	print("Creating socket ...")
	bodynodes_server["socket"] = socket(AF_INET, SOCK_DGRAM)
	print("Binding socket ...")

	try:
		print("Now running ...")
		bodynodes_server["socket"].bind((bodynodes_server["host"], bodynodes_server["port"]))	
		# bodynodes_server["socket"].listen(1)
		bodynodes_server["panel_status"] = "Running"
	except:
		print("Have you forgotten to create the hotspot?")
		raise

	print("Starting connection")
	bodynodes_server["connection"] = AcceptConnection("accepter", bodynodes_server["socket"])
	bodynodes_server["connection"].start()
	
def stop_server():
	print("stop_server")
	print(bodynodes_server["connection"])
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
		
	bodynodes_server["panel_status"] = "Stopped"


class PANEL_PT_Bodynodes(bpy.types.Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'View'
	bl_label = "Bodynodes"
	
	def draw(self, context):
		layout = self.layout
		# Big render button
		layout.label(text="Server:")
		row = layout.row()
		row.scale_y = 2.0
		row.operator("bodynodes.start_server", icon='MESH_CUBE', text="Start")
		row.operator("bodynodes.stop_server", icon='MESH_CUBE', text="Stop")
		
		box = layout.box()
		box.label(text="Server Status: " + bodynodes_server["panel_status"])
		
		row = layout.row()
		row.operator("bodynodes.values_dropdown_menu", icon = "PLUGIN")
		
		row = layout.row()
		row.operator("bodynodes.close", icon='MESH_CUBE', text="Close")

class BodynodesStartServerOperator(bpy.types.Operator):
	bl_idname = "bodynodes.start_server"
	bl_label = "Start Server Operator"

	def execute(self, context):
		start_server()
		return {'FINISHED'}

class BodynodesStopServerOperator(bpy.types.Operator):
	bl_idname = "bodynodes.stop_server"
	bl_label = "Stop Server Operator"
	
	def execute(self, context):
		stop_server()
		return {'FINISHED'}

class BodynodesCloseOperator(bpy.types.Operator):
	bl_idname = "bodynodes.close"
	bl_label = "Close Panel Operator"
	
	def execute(self, context):
		stop_server()
		unregister()
		return {'FINISHED'}

class BodynodesServerStatusOperator(bpy.types.Operator):
	bl_idname = "bodynodes.server_status"
	bl_label = "Server Status Operator"
	
	def draw(self, context):
		print("Draw called")
		layout = self.layout

class BodynodesValuesDropdownMenu(bpy.types.Operator) : 
	bl_idname = "bodynodes.values_dropdown_menu"  
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
		
		bodynodes_data = {
			"targetQuat": {},
			"startQuat": {},
			"offsetQuat": {},
			"readQuat": {},
			"reoriQuat": {},
			"initOrieZ": {},
			"record": True
		}
		reset_puppet_init_rotations()
	
		return {"FINISHED"} 



def register() :
	bpy.utils.register_class(BodynodesStartServerOperator)
	bpy.utils.register_class(BodynodesStopServerOperator)
	bpy.utils.register_class(BodynodesCloseOperator)
	bpy.utils.register_class(BodynodesServerStatusOperator)
	bpy.utils.register_class(BodynodesValuesDropdownMenu)
	
	bpy.utils.register_class(PANEL_PT_Bodynodes)

def unregister() :
	bpy.utils.unregister_class(BodynodesStartServerOperator)
	bpy.utils.unregister_class(BodynodesStopServerOperator)
	bpy.utils.unregister_class(BodynodesCloseOperator)
	bpy.utils.unregister_class(BodynodesServerStatusOperator)
	bpy.utils.unregister_class(BodynodesValuesDropdownMenu)
	
	bpy.utils.unregister_class(PANEL_PT_Bodynodes)

if __name__ == "__main__" :
	register()




