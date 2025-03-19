#
# MIT License
# 
# Copyright (c) 2021-2024 Manuel Bottini
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
#

import glob
import os
import sys

import bpy
import mathutils

bodynodes_objs_init = {
    "forearm_left": mathutils.Quaternion((0.5000, 0.5000, 0.5000, 0.5000)),
    "forearm_right": mathutils.Quaternion((0.5000, 0.5000, -0.5000, -0.5000)),
    "head": mathutils.Quaternion((1.0000, 0.0000, 0.0000, 0.0000)),
    "Hip": mathutils.Quaternion((1.0000, 0.0000, 0.0000, 0.0000)),
    "lowerbody": mathutils.Quaternion((1.0000, 0.0000, 0.0000, 0.0000)),
    "lowerleg_left": mathutils.Quaternion((-0.0000, 1.0000, 0.0000, -0.0000)),
    "lowerleg_right": mathutils.Quaternion((-0.0000, 1.0000, 0.0000, -0.0000)),
    "upperarm_left": mathutils.Quaternion((0.5000, 0.5000, 0.5000, 0.5000)),
    "upperarm_right": mathutils.Quaternion((0.5000, 0.5000, -0.5000, -0.5000)),
    "upperbody": mathutils.Quaternion((1.0000, 0.0000, 0.0000, 0.0000)),
    "upperleg_left": mathutils.Quaternion((-0.0000, 1.0000, 0.0000, -0.0000)),
    "upperleg_right": mathutils.Quaternion((-0.0000, 1.0000, 0.0000, -0.0000))
}

GLOVE_ANGLE_MIGNOLO=0
GLOVE_ANGLE_ANULARE=1
GLOVE_ANGLE_MEDIO  =2
GLOVE_ANGLE_INDICE =3
GLOVE_ANGLE_POLLICE=4
GLOVE_TOUCH_MIGNOLO=5
GLOVE_TOUCH_ANULARE=6
GLOVE_TOUCH_MEDIO  =7
GLOVE_TOUCH_INDICE =8

bodynode_bones_init = [
    "lowerarm_left",
    "lowerarm_right",
    "head",
    "Hip",
    "lowerbody",
    "lowerleg_left",
    "lowerleg_right",
    "upperarm_left",
    "upperarm_right",
    "upperbody",
    "upperleg_left",
    "upperleg_right",
    "hand_left",
    "hand_right",
    "katana"
]

bodynode_fingers_init = [ "mignolo", "anulare", "medio", "indice", "pollice" ]


def get_bone_global_rotation_quaternion(player_selected, bone):
    if bone not in bpy.data.objects[player_selected].pose.bones:
        print(bone+" bone has not been found")
        return None
    return (bpy.data.objects[player_selected].matrix_world @ bpy.data.objects[player_selected].pose.bones[bone].matrix).to_quaternion()


def get_bone_local_rotation_quaternion(player_selected, bone):
    if bone not in bpy.data.objects[player_selected].pose.bones:
        print(bone+" bone has not been found")
        return None

    bone_obj = bpy.data.objects[player_selected].pose.bones[bone]
    if bone_obj.parent:
        return ( bone_obj.parent.matrix.inverted() @ bone_obj.matrix ).to_quaternion()
    else :
        return ( bone_obj.matrix).to_quaternion()

def get_bodynodeobj_ori(bodypart):
    if bodypart+"_ori" not in bpy.data.objects:
        print(bodypart+" bodynodeobj orientation has not been found")
        return None
    return bpy.data.objects[bodypart+"_ori"]

def remove_bodynodes_from_player(player_selected):
    if player_selected not in bpy.data.objects:
        return
    for bodypart in bodynode_bones_init:
        if bodypart not in bpy.data.objects[player_selected].pose.bones:
            print(bodypart + " bone is not in armature")
            continue

        if "Copy Rotation" in bpy.data.objects[player_selected].pose.bones[bodypart].constraints:
            bpy.data.objects[player_selected].pose.bones[bodypart].constraints.remove(
                bpy.data.objects[player_selected].pose.bones[bodypart].constraints["Copy Rotation"]
            )
        if "hand_" in bodypart:
            for finger in bodynode_fingers_init:
                for index in range(1, 4):
                    bone_finger = bodypart + "_" + finger + "_" + str(index)
                    if bone_finger in bpy.data.objects[player_selected].pose.bones:
                        if "Copy Rotation" in bpy.data.objects[player_selected].pose.bones[bone_finger].constraints:
                            bpy.data.objects[player_selected].pose.bones[bone_finger].constraints.remove(
                                bpy.data.objects[player_selected].pose.bones[bone_finger].constraints["Copy Rotation"]
                            )

def apply_bodynodes_to_player(player_selected, bodynodes_armature_config ):
    if player_selected not in bpy.data.objects:
        return
    for bodypart in bodynodes_armature_config.keys():
        if bodynodes_armature_config[bodypart]["bone_name"] == "":
            continue

        # We don't need to set the global rotation of the bodynodeobj_glove. Glove angle data is relative
        if "hand_" in bodypart:
            for finger in bodynode_fingers_init:
                bodynodeobj_glove_finger = get_bodynodeobj_glove(bodypart, finger)
                for index in range(1, 4):
                    bone_finger = bodypart + "_" + finger + "_" + str(index)
                    if bone_finger in bpy.data.objects[player_selected].pose.bones:
                        if "Copy Rotation" not in bpy.data.objects[player_selected].pose.bones[bone_finger].constraints:
                            bpy.data.objects[player_selected].pose.bones[bone_finger].constraints.new(type = 'COPY_ROTATION')
                            bpy.data.objects[player_selected].pose.bones[bone_finger].constraints["Copy Rotation"].target = bodynodeobj_glove_finger
                            bpy.data.objects[player_selected].pose.bones[bone_finger].constraints["Copy Rotation"].owner_space = 'LOCAL'
                            bpy.data.objects[player_selected].pose.bones[bone_finger].constraints["Copy Rotation"].use_y = True
                            bpy.data.objects[player_selected].pose.bones[bone_finger].constraints["Copy Rotation"].use_y = False
                            bpy.data.objects[player_selected].pose.bones[bone_finger].constraints["Copy Rotation"].use_z = False

        bodynodeobj_ori = get_bodynodeobj_ori(bodypart)
        if bodynodeobj_ori == None:
            print(bodypart + " bodynodeobj_ori does not exist")
            continue

        if bodypart not in bpy.data.objects[player_selected].pose.bones:
            print(bodypart + " bone is not in armature")
            continue

        bodynodeobj_ori.rotation_quaternion = get_bone_global_rotation_quaternion(player_selected, bodypart)
        if "Copy Rotation" not in bpy.data.objects[player_selected].pose.bones[bodypart].constraints:
            bpy.data.objects[player_selected].pose.bones[bodypart].constraints.new(type = 'COPY_ROTATION')
            bpy.data.objects[player_selected].pose.bones[bodypart].constraints["Copy Rotation"].target = bodynodeobj_ori
 
def create_quanternion(axis_config, values):
        
    quat = mathutils.Quaternion((
        axis_config["new_w_sign"] * float(values[axis_config["new_w_val"]]),
        axis_config["new_x_sign"] * float(values[axis_config["new_x_val"]]),
        axis_config["new_y_sign"] * float(values[axis_config["new_y_val"]]),
        axis_config["new_z_sign"] * float(values[axis_config["new_z_val"]])
    ))
    #print("bodypart = "+str(bodypart)+" - quat = "+str(quat))
    return quat

# This trasformation ignores what is the local axis of the object once rotated, we don't trust those axis system which might be compromised
# rawquat                   - is the raw quaternion (vector of 4 values) from the sensor
# first_quat                - is the first quaternion that has been registered from the sensor, this will create a 0 angle from where the sensor started sensing
# starting_quat             - is the starting quaternion of the object we want to rotated with the sensor
# env_quat                  - is the environment quaternion, basically indicates somehow where the x axis points 
# bodynodes_axis_config     - axis configuration that will transfor the sensor values into values for the virtual world
def transform_sensor_quat( rawquat, first_quat, starting_quat, env_quat, bodynodes_axis_config):

    sensor_quat = mathutils.Quaternion((rawquat))

    if first_quat == None:
        first_quat = sensor_quat.inverted()

    #bpy.data.objects["katana"].rotation_quaternion = sensor_quat @ first_quat @ starting_quat 
    #bpy.data.objects["katana"].rotation_quaternion = starting_quat @ sensor_quat
    
    #bpy.data.objects["katana"].rotation_quaternion = sensor_quat @ first_quat 
    # Definitely wrong, the object rotates differently depeding where the sensor starts
    
    #bpy.data.objects["katana"].rotation_quaternion = sensor_quat
    # It imposes the current rotation instead of considering the initial rotation of the sensor

    rotation_real_quat = first_quat @ sensor_quat
    rotation_realaxis_quat = create_quanternion(
            bodynodes_axis_config,
            rotation_real_quat)
    
    object_new_quat = env_quat @ rotation_realaxis_quat @ env_quat.inverted() @ starting_quat
    
    return [ object_new_quat , first_quat ]
