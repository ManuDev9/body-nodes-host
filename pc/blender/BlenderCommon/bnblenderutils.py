#
# MIT License
#
# Copyright (c) 2021-2025 Manuel Bottini
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

"""Blender Utilities for Bodynodes Panels"""

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
    "upperleg_right": mathutils.Quaternion((-0.0000, 1.0000, 0.0000, -0.0000)),
}

GLOVE_ANGLE_MIGNOLO = 0
GLOVE_ANGLE_ANULARE = 1
GLOVE_ANGLE_MEDIO = 2
GLOVE_ANGLE_INDICE = 3
GLOVE_ANGLE_POLLICE = 4
GLOVE_TOUCH_MIGNOLO = 5
GLOVE_TOUCH_ANULARE = 6
GLOVE_TOUCH_MEDIO = 7
GLOVE_TOUCH_INDICE = 8

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
    "katana",
]

bodynode_fingers_init = ["mignolo", "anulare", "medio", "indice", "pollice"]


def get_bone_global_rotation_quaternion(player_selected, bone):
    """Get bone global rotation as quaternion"""

    if bone not in bpy.data.objects[player_selected].pose.bones:
        print(bone + " bone has not been found")
        return None
    return (
        bpy.data.objects[player_selected].matrix_world
        @ bpy.data.objects[player_selected].pose.bones[bone].matrix
    ).to_quaternion()


def get_bone_local_rotation_quaternion(player_selected, bone):
    """Get bone local rotation as quaternion"""

    if bone not in bpy.data.objects[player_selected].pose.bones:
        print(bone + " bone has not been found")
        return None

    bone_obj = bpy.data.objects[player_selected].pose.bones[bone]
    if bone_obj.parent:
        return (bone_obj.parent.matrix.inverted() @ bone_obj.matrix).to_quaternion()
    return (bone_obj.matrix).to_quaternion()


def get_bodynodeobj_ori(bodypart):
    """Get bodynode orientation object"""

    if bodypart + "_ori" not in bpy.data.objects:
        print(bodypart + " bodynodeobj orientation has not been found")
        return None
    return bpy.data.objects[bodypart + "_ori"]


def remove_bodynodes_from_player(player_selected):
    """Remove bodynodes objects from player"""

    if player_selected not in bpy.data.objects:
        return

    for bodypart in bodynode_bones_init:
        if bodypart not in bpy.data.objects[player_selected].pose.bones:
            print(bodypart + " bone is not in armature")
            continue

        if (
            "Copy Rotation"
            in bpy.data.objects[player_selected].pose.bones[bodypart].constraints
        ):
            bpy.data.objects[player_selected].pose.bones[bodypart].constraints.remove(
                bpy.data.objects[player_selected]
                .pose.bones[bodypart]
                .constraints["Copy Rotation"]
            )

        if "hand_" not in bodypart:
            continue

        for finger in bodynode_fingers_init:
            for index in range(1, 4):
                bone_finger = bodypart + "_" + finger + "_" + str(index)

                if bone_finger not in bpy.data.objects[player_selected].pose.bones:
                    continue

                if (
                    "Copy Rotation"
                    not in bpy.data.objects[player_selected]
                    .pose.bones[bone_finger]
                    .constraints
                ):
                    continue

                bpy.data.objects[player_selected].pose.bones[
                    bone_finger
                ].constraints.remove(
                    bpy.data.objects[player_selected]
                    .pose.bones[bone_finger]
                    .constraints["Copy Rotation"]
                )


def find_players():
    """Find all bodynodes-compatible players"""

    players_available = (("None", "None", ""),)
    for bpy_object in bpy.data.objects:
        if "BNP" in bpy_object.name_full:
            if (
                "_pos" not in bpy_object.name_full
                and "_ori" not in bpy_object.name_full
                and "_env" not in bpy_object.name_full
            ):
                players_available = players_available + (
                    (bpy_object.name_full + "", bpy_object.name_full + "", ""),
                )

    return players_available


def who_got_bodynodes(players_available):
    """Find player with bodynodes applied"""

    for player in players_available:
        player_name = player[0]
        if player_name in bpy.data.objects:
            print(player_name)
            if (
                "Copy Rotation"
                in bpy.data.objects[player_name].pose.bones["lowerleg_left"].constraints
            ):
                return player_name
    return "None"


def apply_bodynodes_to_player(player_selected, bodynodes_armature_config):
    """Apply bodynodes objects to a player"""

    if player_selected not in bpy.data.objects:
        return

    for bodypart in bodynodes_armature_config.keys():
        if "__" in bodypart or bodynodes_armature_config[bodypart]["bone_name"] == "":
            continue

        # We don't need to set the global rotation of the bodynodeobj_glove. Glove angle data is relative
        if "hand_" not in bodypart:
            continue

        for finger in bodynode_fingers_init:
            bodynodeobj_glove_finger = get_bodynodeobj_glove(bodypart, finger)
            for index in range(1, 4):
                bone_finger = bodypart + "_" + finger + "_" + str(index)

                if bone_finger not in bpy.data.objects[player_selected].pose.bones:
                    continue

                if (
                    "Copy Rotation"
                    in bpy.data.objects[player_selected]
                    .pose.bones[bone_finger]
                    .constraints
                ):
                    continue

                bpy.data.objects[player_selected].pose.bones[
                    bone_finger
                ].constraints.new(type="COPY_ROTATION")
                bpy.data.objects[player_selected].pose.bones[bone_finger].constraints[
                    "Copy Rotation"
                ].target = bodynodeobj_glove_finger
                bpy.data.objects[player_selected].pose.bones[bone_finger].constraints[
                    "Copy Rotation"
                ].owner_space = "LOCAL"
                bpy.data.objects[player_selected].pose.bones[bone_finger].constraints[
                    "Copy Rotation"
                ].use_y = True
                bpy.data.objects[player_selected].pose.bones[bone_finger].constraints[
                    "Copy Rotation"
                ].use_y = False
                bpy.data.objects[player_selected].pose.bones[bone_finger].constraints[
                    "Copy Rotation"
                ].use_z = False

        bodynodeobj_ori = get_bodynodeobj_ori(bodypart)
        if bodynodeobj_ori is None:
            print(bodypart + " bodynodeobj_ori does not exist")
            continue

        if bodypart not in bpy.data.objects[player_selected].pose.bones:
            print(bodypart + " bone is not in armature")
            continue

        bodynodeobj_ori.rotation_quaternion = get_bone_global_rotation_quaternion(
            player_selected, bodypart
        )
        if (
            "Copy Rotation"
            not in bpy.data.objects[player_selected].pose.bones[bodypart].constraints
        ):
            bpy.data.objects[player_selected].pose.bones[bodypart].constraints.new(
                type="COPY_ROTATION"
            )
            bpy.data.objects[player_selected].pose.bones[bodypart].constraints[
                "Copy Rotation"
            ].target = bodynodeobj_ori


def get_bodynodeobj_glove(bodypart, finger):
    """Get glove bodynodes object"""

    if bodypart + "_" + finger not in bpy.data.objects:
        print(bodypart + " bodynodeobj glove has not been found")
        return None
    return bpy.data.objects[bodypart + "_" + finger]


def get_bodynode_rotation_quaternion(bodypart):
    """Get the bodynode rotation as a quaternion"""
    if bodypart not in bpy.data.objects:
        print(bodypart + " hasn't been found")
        return None
    return bpy.data.objects[bodypart].rotation_quaternion


def set_bodynode_rotation_quaternion(bodypart, rotation_quaternion):
    """Set the bodynode rotation with a quaternion"""

    if bodypart not in bpy.data.objects:
        print(bodypart + " hasn't been found")
        return
    bpy.data.objects[bodypart].rotation_quaternion = rotation_quaternion
