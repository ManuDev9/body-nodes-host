#
# MIT License
#
# Copyright (c) 2019-2024 Manuel Bottini
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
import time
import queue
import math
from mathutils import *
from bpy_extras.io_utils import ExportHelper, ImportHelper

from bnblenderaxis import BodynodesAxis

if "bnblenderutils" in sys.modules:
    del sys.modules["bnblenderutils"]

import bnblenderutils

# This script is required to record bodynodes animations
players_available = (('None', 'None', ''),)
player_selected_rec = "None"

bodynodes_saved_armature = {}

bodynodes_tpos = {}

bodynodes_data = {
    "firstOrientationAbs": {},
    "readOrientationAbs": {},
    "startingBodypartQuat": {},
    "readGloveAngle":{},
    "readGloveTouch":{},
    "recording": False,
    "take": None,
    "reset": 0,
    "track" : True
}

bodynodes_panel_rec = {
    "recording" : {
        "status": ""
    }
}

bodynodes_takes = [{}, {}, {}]

info_dialog_rec_obj = {
    "text" : "",
    "is_visible" : False
}

def main_read_orientations():
    global player_selected_rec
    if player_selected_rec == "None":
        return 0.02

    if bodynodes_data["reset"] == 1:
        print("Resetting phase 1")
        bodynodes_data["reset"] = 2
        reset_position_1()
        return 0.02
    if bodynodes_data["reset"] == 2:
        print("Resetting phase 2")
        bodynodes_data["reset"] = 0
        reset_position_2(window=False)
        return 0.02

    for bodypart in bodynodes_data["readOrientationAbs"]:

        if bodypart not in BodynodesAxis.Config:
            print("Bodypart = "+bodypart+ " not in armature conf")
            continue

        if get_bone_global_rotation_quaternion(player_selected_rec, bodypart) == None:
            print("Bodypart = "+bodypart+ " does not have a bone")
            continue

        if bodynodes_data["readOrientationAbs"][bodypart] and bodypart != "katana":
            player_bodypart = get_bodynodeobj_ori(bodypart)
            if bodypart not in bodynodes_data["firstOrientationAbs"]:
                first_quat = None
                bodynodes_data["startingBodypartQuat"][bodypart] = get_bone_global_rotation_quaternion(player_selected_rec, bodypart)
            else:
                first_quat = bodynodes_data["firstOrientationAbs"][bodypart]

            starting_quat = bodynodes_data["startingBodypartQuat"][bodypart]
            rawquat = bodynodes_data["readOrientationAbs"][bodypart]
            bodynodes_axis_config = BodynodesAxis.Config[bodypart]

            bpy.data.objects[player_selected_rec+"_env"].rotation_mode = 'QUATERNION'
            env_quat = bpy.data.objects[player_selected_rec+"_env"].rotation_quaternion
        
            [ object_new_quat , first_quat ] = bnblenderutils.transform_sensor_quat(rawquat, first_quat, starting_quat, env_quat, bodynodes_axis_config)
            bodynodes_data["firstOrientationAbs"][bodypart] = first_quat
                        
            player_bodypart.rotation_quaternion = object_new_quat
            if bodynodes_data["recording"]:
                recordOrientation(player_bodypart, bodypart)

            bodynodes_data["readOrientationAbs"][bodypart] = None

    for bodypart in bodynodes_data["readGloveAngle"]:
        if bodynodes_data["readGloveAngle"][bodypart]:
            for finger in bodynodes_data["readGloveAngle"][bodypart]:
                #print("This bodypart glove angle changed = " + bodypart + " " + finger)
                #player_bodypart = get_bodynodeobj_glove(bodypart, finger)
                #print("player_bodypart = "+player_bodypart)
                player_bodynodeobj = get_bodynodeobj_glove(bodypart, finger)
                #print(bodynodes_data["readGloveAngle"][bodypart][finger])
                player_bodynodeobj.rotation_euler[0] = float(bodynodes_data["readGloveAngle"][bodypart][finger]) * math.pi / 180
        bodynodes_data["readGloveAngle"][bodypart] = None

    for bodypart in bodynodes_data["readGloveTouch"]:
        if bodynodes_data["readGloveTouch"][bodypart]:
            # print("This bodypart glove touch changed = " + bodypart)
            # Depending on the touch and bodypart, you can do different things
            bodynodes_data["readGloveTouch"][bodypart] = None

    return 0.02

def reinit_bn_data():
    global bodynodes_data
    bodynodes_data["firstOrientationAbs"] = {}
    bodynodes_data["readOrientationAbs"] = {}
    bodynodes_data["startingBodypartQuat"] = {}

    bodynodes_data["readGloveAngle"] = {}
    bodynodes_data["readGloveTouch"] = {}



def load_armature():
    # print("load armature")
    global bodynodes_saved_armature
    for bodypart in BodynodesAxis.Config.keys():
        if BodynodesAxis.Config[bodypart]["bone_name"] == "":
            continue
        player_bodypart = get_bodynodeobj_ori(bodypart)
        player_bodypart.rotation_quaternion = bodynodes_saved_armature[bodypart]

def save_armature():
    # print("save armature")
    global bodynodes_saved_armature
    bodynodes_saved_armature = {}
    for bodypart in BodynodesAxis.Config.keys():
        if BodynodesAxis.Config[bodypart]["bone_name"] == "":
            continue
        player_bodypart = get_bodynodeobj_ori(bodypart)
        bodynodes_saved_armature[bodypart] = Quaternion((player_bodypart.rotation_quaternion))

def reset_armature():
    global player_selected_rec
    remove_bodynodes_from_player(player_selected_rec)

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects[player_selected_rec]
    bpy.data.objects[player_selected_rec].select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.rot_clear()
    bpy.ops.pose.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    apply_bodynodes_to_player(player_selected_rec)


def reset_position_1():
    global player_selected_rec
    remove_bodynodes_from_player(player_selected_rec)
    reinit_bn_data()

def reset_position_2(window=True):
    if window:
        time.sleep(5)
    global player_selected_rec
    apply_bodynodes_to_player(player_selected_rec)
    if window:
        info_dialog_rec("Position has been reset")

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
    if not bodynodes_data["track"]:
        return

    if bodypart_o not in BodynodesAxis.Config.keys():
        print("Bodypart "+str(bodypart_o)+" not in bodynodes configuration")
        return

    bodypart = redirect_bodypart(bodypart_o) # bodypart redirection
    if player_selected_rec not in bpy.data.objects:
        print(player_selected_rec + " not found, Select a player")
        return

    if not get_bodynodeobj_ori(bodypart):
        return

    bodynodes_data["readOrientationAbs"][bodypart] = [
        data_json["value"][0],
        data_json["value"][1],
        data_json["value"][2],
        data_json["value"][3]
    ]

def read_glove(data_json):
    bodypart_o = data_json["bodypart"]
    bodypart = redirect_bodypart(bodypart_o) # bodypart redirection

    # Digital events will always be collected
    bodynodes_data["readGloveTouch"][bodypart] = {}
    bodynodes_data["readGloveTouch"][bodypart][bnblenderutils.bodynode_fingers_init[0]] = data_json["value"][bnblenderutils.GLOVE_TOUCH_MIGNOLO]
    bodynodes_data["readGloveTouch"][bodypart][bnblenderutils.bodynode_fingers_init[1]] = data_json["value"][bnblenderutils.GLOVE_TOUCH_ANULARE]
    bodynodes_data["readGloveTouch"][bodypart][bnblenderutils.bodynode_fingers_init[2]] = data_json["value"][bnblenderutils.GLOVE_TOUCH_MEDIO]
    bodynodes_data["readGloveTouch"][bodypart][bnblenderutils.bodynode_fingers_init[3]] = data_json["value"][bnblenderutils.GLOVE_TOUCH_INDICE]

    # print("read_orientations")
    # print(bodynodes_data)
    if not bodynodes_data["track"]:
        return

    if bodypart_o not in BodynodesAxis.Config.keys():
        print("Bodypart "+str(bodypart_o)+" not in bodynodes configuration")
        return

    if player_selected_rec not in bpy.data.objects:
        print(player_selected_rec + " not found, Select a player")
        return

    if not get_bodynodeobj_glove(bodypart, bnblenderutils.bodynode_fingers_init[0]):
        return

    bodynodes_data["readGloveAngle"][bodypart] = {}
    bodynodes_data["readGloveAngle"][bodypart][bnblenderutils.bodynode_fingers_init[0]] = data_json["value"][bnblenderutils.GLOVE_ANGLE_MIGNOLO]
    bodynodes_data["readGloveAngle"][bodypart][bnblenderutils.bodynode_fingers_init[1]] = data_json["value"][bnblenderutils.GLOVE_ANGLE_ANULARE]
    bodynodes_data["readGloveAngle"][bodypart][bnblenderutils.bodynode_fingers_init[2]] = data_json["value"][bnblenderutils.GLOVE_ANGLE_MEDIO]
    bodynodes_data["readGloveAngle"][bodypart][bnblenderutils.bodynode_fingers_init[3]] = data_json["value"][bnblenderutils.GLOVE_ANGLE_INDICE]
    bodynodes_data["readGloveAngle"][bodypart][bnblenderutils.bodynode_fingers_init[4]] = data_json["value"][bnblenderutils.GLOVE_ANGLE_POLLICE]
    #print("data = "+str(data_json["value"]))

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

def clear_any_recording():
    global bodynodes_data
    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    for fc in range(start, end+1):
        for bodypart in bodynodes_data["readOrientationAbs"].keys():
            player_bodypart = get_bodynodeobj_ori(bodypart)
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

    bpy.app.handlers.frame_change_pre.append(stop_at_last_frame)
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
            player_bodypart = get_bodynodeobj_ori(bodypart)
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

def find_players():
    global players_available
    for bpy_object in bpy.data.objects:
        if "BNP" in bpy_object.name_full:
            if "_pos" not in bpy_object.name_full and "_ori" not in bpy_object.name_full and "_env" not in bpy_object.name_full:
                players_available = players_available + ((bpy_object.name_full+'', bpy_object.name_full+'', ''),)

    bpy.types.Scene.players_list_recording = bpy.props.EnumProperty(items= players_available,
        name = "Player",
        description = "Player to consider for recording",
        update = change_recording_player_fun)
    if len(players_available) == 2:
        bpy.context.scene.players_list_recording = players_available[1][0]
    else:
        bpy.context.scene.players_list_recording = "None"

def who_got_bodynodes():
    global players_available
    for player in players_available:
        player_name = player[0]
        if player_name in bpy.data.objects:
            print(player_name)
            if "Copy Rotation" in bpy.data.objects[player_name].pose.bones["lowerleg_left"].constraints:
                return player_name
    return "None"

def remove_bodynodes_from_player(player_selected_rec):
    if player_selected_rec not in bpy.data.objects:
        return
    for bodypart in bnblenderutils.bodynode_bones_init:
        if bodypart not in bpy.data.objects[player_selected_rec].pose.bones:
            print(bodypart + " bone is not in armature")
            continue
        if "Copy Rotation" in bpy.data.objects[player_selected_rec].pose.bones[bodypart].constraints:
            bpy.data.objects[player_selected_rec].pose.bones[bodypart].constraints.remove(
                bpy.data.objects[player_selected_rec].pose.bones[bodypart].constraints["Copy Rotation"]
            )
        if "hand_" in bodypart:
            for finger in bnblenderutils.bodynode_fingers_init:
                for index in range(1, 4):
                    bone_finger = bodypart + "_" + finger + "_" + str(index)
                    if bone_finger in bpy.data.objects[player_selected_rec].pose.bones:
                        if "Copy Rotation" in bpy.data.objects[player_selected_rec].pose.bones[bone_finger].constraints:
                            bpy.data.objects[player_selected_rec].pose.bones[bone_finger].constraints.remove(
                                bpy.data.objects[player_selected_rec].pose.bones[bone_finger].constraints["Copy Rotation"]
                            )

def apply_bodynodes_to_player(player_selected_rec):
    if player_selected_rec not in bpy.data.objects:
        return

    bodynodes_data["track"] = False
    for bodypart in BodynodesAxis.Config.keys():
        if BodynodesAxis.Config[bodypart]["bone_name"] == "":
            continue

        # We don't need to set the global rotation of the bodynodeobj_glove. Glove angle data is relative
        if "hand_" in bodypart:
            for finger in bnblenderutils.bodynode_fingers_init:
                bodynodeobj_glove_finger = get_bodynodeobj_glove(bodypart, finger)
                for index in range(1, 4):
                    bone_finger = bodypart + "_" + finger + "_" + str(index)
                    if bone_finger in bpy.data.objects[player_selected_rec].pose.bones:
                        if "Copy Rotation" not in bpy.data.objects[player_selected_rec].pose.bones[bone_finger].constraints:
                            bpy.data.objects[player_selected_rec].pose.bones[bone_finger].constraints.new(type = 'COPY_ROTATION')
                            bpy.data.objects[player_selected_rec].pose.bones[bone_finger].constraints["Copy Rotation"].target = bodynodeobj_glove_finger
                            bpy.data.objects[player_selected_rec].pose.bones[bone_finger].constraints["Copy Rotation"].owner_space = 'LOCAL'
                            bpy.data.objects[player_selected_rec].pose.bones[bone_finger].constraints["Copy Rotation"].use_y = True
                            bpy.data.objects[player_selected_rec].pose.bones[bone_finger].constraints["Copy Rotation"].use_y = False
                            bpy.data.objects[player_selected_rec].pose.bones[bone_finger].constraints["Copy Rotation"].use_z = False

        bodynodeobj_ori = get_bodynodeobj_ori(bodypart)
        if bodynodeobj_ori == None:
            print(bodypart + " bodynodeobj_ori does not exist")
            continue

        if bodypart not in bpy.data.objects[player_selected_rec].pose.bones:
            print(bodypart + " bone is not in armature")
            continue

        bodynodeobj_ori.rotation_quaternion = get_bone_global_rotation_quaternion(player_selected_rec, bodypart)
        if "Copy Rotation" not in bpy.data.objects[player_selected_rec].pose.bones[bodypart].constraints:
            bpy.data.objects[player_selected_rec].pose.bones[bodypart].constraints.new(type = 'COPY_ROTATION')
            bpy.data.objects[player_selected_rec].pose.bones[bodypart].constraints["Copy Rotation"].target = bodynodeobj_ori

    bodynodes_data["track"] = True

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

    print(player_selected_rec)
    if player_selected_rec == "None":
        return
    if player_selected_rec+"_pos" not in bpy.data.objects:
        bpy.ops.object.add()
        bpy.context.active_object.name = player_selected_rec+"_pos"
        bpy.context.active_object.location = Vector((0,0,0))
    if "Copy Location" not in bpy.data.objects[player_selected_rec].pose.bones["Hip"].constraints:
        bpy.data.objects[player_selected_rec].pose.bones["Hip"].constraints.new(type = 'COPY_LOCATION')
        bpy.data.objects[player_selected_rec].pose.bones["Hip"].constraints["Copy Location"].target = bpy.data.objects[player_selected_rec+"_pos"]
    if "Copy Rotation" not in bpy.data.objects[player_selected_rec].pose.bones["Hip"].constraints:
        bpy.data.objects[player_selected_rec].pose.bones["Hip"].constraints.new(type = 'COPY_ROTATION')
        bpy.data.objects[player_selected_rec].pose.bones["Hip"].constraints["Copy Rotation"].target = bpy.data.objects[player_selected_rec]
        bpy.data.objects[player_selected_rec].pose.bones["Hip"].constraints["Copy Rotation"].use_x = False
        bpy.data.objects[player_selected_rec].pose.bones["Hip"].constraints["Copy Rotation"].use_y = False
        bpy.data.objects[player_selected_rec].pose.bones["Hip"].constraints["Copy Rotation"].use_z = True
        bpy.data.objects[player_selected_rec].pose.bones["Hip"].constraints["Copy Rotation"].subtarget = "lowerbody"

    apply_bodynodes_to_player(player_selected_rec)


def save_animation_rec(filepath):
    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    animation_json = {}
    for bodypart in BodynodesAxis.Config.keys():
        if BodynodesAxis.Config[bodypart]["bone_name"] == "":
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

    # Example of redirection
    # elif bodypart == "upperleg_left":
        # return "upperarm_left"
    # elif bodypart == "upperleg_right":
        # return "upperarm_right"

    if bodypart in BodynodesAxis.Config.keys() and BodynodesAxis.Config[bodypart]["bone_name"] != "":
        return BodynodesAxis.Config[bodypart]["bone_name"]
    return "none"

def get_bodynodeobj_ori(bodypart):
    if bodypart+"_ori" not in bpy.data.objects:
        print(bodypart+" bodynodeobj orientation has not been found")
        return None
    return bpy.data.objects[bodypart+"_ori"]

def get_bodynodeobj_glove(bodypart, finger):
    if bodypart+"_"+finger not in bpy.data.objects:
        print(bodypart+" bodynodeobj glove has not been found")
        return None
    return bpy.data.objects[bodypart+"_"+finger]

def get_bone_global_rotation_quaternion(player_selected, bone):
    if bone not in bpy.data.objects[player_selected].pose.bones:
        print(bone+" bone has not been found")
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

bpy.context.scene.take_recording_list = '3'

class PANEL_PT_BodynodesRecording(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'View'
    bl_label = "Bodynodes Recording"

    def draw(self, context):
        layout = self.layout

        if not BodynodesAxis.Config:
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
        col1.enabled = True
        col2 = row.column()
        col2.operator("bodynodes.clear_recordings", text="Clear")
        col2.enabled = True

        row = layout.row()
        col1 = row.column()
        col1.operator("bodynodes.save_animation_rec", text="Save Anim")
        col1.enabled = True

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

def register_recording() :
    find_players()
    player_selected_rec = who_got_bodynodes()
    remove_bodynodes_from_player(player_selected_rec)
    bpy.context.scene.players_list_recording = player_selected_rec
    save_armature()

    bpy.utils.register_class(BodynodesTakeRecordingOperator)
    bpy.utils.register_class(BodynodesClearRecordingsOperator)
    bpy.utils.register_class(BodynodesEnableDisableTrackingOperator)
    bpy.utils.register_class(BodynodesResetPosition1Operator)
    bpy.utils.register_class(BodynodesResetPosition2Operator)
    bpy.utils.register_class(BodynodesSaveArmatureOperator)
    bpy.utils.register_class(BodynodesLoadArmatureOperator)
    bpy.utils.register_class(BodynodesResetArmatureOperator)
    bpy.utils.register_class(BodynodesSaveAnimationRecOperator)

    bpy.utils.register_class(PANEL_PT_BodynodesRecording)
    bpy.utils.register_class(InfoDialogRecOperator)

    bpy.app.timers.register(main_read_orientations)

def unregister_recording() :
    stop_animation()

    bpy.utils.unregister_class(BodynodesTakeRecordingOperator)
    bpy.utils.unregister_class(BodynodesClearRecordingsOperator)
    bpy.utils.unregister_class(BodynodesEnableDisableTrackingOperator)
    bpy.utils.unregister_class(BodynodesResetPosition1Operator)
    bpy.utils.unregister_class(BodynodesResetPosition2Operator)
    bpy.utils.unregister_class(BodynodesSaveArmatureOperator)
    bpy.utils.unregister_class(BodynodesLoadArmatureOperator)
    bpy.utils.unregister_class(BodynodesResetArmatureOperator)
    bpy.utils.unregister_class(BodynodesSaveAnimationRecOperator)

    bpy.utils.unregister_class(PANEL_PT_BodynodesRecording)
    bpy.utils.unregister_class(InfoDialogRecOperator)

    bpy.app.timers.unregister(main_read_orientations)

def stop_at_last_frame(scene):
    if scene.frame_current == scene.frame_end-1:
        stop_animation()
        bpy.app.handlers.frame_change_pre.clear()

if __name__ == "__main__" :
    register_recording()
