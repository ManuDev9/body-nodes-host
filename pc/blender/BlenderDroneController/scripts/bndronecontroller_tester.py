#
# MIT License
#
# Copyright (c) 2024 Manuel Bottini
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

# The point of this script is to find out the relationships between orientations of
# different connected parts that make the position of an end point. Two body parts
# will be considered and the equations to find out the final position will be
# found

import glob
import os
import json
import sys
import mathutils
import math

from bpy_extras.io_utils import ExportHelper, ImportHelper

dir_path = os.path.dirname(os.path.realpath(__file__))

bn_common_path = "C:/Users\Manu/VirtualBox VMs/BodynodesDev/CommonDir/workspace/body-nodes-common/python"
blender_common_path = "C:/Users/Manu/VirtualBox VMs/BodynodesDev/CommonDir/workspace/body-nodes-host/pc/blender/BlenderCommon"
pythonlib_wifi_path = "C:/Users/Manu/VirtualBox VMs/BodynodesDev/CommonDir/workspace/body-nodes-host/modules/pythonlib"

# Removing the scripts saved in cache so that Blender uses the last updated version of the scritps
[os.remove(file) for file in glob.glob(os.path.join(os.path.abspath(__file__ + "/../../scripts/__pycache__"), "bndronecontroller_tester++++.cpython*.pyc"))]
[os.remove(file) for file in glob.glob(os.path.join(os.path.abspath(bn_common_path + "/__pycache__"), "bncommon.cpython*.pyc"))]
[os.remove(file) for file in glob.glob(os.path.join(os.path.abspath(blender_common_path + "/__pycache__"), "bnblenderutils.cpython*.pyc"))]
[os.remove(file) for file in glob.glob(os.path.join(os.path.abspath(__file__ + "/../../../../modules/pythonlib/__pycache__"), "bnwifibodynodeshost.cpython*.pyc"))]
[os.remove(file) for file in glob.glob(os.path.join(os.path.abspath(__file__ + "/../../../../modules/pythonlib/__pycache__"), "bnblebodynodeshost.cpython*.pyc"))]

sys.path.append(os.path.abspath(__file__)+"/../../scripts")
sys.path.append(bn_common_path)
sys.path.append(blender_common_path)
sys.path.append(pythonlib_wifi_path)

if "bncommon" in sys.modules:
    del sys.modules["bncommon"]
if "bnblenderutils" in sys.modules:
    del sys.modules["bnblenderutils"]
if "bnblebodynodeshost" in sys.modules:
    del sys.modules["bnblebodynodeshost"]
if "bnwifibodynodeshost" in sys.modules:
    del sys.modules["bnwifibodynodeshost"]

import bncommon
import bnblenderutils
import bnblebodynodeshost
import bnwifibodynodeshost

bodynodes_panel_connect = {
    "server" : {
        "running": False,
        "status": "Start server"
    },
    "ble" : {
        "running": False,
        "status": "Start BLE"
    },
    "drone" : {
        "tracking": False,
        "status": "Disconnected"
    }
}

bodynodes_data = {
    "firstOrientationAbs": {},
    "readOrientationAbs": {},
    "startingBodypartQuat": {},
    "readOrientationAbs": {},
    "readGloveAngle":{},
    "readGloveTouch":{},
    "reset": 0
}

droneposition_obj = {
    "name" : "droneposition_obj",
    "location" : [0 ,0, 0],
    "prev_location" : [0 ,0, 0],
    "constrloc" : [ [10, 20], [-5, 5], [-5, 5] ],
    "initial_relpos" : [10 ,0, 0]
}

bodynodes_axis_config_drone = {}

vw1_obj = "virtual_world_env"

def load_axis_config_drone(filepath):
    global bodynodes_axis_config_drone
    with open(filepath) as file:
        bodynodes_axis_config_drone = json.load(file)

def save_axis_config_drone(filepath):
    global bodynodes_axis_config_drone
    with open(filepath, "w") as file:
        file.write(json.dumps(bodynodes_axis_config_drone, indent=4, sort_keys=True))

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

    if data_json["sensortype"] == "orientation_abs":
        read_orientations(data_json)
    elif data_json["sensortype"] == "glove":
        read_glove(data_json)
    elif data_json["sensortype"] == "acceleration_abs":
        print("Acceleration data is not yet used")

def read_orientations(data_json):

    bodypart_o = str(data_json["bodypart"]).replace("\x00","")
    # print("read_orientations")
    #print(data_json)

    if bodypart_o not in bodynodes_axis_config_drone.keys():
        print("Bodypart "+str(bodypart_o)+" not in bodynodes configuration")
        return

    bodynodes_data["readOrientationAbs"][bodypart_o] = [
        data_json["value"][0],
        data_json["value"][1],
        data_json["value"][2],
        data_json["value"][3]
    ]


class BlenderBodynodeListener(bnblebodynodeshost.BodynodeListener):
    def __init__(self):
        print("This is the Blender listener")

    def onMessageReceived(self, player, bodypart, sensortype, value):
        data_json = {
            "player": player,
            "bodypart": bodypart,
            "sensortype": sensortype,
            "value": value
        }
        read_sensordata(data_json)

    def isOfInterest(self, player, bodypart, sensortype):
        # Everything is of interest
        return True

class BLEBlenderBodynodeListener(bnblebodynodeshost.BodynodeListener):
    def __init__(self):
        print("This is the BLE Blender listener")

    def onMessageReceived(self, player, bodypart, sensortype, value):
        data_json = {
            "player": player,
            "bodypart": bodypart,
            "sensortype": sensortype,
            "value": value
        }
        read_sensordata(data_json)

    def isOfInterest(self, player, bodypart, sensortype):
        # Everything is of interest
        return True

class WifiBlenderBodynodeListener(bnwifibodynodeshost.BodynodeListener):
    def __init__(self):
        print("This is the Wifi Blender listener")

    def onMessageReceived(self, player, bodypart, sensortype, value):
        data_json = {
            "player": player,
            "bodypart": bodypart,
            "sensortype": sensortype,
            "value": value
        }
        read_sensordata(data_json)

    def isOfInterest(self, player, bodypart, sensortype):
        # Everything is of interest
        return True


bleblenderbnlistener = BLEBlenderBodynodeListener()
bnblehost = bnblebodynodeshost.BnBLEHostCommunicator()

wifiblenderbnlistener = WifiBlenderBodynodeListener()
bnwifihost = bnwifibodynodeshost.BnWifiHostCommunicator()

bnmotiontrack = bncommon.BnTwoNodesMotionTracking(
    initialPosition = [0,0,0], lengthArm1 = 10, lengthArm2 = 10,
    locationConstraints = droneposition_obj[ "constrloc"])

def main_read_orientations():
    # That's where we move the objects
    global bodynodes_data
    #print(bodynodes_data["readOrientationAbs"])
    for bodypart in bodynodes_data["readOrientationAbs"]:

        if bodypart not in bodynodes_axis_config_drone:
            print("Bodypart = "+bodypart+ " not in armature conf")
            continue

        if bodypart+"_obj" not in bpy.data.objects:
            print("Bodypart = "+bodypart+ " does not have an _obj object")
            continue

        if bodypart not in bpy.data.objects:
            print("Bodypart = "+bodypart+ " does not have an object")
            continue

        if bodynodes_data["readOrientationAbs"][bodypart] and bodypart != "katana":
            player_bodypart = bpy.data.objects[bodypart]
            
            if bodypart not in bodynodes_data["firstOrientationAbs"]:
                first_quat = None
                bodynodes_data["startingBodypartQuat"][bodypart] = mathutils.Quaternion((bpy.data.objects[bodypart].rotation_quaternion))
            else:
                first_quat = bodynodes_data["firstOrientationAbs"][bodypart]

            starting_quat = bodynodes_data["startingBodypartQuat"][bodypart]
            rawquat = bodynodes_data["readOrientationAbs"][bodypart]
            bodynodes_axis_config = bodynodes_axis_config_drone[bodypart]

            env_quat = bpy.data.objects[vw1_obj].rotation_quaternion
        
            [ object_new_quat , first_quat ] = bnblenderutils.transform_sensor_quat(rawquat, first_quat, starting_quat, env_quat, bodynodes_axis_config)
            bodynodes_data["firstOrientationAbs"][bodypart] = first_quat
                        
            player_bodypart.rotation_quaternion = object_new_quat

            bodynodes_data["readOrientationAbs"][bodypart] = None


    # Position Estimation via Sensor Orientation
    droneposition_obj["location"] = bnmotiontrack.compute(
        bpy.data.objects["lowerarm_right"].rotation_quaternion,
        bpy.data.objects["upperarm_right"].rotation_quaternion
    )

    bpy.data.objects[droneposition_obj["name"]].location.x = droneposition_obj["location"][0]
    bpy.data.objects[droneposition_obj["name"]].location.y = droneposition_obj["location"][1]
    bpy.data.objects[droneposition_obj["name"]].location.z = droneposition_obj["location"][2]

    return 0.02
    
def main_drone_function():
    # TODO
    # Ping the drone and set the Status
    
    # If status is connected, check location and prev_location to decide where we want to send the drone
    
    # Just process one displacement at a time and having the prev_location set correctly (you need to test timings and how far each single operation moves the drone)
    
    # Think about a rescaler slider to make operations bigger
    
    
    return 0.5

list_axis = [('0', 'W', ''),
             ('1', 'X', ''),
             ('2', 'Y', ''),
             ('3', 'Z', ''),
             ('4', '-W', ''),
             ('5', '-X', ''),
             ('6', '-Y', ''),
             ('7', '-Z', '')]

def reset_objects():    
    bpy.data.objects["upperarm_right"].rotation_quaternion = mathutils.Quaternion((0.707,0,0.707,0))
    bpy.data.objects["lowerarm_right"].rotation_quaternion = mathutils.Quaternion((1,0,0,0))
    bodynodes_data["firstOrientationAbs"] = {}
    bodynodes_data["startingBodypartQuat"] = {}
    bodynodes_data["readOrientationAbs"] = {}


def start_server():
    print("start_server")
    if bnwifihost.isRunning():
        print("Wifi BnHost is already there...")
        bodynodes_panel_connect["server"]["status"] = "Server running"
        bodynodes_panel_connect["server"]["running"] = True
        return

    reset_objects()

    bnblenderutils.reinit_bn_data()
    bnwifihost.start(["BN"])
    bnwifihost.addListener(wifiblenderbnlistener)

    bodynodes_panel_connect["server"]["status"] = "Server running"
    bodynodes_panel_connect["server"]["running"] = True


def stop_server():
    print("stop_server")
    global starting_quat
    if not bnwifihost.isRunning():
        print("Wifi BnHost was already stopped...")
        bodynodes_panel_connect["server"]["status"] = "Server not running"
        bodynodes_panel_connect["server"]["running"] = False
        return

    bnwifihost.removeListener(wifiblenderbnlistener)
    bnwifihost.stop();
    
    reset_objects()
    starting_quat = None
    bodynodes_panel_connect["server"]["status"] = "Server not running"
    bodynodes_panel_connect["server"]["running"] = False

def start_ble():
    print("start_ble")
    if bnblehost.isRunning():
        print("BLE BnHost is already there...")
        bodynodes_panel_connect["ble"]["status"] = "BLE running"
        bodynodes_panel_connect["ble"]["running"] = True
        return

    reset_objects()

    bnblehost.start(["Bodynode"])
    bnblehost.addListener(bleblenderbnlistener)

    bodynodes_panel_connect["ble"]["status"] = "BLE running"
    bodynodes_panel_connect["ble"]["running"] = True

def stop_ble():
    print("stop_ble")
    global starting_quat
    if not bnblehost.isRunning():
        print("BLE BnHost wass already stopped...")
        bodynodes_panel_connect["ble"]["status"] = "BLE not running"
        bodynodes_panel_connect["ble"]["running"] = False
        return

    bnblehost.removeListener(bleblenderbnlistener)
    bnblehost.stop();
    
    reset_objects()
    starting_quat = None
    bodynodes_panel_connect["ble"]["status"] = "BLE not running"
    bodynodes_panel_connect["ble"]["running"] = False


def drone_tracking_toggle():
    #TODO
    return


class PANEL_PT_BodynodesMain(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'View'
    bl_label = "Bodynodes Main"

    def draw(self, context):
        layout = self.layout    
    
        row = layout.row()
        row.operator("bodynodes.close_main", text="Close")

        layout.label(text="-----" )

        layout.label(text="Server:   "  + bodynodes_panel_connect["server"]["status"])
        
        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator("bodynodes.startstop_server",
            text="Stop" if bodynodes_panel_connect["server"]["running"] else "Start")
        col1.enabled = True

        layout.label(text="BLE:   "  + bodynodes_panel_connect["ble"]["status"])
        
        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator("bodynodes.startstop_ble",
            text="Stop" if bodynodes_panel_connect["ble"]["running"] else "Start")
        col1.enabled = True

        layout.label(text="-----" )
        
        row = layout.row()
        row.operator("bodynodes.load_axis_config_drone", text="Load Axis Config")
        row.enabled = True

        if not bodynodes_axis_config_drone:
            row = layout.row()
            row.scale_y = 1.0
            col1 = row.column()
            col1.label(text="Load a configuration file")
            return

        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.label(text="Axis Config:")
        col1.ui_units_x = 15
        col2 = row.column()
        col2.operator("bodynodes.axis_config", text="Change")
        col2.enabled = True
        col3 = row.column()
        col3.operator("bodynodes.save_axis_config_drone", text="Save")
        col3.enabled = True

        row = layout.row()
        row.operator("bodynodes.reset_objects", text="Reset")

        layout.label(text="-----" )
        
        row = layout.row()
        row.scale_y = 0.5
        row.label(text="Location X:   "  + "{:.5f}".format(droneposition_obj["location"][0]) )
        row = layout.row()
        row.scale_y = 0.5
        row.label(text="Location Y:   "  + "{:.5f}".format(droneposition_obj["location"][1]) )
        row = layout.row()
        row.scale_y = 0.5
        row.label(text="Location Z:   "  + "{:.5f}".format(droneposition_obj["location"][2]) )


class PANEL_PT_BodynodesDroneController(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'View'
    bl_label = "Bodynodes Drone Controller"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.scale_y = 1.0
        row.label(text="Connect to Drone Wifi" )
        
        row = layout.row()
        row.scale_y = 1.0
        row.label(text="Drone:   "  + bodynodes_panel_connect["drone"]["status"])
 
        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator("bodynodes.dronetrack_toggle",
            text="Stop" if bodynodes_panel_connect["drone"]["tracking"] else "Start")
        col1.enabled = True

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

class BodynodesStartStopBLEOperator(bpy.types.Operator):
    bl_idname = "bodynodes.startstop_ble"
    bl_label = "StartStop BLE Operator"
    bl_description = "Starts/Stop the local BLE central device. It resets position of the sensors at every start"

    def execute(self, context):
        if bodynodes_panel_connect["ble"]["running"]:
            stop_ble()
        else:
            bpy.app.timers.register(start_ble, first_interval=4.0)

        return {'FINISHED'}

class BodynodesLoadAxisConfigDroneOperator(bpy.types.Operator, ImportHelper):
    bl_idname = "bodynodes.load_axis_config_drone"
    bl_label = "Load Axis Configuration Operator"
    bl_description = "Load Axis configuration from a json file"

    filter_glob: bpy.props.StringProperty(
        default='*.json',
        options={'HIDDEN'}
    )

    def execute(self, context):
        load_axis_config_drone(self.filepath)
        return {'FINISHED'}

class BodynodesAxisConfigOperator(bpy.types.Operator):
    bl_idname = "bodynodes.axis_config"
    bl_label = "Bodynodes Axis Configuration"
    bl_description = "Helper to configure the Axis system"
    bl_options = {"REGISTER", "UNDO"}

    bodypart_to_change : bpy.props.EnumProperty(items= [
                                                 ('none', 'none', ''),
                                                 ('lowerarm_right', 'lowerarm_right', ''),
                                                 ('lowerarm_left', 'lowerarm_left', ''),
                                                 ('upperarm_right', 'upperarm_right', ''),
                                                 ('upperarm_left', 'upperarm_left', ''),
                                                 ('katana', 'katana', '')],
                                                 name = "Bodypart")

    bones_items = ( )

    bones_items = bones_items + (('none', 'none', ''),)
    for bone in bnblenderutils.bodynode_bones_init:
        bones_items = bones_items + ((bone, bone, ''),)
        
    new_bone_name : bpy.props.EnumProperty(items= bones_items,
                                        name = "Bone Name")

    new_w_axis: bpy.props.EnumProperty(items= list_axis,
                                        name = "Axis W")

    new_x_axis: bpy.props.EnumProperty(items= list_axis,
                                        name = "Axis X")

    new_y_axis: bpy.props.EnumProperty(items= list_axis,
                                        name = "Axis Y")

    new_z_axis: bpy.props.EnumProperty(items= list_axis,
                                        name = "Axis Z")

    def execute(self, context):
        #self.report({'INFO'}, f"Selected: {self.menu_items}")
        global bodynodes_axis_config_drone

        bodypart_to_change = str(self.bodypart_to_change)
        new_bone_name = str(self.new_bone_name)
        if bodypart_to_change == "none" or new_bone_name == "none":
            return {"FINISHED"}

        new_w_axis = int(self.new_w_axis)
        new_x_axis = int(self.new_x_axis)
        new_y_axis = int(self.new_y_axis)
        new_z_axis = int(self.new_z_axis)
        print(bodypart_to_change)

        if new_w_axis > 3:
            bodynodes_axis_config_drone[bodypart_to_change]["new_w_sign"] = -1
            new_w_axis -= 4
        else:
            bodynodes_axis_config_drone[bodypart_to_change]["new_w_sign"] = 1

        if new_x_axis > 3:
            bodynodes_axis_config_drone[bodypart_to_change]["new_x_sign"] = -1
            new_x_axis -= 4
        else:
            bodynodes_axis_config_drone[bodypart_to_change]["new_x_sign"] = 1

        if new_y_axis > 3:
            bodynodes_axis_config_drone[bodypart_to_change]["new_y_sign"] = -1
            new_y_axis -= 4
        else:
            bodynodes_axis_config_drone[bodypart_to_change]["new_y_sign"] = 1

        if new_z_axis > 3:
            bodynodes_axis_config_drone[bodypart_to_change]["new_z_sign"] = -1
            new_z_axis -= 4
        else:
            bodynodes_axis_config_drone[bodypart_to_change]["new_z_sign"] = 1

        bodynodes_axis_config_drone[bodypart_to_change]["new_w_val"] = new_w_axis
        bodynodes_axis_config_drone[bodypart_to_change]["new_x_val"] = new_x_axis
        bodynodes_axis_config_drone[bodypart_to_change]["new_y_val"] = new_y_axis
        bodynodes_axis_config_drone[bodypart_to_change]["new_z_val"] = new_z_axis
        bodynodes_axis_config_drone[bodypart_to_change]["bone_name"] = new_bone_name

        reset_objects()
        return {'FINISHED'}


class BodynodesSaveAxisConfigDroneOperator(bpy.types.Operator, ExportHelper):
    bl_idname = "bodynodes.save_axis_config_drone"
    bl_label = "Save Axis Config Operator"
    bl_description = "Save the axis configuration in a json file"

    # ExportHelper mixin class uses this
    filename_ext = ".json"

    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        save_axis_config_drone(self.filepath)
        return {'FINISHED'}

class BodynodesResetObjectsOperator(bpy.types.Operator):
    bl_idname = "bodynodes.reset_objects"
    bl_label = "Reset Objects Operator"
    bl_description = "It resets position of the objects"

    def execute(self, context):
        reset_objects()
        return {'FINISHED'}

class BodynodesDroneTrackingOperator(bpy.types.Operator):
    bl_idname = "bodynodes.dronetrack_toggle"
    bl_label = "Drone Tracking Toggle"
    bl_description = "Toggles the tracking of the drone"

    def execute(self, context):
        drone_tracking_toggle()
        return {'FINISHED'}

class BodynodesCloseMainOperator(bpy.types.Operator):
    bl_idname = "bodynodes.close_main"
    bl_label = "Close Main Panel Operator"
    bl_description = "Close all the Bodynodes panels"

    def execute(self, context):
        unregister_all()
        return {'FINISHED'}

def unregister_all():
    stop_server()
    bpy.utils.unregister_class(BodynodesStartStopServerOperator)
    bpy.utils.unregister_class(BodynodesStartStopBLEOperator)
    bpy.utils.unregister_class(BodynodesLoadAxisConfigDroneOperator)
    bpy.utils.unregister_class(BodynodesAxisConfigOperator)
    bpy.utils.unregister_class(BodynodesSaveAxisConfigDroneOperator)
    bpy.utils.unregister_class(BodynodesResetObjectsOperator)
    bpy.utils.unregister_class(BodynodesCloseMainOperator)
    bpy.utils.unregister_class(PANEL_PT_BodynodesMain)

    bpy.utils.unregister_class(BodynodesDroneTrackingOperator)
    bpy.utils.unregister_class(PANEL_PT_BodynodesDroneController)

    bpy.app.timers.unregister(main_read_orientations)
    bpy.app.timers.unregister(main_drone_function)

def register_all():
    bpy.utils.register_class(BodynodesStartStopServerOperator)
    bpy.utils.register_class(BodynodesStartStopBLEOperator)
    bpy.utils.register_class(BodynodesLoadAxisConfigDroneOperator)
    bpy.utils.register_class(BodynodesAxisConfigOperator)
    bpy.utils.register_class(BodynodesSaveAxisConfigDroneOperator)
    bpy.utils.register_class(BodynodesResetObjectsOperator)
    bpy.utils.register_class(BodynodesCloseMainOperator)
    bpy.utils.register_class(PANEL_PT_BodynodesMain)

    bpy.utils.register_class(BodynodesDroneTrackingOperator)
    bpy.utils.register_class(PANEL_PT_BodynodesDroneController)
    
    bpy.app.timers.register(main_read_orientations)
    bpy.app.timers.register(main_drone_function)

if __name__ == "__main__" :
    register_all()

