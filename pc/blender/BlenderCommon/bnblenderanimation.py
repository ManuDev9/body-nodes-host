#
# MIT License
#
# Copyright (c) 2019-2026 Manuel Bottini
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

"""Animation Panel to easily edit Bodynodes animation data on Blender"""

import sys
import json
from dataclasses import dataclass
import bpy
import mathutils
from bpy_extras.io_utils import ExportHelper, ImportHelper

if "bnblenderaxis" in sys.modules:
    del sys.modules["bnblenderaxis"]

from bnblenderaxis import (  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
    BodynodesAxis,
)


@dataclass
class Internal:
    """Internal module data dataclass"""

    player_selected_anim = "None"
    bodynodes_saved_armature_change_anim = {}
    bodynodes_animation_editor_moves_selected_bones = []


internal = Internal()


bodynodes_panel_anim = {
    "editor_moves": {
        "created": False,
    },
    "rot_change": False,
    "loc_change": False,
}


def find_players():
    """Find players"""

    players_available = (("None", "None", ""),)
    for bpy_object in bpy.data.objects:
        if "BNP" in bpy_object.name_full:
            if (
                "_pos" not in bpy_object.name_full
                and "_ori" not in bpy_object.name_full
            ):
                players_available = players_available + (
                    (bpy_object.name_full + "", bpy_object.name_full + "", ""),
                )

    bpy.types.Scene.players_list_animation = bpy.props.EnumProperty(
        items=players_available,
        name="Player",
        description="Player to consider for animation",
        update=change_animation_player_fun,
    )

    if len(players_available) == 2:
        bpy.context.scene.players_list_animation = players_available[1][0]
    else:
        bpy.context.scene.players_list_animation = "None"


def create_hip_constraints():
    """Create hip constraints"""

    if internal.player_selected_anim + "_pos" not in bpy.data.objects:
        print("Reference object does not exist")
        return
    if (
        "Copy Location"
        not in bpy.data.objects[internal.player_selected_anim]
        .pose.bones["Hip"]
        .constraints
    ):
        bpy.data.objects[internal.player_selected_anim].pose.bones[
            "Hip"
        ].constraints.new(type="COPY_LOCATION")
        bpy.data.objects[internal.player_selected_anim].pose.bones["Hip"].constraints[
            "Copy Location"
        ].target = bpy.data.objects[internal.player_selected_anim + "_pos"]


def bake_animation(start=None, end=None, keep_hip_constr=True):
    """Bake animation"""

    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = bpy.data.objects[
        internal.player_selected_anim
    ]
    bpy.data.objects[internal.player_selected_anim].select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    for b in bpy.data.objects[internal.player_selected_anim].pose.bones:
        b.bone.select = True

    if start is None:
        start = bpy.context.scene.frame_start
    if end is None:
        end = bpy.context.scene.frame_end
    bpy.ops.nla.bake(
        frame_start=start,
        frame_end=end,
        step=1,
        only_selected=True,
        visual_keying=True,
        clear_constraints=True,
        use_current_action=True,
        bake_types={"POSE"},
    )

    for b in bpy.data.objects[internal.player_selected_anim].pose.bones:
        b.bone.select = False

    for bodypart, baconfig in BodynodesAxis.Config.items():
        if baconfig["bone_name"] == "":
            continue
        if bodypart in bpy.data.objects:
            bpy.data.objects[bodypart].animation_data_clear()

    if internal.player_selected_anim + "_pos" in bpy.data.objects:
        if keep_hip_constr:
            create_hip_constraints()
        else:
            bpy.data.objects[
                internal.player_selected_anim + "_pos"
            ].animation_data_clear()


def save_animation_json(filepath):
    """Save animation as json"""

    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    animation_json = {}
    for bodypart, baconfig in BodynodesAxis.Config.items():
        if baconfig["bone_name"] == "":
            continue
        animation_json[bodypart] = []

    for bodypart, anim_elem in animation_json.items():
        for frame in range(start, end + 1):
            bpy.context.scene.frame_set(frame)
            obj_quat = mathutils.Quaternion(
                get_bone_global_rotation_quaternion_anim(
                    BodynodesAxis.Config[bodypart]["bone_name"]
                )
            )
            keyframe_info = {
                "rotation_quaternion": [obj_quat.w, obj_quat.x, obj_quat.y, obj_quat.z],
                "frame_current": frame - start,
            }
            anim_elem.append(keyframe_info)

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(json.dumps(animation_json, indent=4, sort_keys=True))


def add_bodynodes_constr():
    """Add bodynodes constraits"""

    if internal.player_selected_anim == "None":
        return
    create_hip_constraints()

    for bodypart, baconfig in BodynodesAxis.Config.items():
        if baconfig["bone_name"] == "":
            continue
        bone_name = baconfig["bone_name"]
        if bodypart in bpy.data.objects:
            if (
                "Copy Rotation"
                not in bpy.data.objects[internal.player_selected_anim]
                .pose.bones[bodypart]
                .constraints
            ):
                bpy.data.objects[internal.player_selected_anim].pose.bones[
                    bone_name
                ].constraints.new(type="COPY_ROTATION")
                bpy.data.objects[internal.player_selected_anim].pose.bones[
                    bone_name
                ].constraints["Copy Rotation"].target = bpy.data.objects[bodypart]


def load_fbx(filepath):
    """Load FBX file"""

    # Remove all data
    try:
        while True:
            bpy.data.armatures.remove(bpy.data.armatures[0])
    except IndexError:
        pass
    try:
        while True:
            bpy.data.objects.remove(bpy.data.objects[0])
    except IndexError:
        pass
    try:
        while True:
            bpy.data.actions.remove(bpy.data.actions[0])
    except IndexError:
        pass

    # Import the .fbx
    bpy.ops.import_scene.fbx(filepath=filepath)

    bpy.ops.object.add()
    bpy.context.active_object.name = internal.player_selected_anim + "_pos"
    bpy.context.active_object.location = mathutils.Vector((0, 0, 0))

    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end

    bpy.data.objects[internal.player_selected_anim + "_pos"].constraints.new(
        type="COPY_LOCATION"
    )
    bpy.data.objects[internal.player_selected_anim + "_pos"].constraints[
        "Copy Location"
    ].target = bpy.data.objects[internal.player_selected_anim]
    bpy.data.objects[internal.player_selected_anim + "_pos"].constraints[
        "Copy Location"
    ].subtarget = "Hip"
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = bpy.data.objects[
        internal.player_selected_anim + "_pos"
    ]
    bpy.data.objects[internal.player_selected_anim + "_pos"].select_set(True)
    bpy.ops.nla.bake(
        frame_start=start,
        frame_end=end,
        step=1,
        only_selected=True,
        visual_keying=True,
        clear_constraints=True,
        use_current_action=True,
        bake_types={"OBJECT"},
    )
    create_hip_constraints()


def save_animation_fbx(filepath):
    """Save animation FBX"""

    # Bake all bones constraints and clean
    # Bake hip bone constraints and clean
    bake_animation(keep_hip_constr=False)
    # Remove all not necessary actions
    action_to_keep = bpy.data.objects[
        internal.player_selected_anim
    ].animation_data.action

    for action in bpy.data.actions:
        if action.name != action_to_keep.name:
            bpy.data.actions.remove(action)

    # Select what you need
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = bpy.data.objects[
        internal.player_selected_anim
    ]
    bpy.data.objects[internal.player_selected_anim].children[0].select_set(True)
    bpy.data.objects[internal.player_selected_anim].select_set(True)
    # Save scene as .fbx file with only model and one animation in it
    # Compatible for Blender 2.82 (you need to adapt to your blender version)
    # This is the video I got the main parameters from: https://www.youtube.com/watch?v=ysl0qYq5p9w
    bpy.ops.export_scene.fbx(
        filepath=filepath,
        check_existing=True,
        filter_glob="*.fbx",
        use_selection=True,
        use_active_collection=False,
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_NONE",
        bake_space_transform=False,
        object_types={"ARMATURE", "MESH"},
        use_mesh_modifiers=True,
        use_mesh_modifiers_render=True,
        mesh_smooth_type="OFF",
        use_subsurf=False,
        use_mesh_edges=False,
        use_tspace=False,
        use_custom_props=False,
        add_leaf_bones=False,
        primary_bone_axis="Y",
        secondary_bone_axis="X",
        use_armature_deform_only=False,
        armature_nodetype="NULL",
        bake_anim=True,
        bake_anim_use_all_bones=False,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=True,
        bake_anim_force_startend_keying=False,
        bake_anim_step=1.0,
        bake_anim_simplify_factor=1.0,
        path_mode="AUTO",
        embed_textures=False,
        batch_mode="OFF",
        use_batch_own_dir=True,
        use_metadata=True,
        axis_forward="-Z",
        axis_up="Y",
    )
    if internal.player_selected_anim + "_pos" in bpy.data.objects:
        create_hip_constraints()


def save_model_fbx(filepath):
    """Save model FBX"""

    # Bake all bones constraints and clean
    # Bake hip bone constraints and clean
    bake_animation(keep_hip_constr=False)

    for action in bpy.data.actions:
        bpy.data.actions.remove(action)

    # Select what you need
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = bpy.data.objects[
        internal.player_selected_anim
    ]
    bpy.data.objects[internal.player_selected_anim].children[0].select_set(True)
    bpy.data.objects[internal.player_selected_anim].select_set(True)
    # Save scene as .fbx file with only model and one animation in it
    # Compatible for Blender 2.82 (you need to adapt to your blender version)
    bpy.ops.export_scene.fbx(
        filepath=filepath,
        check_existing=True,
        filter_glob="*.fbx",
        use_selection=True,
        use_active_collection=False,
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_NONE",
        bake_space_transform=False,
        object_types={"ARMATURE", "MESH"},
        use_mesh_modifiers=True,
        use_mesh_modifiers_render=True,
        mesh_smooth_type="OFF",
        use_subsurf=False,
        use_mesh_edges=False,
        use_tspace=False,
        use_custom_props=False,
        add_leaf_bones=False,
        primary_bone_axis="Y",
        secondary_bone_axis="X",
        use_armature_deform_only=False,
        armature_nodetype="NULL",
        bake_anim=True,
        bake_anim_use_all_bones=False,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=True,
        bake_anim_force_startend_keying=False,
        bake_anim_step=1.0,
        bake_anim_simplify_factor=1.0,
        path_mode="AUTO",
        embed_textures=False,
        batch_mode="OFF",
        use_batch_own_dir=True,
        use_metadata=True,
        axis_forward="-Z",
        axis_up="Y",
    )
    if internal.player_selected_anim + "_pos" in bpy.data.objects:
        create_hip_constraints()


def load_animation(filepath):
    """Load animation"""

    # Load animation on bodynodes objects
    with open(filepath, encoding="utf-8") as file:
        animation_json = json.load(file)

    start = bpy.context.scene.frame_start
    for bodypart in animation_json.keys():
        for keyframe_info in animation_json[bodypart]:
            player_bodypart = get_bodynodeobj_ori(bodypart)
            set_bodynode_rotation_quaternion(
                bodypart, mathutils.Quaternion((keyframe_info["rotation_quaternion"]))
            )
            player_bodypart.keyframe_insert(
                data_path="rotation_quaternion",
                frame=(keyframe_info["frame_current"] + start),
            )

    # Apply bodynodes objects constraints to bones
    for bodypart in animation_json.keys():
        if (
            "Copy Rotation"
            not in bpy.data.objects[internal.player_selected_anim]
            .pose.bones[bodypart]
            .constraints
        ):
            bpy.data.objects[internal.player_selected_anim].pose.bones[
                bodypart
            ].constraints.new(type="COPY_ROTATION")
            bpy.data.objects[internal.player_selected_anim].pose.bones[
                bodypart
            ].constraints["Copy Rotation"].target = bpy.data.objects[bodypart]

    # Bake
    bake_animation()


def create_animation_editor_moves():
    """Create editor moves"""

    bodynodes_panel_anim["editor_moves"]["created"] = True
    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    bpy.context.scene.frame_set(start)

    if "Animation" not in bpy.data.collections:
        bpy.ops.collection.create(name="Animation")
        bpy.context.scene.collection.children.link(bpy.data.collections["Animation"])

    bpy.ops.object.mode_set(mode="OBJECT")

    # Get selected bones
    internal.bodynodes_animation_editor_moves_selected_bones = []
    for bone in bpy.data.objects[internal.player_selected_anim].data.bones.items():
        if bone[1].select:
            internal.bodynodes_animation_editor_moves_selected_bones.append(bone[0])
            bpy.ops.object.empty_add(
                type="CUBE", location=get_bone_global_tail_location_anim(bone[0])
            )
            ikobj_name = "__temp_" + bone[0] + "_ik"
            bpy.data.objects["Empty"].name = ikobj_name
            bpy.data.objects[ikobj_name].scale = mathutils.Vector((0.2, 0.2, 0.2))
            if ikobj_name not in bpy.data.collections["Animation"].objects:
                bpy.data.collections["Animation"].objects.link(
                    bpy.data.objects[ikobj_name]
                )

    if len(internal.bodynodes_animation_editor_moves_selected_bones) == 0:
        print("Nothing was selected")

    for frame in range(start, end + 1):
        bpy.context.scene.frame_set(frame)
        for bone in internal.bodynodes_animation_editor_moves_selected_bones:
            # bpy.data.objects[internal.player_selected_anim].pose.bones["Toe_R"]
            bpy.ops.object.empty_add(
                type="SPHERE", location=get_bone_global_tail_location_anim(bone)
            )
            obj_name = "__temp_" + bone + "_" + str(frame)
            bpy.data.objects["Empty"].name = obj_name
            bpy.data.objects[obj_name].scale = mathutils.Vector((0.1, 0.1, 0.1))
            if obj_name not in bpy.data.collections["Animation"].objects:
                bpy.data.collections["Animation"].objects.link(
                    bpy.data.objects[obj_name]
                )

    for bone in internal.bodynodes_animation_editor_moves_selected_bones:
        # Apply location constraints on the bones
        ikobj_name = "__temp_" + bone + "_ik"
        bpy.data.objects[internal.player_selected_anim].pose.bones[
            bone
        ].constraints.new(type="IK")
        bpy.data.objects[internal.player_selected_anim].pose.bones[bone].constraints[
            "IK"
        ].target = bpy.data.objects[ikobj_name]
        bpy.data.objects[internal.player_selected_anim].pose.bones[bone].constraints[
            "IK"
        ].chain_count = 1

    update_animation_editor_moves()


def update_animation_editor_moves():
    """Update editor moves"""

    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    for frame in range(start, end + 1):
        for bone in internal.bodynodes_animation_editor_moves_selected_bones:
            bpy.context.scene.frame_set(frame)
            obj_name = "__temp_" + bone + "_" + str(frame)
            ikobj_name = "__temp_" + bone + "_ik"
            bpy.data.objects[ikobj_name].location = bpy.data.objects[obj_name].location
            bpy.data.objects[ikobj_name].keyframe_insert(
                data_path="location", frame=(frame)
            )


def save_animation_editor_moves():
    """Save editor moves"""
    bake_animation()
    destroy_animation_editor_moves()


def destroy_animation_editor_moves():
    """Destroy editor moves"""

    bodynodes_panel_anim["editor_moves"]["created"] = False
    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    for bone in internal.bodynodes_animation_editor_moves_selected_bones:
        for frame in range(start, end + 1):
            obj_name = "__temp_" + bone + "_" + str(frame)
            bpy.data.objects.remove(bpy.data.objects[obj_name], do_unlink=True)

        if (
            "IK"
            in bpy.data.objects[internal.player_selected_anim]
            .pose.bones[bone]
            .constraints
        ):
            bpy.data.objects[internal.player_selected_anim].pose.bones[
                bone
            ].constraints.remove(
                bpy.data.objects[internal.player_selected_anim]
                .pose.bones[bone]
                .constraints["IK"]
            )
        ikobj_name = "__temp_" + bone + "_ik"
        bpy.data.objects.remove(bpy.data.objects[ikobj_name], do_unlink=True)


def start_rot_change_animation():
    """Start rotation change"""

    for bodypart, bnconfig in BodynodesAxis.Config.items():
        if bnconfig["bone_name"] == "":
            continue
        obj_quat = get_bodypart_bone(bodypart).rotation_quaternion
        internal.bodynodes_saved_armature_change_anim[bodypart] = mathutils.Quaternion(
            (obj_quat)
        )

    obj_quat = get_bodypart_bone("Hip").rotation_quaternion
    internal.bodynodes_saved_armature_change_anim["Hip"] = mathutils.Quaternion(
        (obj_quat)
    )


def start_loc_change_animation():
    """Start location change"""

    obj_loc = bpy.data.objects[internal.player_selected_anim + "_pos"].location
    internal.bodynodes_saved_armature_change_anim["location"] = mathutils.Vector(
        (obj_loc)
    )


def done_loc_change_animation():
    """Done location change"""

    puppet_diff_anim = {}
    obj_loc = bpy.data.objects[internal.player_selected_anim + "_pos"].location
    puppet_diff_anim["location"] = (
        obj_loc - internal.bodynodes_saved_armature_change_anim["location"]
    )

    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end

    for frame in range(start, end + 1):
        bpy.context.scene.frame_set(frame)
        player_bodypart = bpy.data.objects[internal.player_selected_anim + "_pos"]
        player_bodypart.location = (
            player_bodypart.location + puppet_diff_anim["location"]
        )

        # This might crash, add the proper try-catch
        if player_bodypart.keyframe_delete(data_path="location", frame=frame):
            player_bodypart.keyframe_insert(data_path="location", frame=frame)

    bpy.context.scene.frame_set(start)


def done_rot_change_animation():
    """Done rotation change"""

    puppet_diff_anim = {}
    for bodypart, bn_item in internal.bodynodes_saved_armature_change_anim.items():
        obj_quat = get_bodypart_bone(bodypart).rotation_quaternion
        if bn_item != obj_quat:
            puppet_diff_anim[bodypart] = obj_quat @ bn_item.inverted()

    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end

    for frame in range(start, end + 1):
        bpy.context.scene.frame_set(frame)
        for bodypart, puppet_diff_elem in puppet_diff_anim.items():
            player_bodypart = get_bodypart_bone(bodypart)
            player_bodypart.rotation_quaternion = (
                puppet_diff_elem @ player_bodypart.rotation_quaternion
            )
            if player_bodypart.keyframe_delete(
                data_path="rotation_quaternion", frame=frame
            ):
                player_bodypart.keyframe_insert(
                    data_path="rotation_quaternion", frame=frame
                )

    bpy.context.scene.frame_set(start)


def change_animation_player_fun(
    self, context
):  # pylint: disable=unused-argument # Blender callback
    """Change Player button callback"""

    internal.player_selected_anim = self.players_list_animation


def redirect_bodypart_anim(bodypart):
    """redirect bodypart to another one"""

    if (
        bodypart in BodynodesAxis.Config
        and BodynodesAxis.Config[bodypart]["bone_name"] != ""
    ):
        return BodynodesAxis.Config[bodypart]["bone_name"]
    return bodypart


def get_bodypart_bone(bodypart):
    """Get bodynode bone of bodypart"""

    bone_name = redirect_bodypart_anim(bodypart)
    if bodypart not in bpy.data.objects[internal.player_selected_anim].pose.bones:
        print(bodypart + " bone has not been found")
        return None

    return bpy.data.objects[internal.player_selected_anim].pose.bones[bone_name]


def get_bodynodeobj_ori(bodypart):
    """Get bodynode object of bodypart"""

    if bodypart + "_ori" not in bpy.data.objects:
        print(bodypart + " bodynodeobj orientation has not been found")
        return None
    return bpy.data.objects[bodypart + "_ori"]


def get_bone_global_rotation_quaternion_anim(bone):
    """Get global rotation as quaternion of bone"""

    if bone not in bpy.data.objects[internal.player_selected_anim].pose.bones:
        print(bone + " bone has not been found")
        return None
    return (
        bpy.data.objects[internal.player_selected_anim].matrix_world
        @ bpy.data.objects[internal.player_selected_anim].pose.bones[bone].matrix
    ).to_quaternion()


def get_bone_global_location_anim(bone):
    """Get global location of bone"""

    if bone not in bpy.data.objects[internal.player_selected_anim].pose.bones:
        print(bone + " bone has not been found")
        return None

    return (
        bpy.data.objects[internal.player_selected_anim].matrix_world
        @ bpy.data.objects[internal.player_selected_anim].pose.bones[bone].matrix
        @ bpy.data.objects[internal.player_selected_anim].pose.bones[bone].location
    )


def get_bone_global_tail_location_anim(bone):
    """Get global location of bone tail"""

    if bone not in bpy.data.objects[internal.player_selected_anim].pose.bones:
        print(bone + " bone has not been found")
        return None

    return (
        bpy.data.objects[internal.player_selected_anim].matrix_world
        @ bpy.data.objects[internal.player_selected_anim].pose.bones[bone].tail
    )


# def set_bodynode_rotation_quaternion(player, bodypart, rotation_quaternion):
# bone = get_bodypart_bone(bodypart)
# loc, rot, sca = bone.matrix.decompose()
# mat_loc = Matrix.Translation(loc)
# mat_sca = Matrix()
# mat_sca[0][0] = 1
# mat_sca[1][1] = 1
# mat_sca[2][2] = 1
# mat_rot = (bpy.data.objects[player].matrix_world.inverted().to_quaternion() @ rotation_quaternion).to_matrix().to_4x4()
# bone.matrix = mat_loc @ mat_rot @ mat_sca


def get_bodynode_rotation_quaternion(bodypart):
    """Get quaternion rotation of bodynode object"""

    if bodypart not in bpy.data.objects:
        print(bodypart + " hasn't been found")
        return None

    return bpy.data.objects[bodypart].rotation_quaternion


def set_bodynode_rotation_quaternion(bodypart, rotation_quaternion):
    """Set bodynode object rotation with quaternion"""

    if bodypart not in bpy.data.objects:
        print(bodypart + " hasn't been found")
        return

    bpy.data.objects[bodypart].rotation_mode = "QUATERNION"
    bpy.data.objects[bodypart].rotation_quaternion = rotation_quaternion


def apply_ref_walk(full_3d=False):
    """Apply ref walk algo"""

    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    bpy.context.scene.frame_set(start)
    player_ref = bpy.data.objects[internal.player_selected_anim + "_pos"]

    bpy.context.scene.frame_set(start - 1)
    ref_foot = bpy.data.objects[internal.player_selected_anim].data.bones.active.name
    ref_foot_prev_glocation = get_bone_global_location_anim(ref_foot)

    # We will work every 2 frames be so that the animation will be smoother
    step = 2
    if full_3d:
        step = 1
    for frame in range(start, end + 1, step):
        bpy.context.scene.frame_set(frame)
        diff_glocation = (
            get_bone_global_location_anim(ref_foot) - ref_foot_prev_glocation
        )
        player_ref.location[0] -= diff_glocation[0]
        player_ref.location[1] -= diff_glocation[1]
        if full_3d:
            player_ref.location[2] -= diff_glocation[2]
        player_ref.keyframe_insert(data_path="location", frame=frame)


def apply_auto_walk():
    """Apply auto walk algo"""

    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    player_ref = bpy.data.objects[internal.player_selected_anim + "_pos"]

    ref_foot = None
    ref_foot_prev_glocation = None

    # We will work every 2 frames be so that the animation will be smoother
    for frame in range(start, end + 1, 2):

        # Check ref foot
        ltoe_glocation_now = get_bone_global_location_anim("Toe_L")
        rtoe_glocation_now = get_bone_global_location_anim("Toe_R")
        lfoot_glocation_now = get_bone_global_location_anim("Foot_L")
        rfoot_glocation_now = get_bone_global_location_anim("Foot_R")

        lmid_z = (ltoe_glocation_now[2] + lfoot_glocation_now[2]) / 2
        rmid_z = (rtoe_glocation_now[2] + rfoot_glocation_now[2]) / 2

        # Which one is lower?
        if lmid_z > rmid_z:
            ref_foot = "Toe_R"
        else:
            ref_foot = "Toe_L"

        bpy.context.scene.frame_set(frame - 2)
        ref_foot_prev_glocation = get_bone_global_location_anim(ref_foot)
        bpy.context.scene.frame_set(frame)
        diff_glocation = (
            get_bone_global_location_anim(ref_foot) - ref_foot_prev_glocation
        )
        player_ref.location[0] -= diff_glocation[0]
        player_ref.location[1] -= diff_glocation[1]
        player_ref.keyframe_insert(data_path="location", frame=frame)


def apply_steady_feet_ref():
    """Create steady feet objects"""

    # Let's check what we have selected
    ref_foot = bpy.data.objects[internal.player_selected_anim].data.bones.active.name
    if ref_foot not in ("Foot_L", "Foot_R"):
        print("Please select one of the feet")
        return

    # We apply the ref walk algorithm on the selected foot
    apply_ref_walk(True)

    # We take to other leg
    if ref_foot == "Foot_R":
        other_foot = "Foot_L"
        other_lowerleg = redirect_bodypart_anim("lowerleg_left")
    else:
        other_foot = "Foot_R"
        other_lowerleg = redirect_bodypart_anim("lowerleg_right")

    # Remove animation data from other leg, if any
    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    for frame in range(start + 1, end + 1):
        bpy.data.objects[internal.player_selected_anim].pose.bones[
            other_lowerleg
        ].keyframe_delete(data_path="rotation_quaternion", frame=frame)
        bpy.data.objects[internal.player_selected_anim].pose.bones[
            other_foot
        ].keyframe_delete(data_path="rotation_quaternion", frame=frame)

    # Create a temporary empty object in same position of other_foot
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.empty_add(
        type="SPHERE", location=get_bone_global_location_anim(other_foot)
    )
    bpy.data.objects["Empty"].name = "__temp1"
    loc_position_obj = bpy.data.objects["__temp1"]

    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = bpy.data.objects[
        internal.player_selected_anim
    ]
    bpy.data.objects[internal.player_selected_anim].select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    bpy.data.objects[internal.player_selected_anim].data.bones[ref_foot].select = True

    # Apply the auto IK constraint on the other_lowerleg
    if (
        "IK"
        in bpy.data.objects[internal.player_selected_anim]
        .pose.bones[other_lowerleg]
        .constraints
    ):
        bpy.data.objects[internal.player_selected_anim].pose.bones[
            other_lowerleg
        ].constraints.remove(
            bpy.data.objects[internal.player_selected_anim]
            .pose.bones[other_lowerleg]
            .constraints["IK"]
        )
    bpy.data.objects[internal.player_selected_anim].pose.bones[
        other_lowerleg
    ].constraints.new(type="IK")
    bpy.data.objects[internal.player_selected_anim].pose.bones[
        other_lowerleg
    ].constraints["IK"].target = loc_position_obj
    bpy.data.objects[internal.player_selected_anim].pose.bones[
        other_lowerleg
    ].constraints["IK"].chain_count = 2

    # Apply bake, which will remove contraints
    bake_animation()

    # Remove the temporary object
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.data.objects.remove(loc_position_obj, do_unlink=True)
    bpy.ops.object.mode_set(mode="POSE")


def create_steady_handorfoot_obj():
    """Create steady object"""

    # Let's check what we have selected
    ref_part = bpy.data.objects[internal.player_selected_anim].data.bones.active.name

    if not any(bone_name in ref_part for bone_name in ["hand", "Hand", "foot", "Foot"]):
        print("Select and Hand or a Foot bone")

    # Positioning animation has already been processed.
    # Here we wan the bones to stick and follow the rest of the body

    # Create a temporary empty object in same position of ref_part
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.empty_add(
        type="SPHERE", location=get_bone_global_location_anim(ref_part)
    )
    bpy.data.objects["Empty"].name = "__temp1"
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = bpy.data.objects[
        internal.player_selected_anim
    ]
    bpy.data.objects[internal.player_selected_anim].select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    bpy.data.objects[internal.player_selected_anim].data.bones[ref_part].select = True


def apply_steady_handorfoot_ref():
    """Apply steady algo"""

    if "__temp1" not in bpy.data.objects:
        print("Click on HOF Obj first")

    # Let's check what we have selected
    ref_part = bpy.data.objects[internal.player_selected_anim].data.bones.active.name

    if not any(bone_name in ref_part for bone_name in ["hand", "Hand", "foot", "Foot"]):
        print("Select and Hand or a Foot bone")

    # Positioning animation has already been processed.
    # Here we wan the bones to stick and follow the rest of the body
    bpy.ops.object.mode_set(mode="OBJECT")

    # Create a temporary empty object in same position of ref_part
    loc_position_obj = bpy.data.objects["__temp1"]

    # Let's take the frames
    frames = {
        "start": bpy.context.scene.frame_start,
        "end": bpy.context.scene.frame_end,
    }
    bpy.context.scene.frame_set(frames["start"])

    bpy.ops.object.mode_set(mode="OBJECT")

    # Get bones to use
    bones_to_use = [
        bpy.data.armatures["DancerArmature"].bones[ref_part].parent.name,
        bpy.data.armatures["DancerArmature"].bones[ref_part].parent.parent.name,
    ]

    for bone_to_use in bones_to_use:
        bone = bpy.data.armatures["DancerArmature"].bones[bone_to_use]
        bpy.ops.object.empty_add(
            type="CUBE", location=get_bone_global_tail_location_anim(bone_to_use)
        )
        ikobj_name = "__temp_" + bone_to_use + "_ik"
        bpy.data.objects["Empty"].name = ikobj_name
        bpy.data.objects[ikobj_name].scale = mathutils.Vector((0.2, 0.2, 0.2))

    for frame in range(frames["start"], frames["end"] + 1):
        bpy.context.scene.frame_set(frame)
        for bone in bones_to_use:
            # bpy.data.objects[internal.player_selected_anim].pose.bones["Toe_R"]
            bpy.ops.object.empty_add(
                type="SPHERE", location=get_bone_global_tail_location_anim(bone)
            )
            obj_name = "__temp_" + bone + "_" + str(frame)
            bpy.data.objects["Empty"].name = obj_name
            bpy.data.objects[obj_name].scale = mathutils.Vector((0.1, 0.1, 0.1))

    for bone in bones_to_use:
        # Apply location constraints on the bones
        ikobj_name = "__temp_" + bone + "_ik"
        bpy.data.objects[internal.player_selected_anim].pose.bones[
            bone
        ].constraints.new(type="IK")
        bpy.data.objects[internal.player_selected_anim].pose.bones[bone].constraints[
            "IK"
        ].target = bpy.data.objects[ikobj_name]
        bpy.data.objects[internal.player_selected_anim].pose.bones[bone].constraints[
            "IK"
        ].chain_count = 1

    # I move the ALL IK constraints to force the hand in the position I selected

    # I start by moving the single objects
    for frame in range(frames["start"], frames["end"] + 1):
        bone_p1 = bpy.data.armatures["DancerArmature"].bones[ref_part].parent.name
        bone_p2 = (
            bpy.data.armatures["DancerArmature"].bones[ref_part].parent.parent.name
        )
        obj_p1_name = "__temp_" + bone_p1 + "_" + str(frame)
        obj_p2_name = "__temp_" + bone_p2 + "_" + str(frame)
        delta = loc_position_obj.location - bpy.data.objects[obj_p1_name].location
        bpy.data.objects[obj_p1_name].location = loc_position_obj.location
        bpy.data.objects[obj_p2_name].location = (
            bpy.data.objects[obj_p2_name].location + delta
        )

    for frame in range(frames["start"], frames["end"] + 1):
        for bone in bones_to_use:
            bpy.context.scene.frame_set(frame)
            obj_name = "__temp_" + bone + "_" + str(frame)
            ikobj_name = "__temp_" + bone + "_ik"
            bpy.data.objects[ikobj_name].location = bpy.data.objects[obj_name].location
            bpy.data.objects[ikobj_name].keyframe_insert(
                data_path="location", frame=(frame)
            )

    # Apply bake, which will remove contraints
    bake_animation()

    for bone in bones_to_use:
        for frame in range(frames["start"], frames["end"] + 1):
            obj_name = "__temp_" + bone + "_" + str(frame)
            bpy.data.objects.remove(bpy.data.objects[obj_name], do_unlink=True)

        if (
            "IK"
            in bpy.data.objects[internal.player_selected_anim]
            .pose.bones[bone]
            .constraints
        ):
            bpy.data.objects[internal.player_selected_anim].pose.bones[
                bone
            ].constraints.remove(
                bpy.data.objects[internal.player_selected_anim]
                .pose.bones[bone]
                .constraints["IK"]
            )
        ikobj_name = "__temp_" + bone + "_ik"
        bpy.data.objects.remove(bpy.data.objects[ikobj_name], do_unlink=True)

    # Remove the temporary object
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.data.objects.remove(loc_position_obj, do_unlink=True)


def repeat_mirror():
    """Repeat Mirror"""

    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    offset = end - start + 1

    for bodypart, baconfig in BodynodesAxis.Config.items():
        if baconfig["bone_name"] == "":
            continue
        bodypart_to_use = bodypart

        if "left" in bodypart_to_use:
            bodypart_to_use = bodypart_to_use.replace("left", "right")
        elif "right" in bodypart_to_use:
            bodypart_to_use = bodypart_to_use.replace("right", "left")
        bodypart_to_key = bpy.data.objects[bodypart_to_use]
        bodypart_to_key.rotation_mode = "XYZ"

        for frame in range(start, end + 1):
            bpy.context.scene.frame_set(frame)
            eul = get_bone_global_rotation_quaternion_anim(bodypart).to_euler()
            eul[1] = -eul[1]
            eul[2] = -eul[2]
            bodypart_to_key.rotation_euler = eul
            bodypart_to_key.keyframe_insert(
                data_path="rotation_euler", frame=(frame + offset)
            )

    # This has to be done separately to let the left side get properly recorded from right side
    for bodypart, _ in BodynodesAxis.Config.items():
        if (
            "Copy Rotation"
            not in bpy.data.objects[internal.player_selected_anim]
            .pose.bones[bodypart]
            .constraints
        ):
            bpy.data.objects[internal.player_selected_anim].pose.bones[
                bodypart
            ].constraints.new(type="COPY_ROTATION")
            bpy.data.objects[internal.player_selected_anim].pose.bones[
                bodypart
            ].constraints["Copy Rotation"].target = bpy.data.objects[bodypart]

    bake_animation(end + 1, end + offset)

    # Let's work on the location reference object and move it opposite to already recorded animation
    # ref_obj = bpy.data.objects[internal.player_selected_anim+"_pos"]
    # for frame in range(start+1, end+1):
    # 	bpy.context.scene.frame_set(frame-1)
    # 	loc_prev = mathutils.Vector(ref_obj.location)
    # 	bpy.context.scene.frame_set(frame)
    # 	loc_diff = ref_obj.location - loc_prev
    # 	loc_diff[0] = -loc_diff[0]
    # 	bpy.context.scene.frame_set(frame+offset)
    # 	ref_obj.location += loc_diff
    # 	ref_obj.keyframe_insert(data_path='location', frame=(frame+offset))


class PANEL_PT_BodynodesAnimation(
    bpy.types.Panel
):  # pylint: disable=invalid-name # reason: Blender naming convention
    """Bodynodes Animation Blender Panel"""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"
    bl_label = "Bodynodes Animation"

    def draw_animation_section(self):
        """Draw animation section"""

        layout = self.layout
        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.label(text="Animation:")
        col2 = row.column()
        col2.operator("bodynodes.load_animation", text="Load")
        col2.enabled = True
        col3 = row.column()
        col3.operator("bodynodes.bake_animation", text="Bake")
        col3.enabled = True

    def draw_moveditor_section(self):
        """Draw Movements Editor section"""

        layout = self.layout
        layout.label(text="Movements Editor:")
        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator("bodynodes.create_animation_editor_moves", text="Create")
        col1.enabled = not bodynodes_panel_anim["editor_moves"]["created"]
        col2 = row.column()
        col2.operator("bodynodes.update_animation_editor_moves", text="Update")
        col2.enabled = bodynodes_panel_anim["editor_moves"]["created"]
        col3 = row.column()
        col3.operator("bodynodes.save_animation_editor_moves", text="Save")
        col3.enabled = True
        col4 = row.column()
        col4.operator("bodynodes.destroy_animation_editor_moves", text="Destroy")
        col4.enabled = True

    def draw_walking_section(self):
        """Draw Walking section"""

        layout = self.layout
        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.label(text="Walking:")
        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator("bodynodes.apply_auto_walk", text="Auto")
        col1.enabled = True
        col2 = row.column()
        col2.operator("bodynodes.apply_ref_walk_2d", text="Ref 2D")
        col2.enabled = True
        col3 = row.column()
        col3.operator("bodynodes.apply_ref_walk_3d", text="Ref 3D")
        col3.enabled = True

    def draw_steady_section(self):
        """Draw Steady Algos section"""

        layout = self.layout
        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.label(text="Steady:")
        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator("bodynodes.apply_steady_feet_ref", text="Feet Ref")
        col1.enabled = True
        col2 = row.column()
        col2.operator("bodynodes.create_steady_handorfoot_obj", text="HOF Obj")
        col2.enabled = True
        col3 = row.column()
        col3.operator("bodynodes.apply_steady_handorfoot_ref", text="HOF Ref")
        col3.enabled = True
        row = layout.row()

        row.scale_y = 1.0
        col1 = row.column()
        col1.label(text="Repeat:")
        col2 = row.column()
        col2.operator("bodynodes.repeat_mirror", text="Mirror")

    def draw_changes_section(self):
        """Draw Changes section"""

        layout = self.layout
        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.label(text="Rot Changes:")
        col2 = row.column()
        col2.operator(
            "bodynodes.startdone_rot_change_animation",
            text="Done" if bodynodes_panel_anim["rot_change"] else "Start",
        )
        col2.enabled = True

        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.label(text="Loc Changes:")
        col2 = row.column()
        col2.operator(
            "bodynodes.startdone_loc_change_animation",
            text="Done" if bodynodes_panel_anim["loc_change"] else "Start",
        )
        col2.enabled = True

    def draw_loadsave_section(self):
        """Draw Load and Save data section"""

        layout = self.layout
        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator("bodynodes.save_animation_json", text="Save JSON")
        col1.enabled = True

        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.label(text="FBX:")
        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator("bodynodes.load_fbx", text="Load Anim FBX")
        col1.enabled = True

        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator("bodynodes.save_animation_fbx", text="Save Anim FBX")
        col1.enabled = True

        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator("bodynodes.save_model_fbx", text="Save Model FBX")
        col1.enabled = True

    def draw(self, context):
        layout = self.layout

        if not BodynodesAxis.Config:
            row = layout.row()
            row.scale_y = 1.0
            col1 = row.column()
            col1.label(text="Load a configuration file")
            return

        row = layout.row()
        row.prop(context.scene, "players_list_animation")

        if internal.player_selected_anim == "None":
            row = layout.row()
            row.scale_y = 1.0
            col1 = row.column()
            col1.label(text="Select a player")
            return

        self.draw_animation_section()
        self.draw_moveditor_section()
        self.draw_walking_section()
        self.draw_steady_section()
        self.draw_changes_section()
        self.draw_loadsave_section()


class BodynodesBakeAnimationOperator(bpy.types.Operator):
    """Bake the animation moving it from the bodynodes to the bones"""

    bl_idname = "bodynodes.bake_animation"
    bl_label = "Bake Animation Operator"
    bl_description = "Bake the animation moving it from the bodynodes to the bones"

    def execute(self, context):
        bake_animation()
        return {"FINISHED"}


class BodynodesSaveAnimationJSONOperator(bpy.types.Operator, ExportHelper):
    """Save bones animation as data in a json file"""

    bl_idname = "bodynodes.save_animation_json"
    bl_label = "Save Animation JSON Operator"
    bl_description = "Save bones animation as data in a json file"
    filepath = None

    # ExportHelper mixin class uses this
    filename_ext = ".json"

    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={"HIDDEN"},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        save_animation_json(self.filepath)
        return {"FINISHED"}


class BodynodesLoadFBXOperator(bpy.types.Operator, ImportHelper):
    """Load a .fbx file"""

    bl_idname = "bodynodes.load_fbx"
    bl_label = "Load FBX Operator"
    bl_description = "Load a .fbx file"
    filepath = None

    filter_glob: bpy.props.StringProperty(default="*.fbx", options={"HIDDEN"})

    def execute(self, context):
        load_fbx(self.filepath)
        return {"FINISHED"}


class BodynodesSaveAnimationFBXOperator(bpy.types.Operator, ExportHelper):
    """Save animation as a .fbx file. Useful to export to Unity (for example)"""

    bl_idname = "bodynodes.save_animation_fbx"
    bl_label = "Save Animation as FBX Operator"
    bl_description = (
        "Save animation as a .fbx file. Useful to export to Unity (for example)"
    )
    filepath = None

    # ExportHelper class uses this
    filename_ext = ".fbx"

    filter_glob: bpy.props.StringProperty(
        default="*.fbx",
        options={"HIDDEN"},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        save_animation_fbx(self.filepath)
        return {"FINISHED"}


class BodynodesSaveModelFBXOperator(bpy.types.Operator, ExportHelper):
    """Save model as a .fbx file. Useful to export to Unity (for example)"""

    bl_idname = "bodynodes.save_model_fbx"
    bl_label = "Save Model as FBX Operator"
    bl_description = (
        "Save model as a .fbx file. Useful to export to Unity (for example)"
    )
    filepath = None

    # ExportHelper class uses this
    filename_ext = ".fbx"

    filter_glob: bpy.props.StringProperty(
        default="*.fbx",
        options={"HIDDEN"},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        save_model_fbx(self.filepath)
        return {"FINISHED"}


class BodynodesLoadAnimationOperator(bpy.types.Operator, ImportHelper):
    """Load animation from a json file"""

    bl_idname = "bodynodes.load_animation"
    bl_label = "Load Animation Operator"
    bl_description = "Load animation from a json file"
    filepath = None

    filter_glob: bpy.props.StringProperty(default="*.json", options={"HIDDEN"})

    def execute(self, context):
        add_bodynodes_constr()
        load_animation(self.filepath)
        return {"FINISHED"}


class BodynodesCreateAnimationEditorMovesOperator(bpy.types.Operator):
    """Create the animation editor moves environment"""

    bl_idname = "bodynodes.create_animation_editor_moves"
    bl_label = "Create Animation Editor Moves Operator"
    bl_description = "Create the animation editor moves environment"

    def execute(self, context):
        create_animation_editor_moves()
        return {"FINISHED"}


class BodynodesUpdateAnimationEditorMovesOperator(bpy.types.Operator):
    """Update the animation editor moves environment"""

    bl_idname = "bodynodes.update_animation_editor_moves"
    bl_label = "Update Animation Editor Moves Operator"
    bl_description = "Update the animation editor moves environment"

    def execute(self, context):
        update_animation_editor_moves()
        return {"FINISHED"}


class BodynodesSaveAnimationEditorMovesOperator(bpy.types.Operator):
    """Save the animation of editor moves environment"""

    bl_idname = "bodynodes.save_animation_editor_moves"
    bl_label = "Save Animation Editor Moves Operator"
    bl_description = "Save the animation of editor moves environment"

    def execute(self, context):
        save_animation_editor_moves()
        return {"FINISHED"}


class BodynodesDestroyAnimationEditorMovesOperator(bpy.types.Operator):
    """Destroy animation editor moves environment"""

    bl_idname = "bodynodes.destroy_animation_editor_moves"
    bl_label = "Destroy Animation Editor Moves Operator"
    bl_description = "Destroy animation editor moves environment"

    def execute(self, context):
        destroy_animation_editor_moves()
        return {"FINISHED"}


class BodynodesApplyWalkAutoOperator(bpy.types.Operator):
    """Apply walk algorithm with automatic reference selection"""

    bl_idname = "bodynodes.apply_auto_walk"
    bl_label = "Apply Auto Walk Operator"
    bl_description = "Apply walk algorithm with automatic reference selection"

    def execute(self, context):
        apply_auto_walk()
        return {"FINISHED"}


class BodynodesApplyWalkRef2DOperator(bpy.types.Operator):
    """Apply walk 2D algorithm using as reference the selected bone"""

    bl_idname = "bodynodes.apply_ref_walk_2d"
    bl_label = "Apply Ref Walk 2D Operator"
    bl_description = "Apply walk 2D algorithm using as reference the selected bone"

    def execute(self, context):
        apply_ref_walk()
        return {"FINISHED"}


class BodynodesApplyWalkRef3DOperator(bpy.types.Operator):
    """Apply walk 3D algorithm using as reference the selected bone"""

    bl_idname = "bodynodes.apply_ref_walk_3d"
    bl_label = "Apply Ref Walk 3D Operator"
    bl_description = "Apply walk 3D algorithm using as reference the selected bone"

    def execute(self, context):
        apply_ref_walk(True)
        return {"FINISHED"}


class BodynodesApplySteadyFeetRefOperator(bpy.types.Operator):
    """Apply steady feet algorithm using as reference the selected foot"""

    bl_idname = "bodynodes.apply_steady_feet_ref"
    bl_label = "Apply Steady Feet Ref Operator"
    bl_description = "Apply steady feet algorithm using as reference the selected foot"

    def execute(self, context):
        apply_steady_feet_ref()
        return {"FINISHED"}


class BodynodesCreateSteadyHandorfootObjOperator(bpy.types.Operator):
    """Create steady object on the selected hand or foot bone"""

    bl_idname = "bodynodes.create_steady_handorfoot_obj"
    bl_label = "Create Steady Hand or Foot Object Operator"
    bl_description = "Create steady object on the selected hand or foot bone"

    def execute(self, context):
        create_steady_handorfoot_obj()
        return {"FINISHED"}


class BodynodesApplySteadyHandorfootRefOperator(bpy.types.Operator):
    """Apply steady algorithm on the selected hand or foot bone"""

    bl_idname = "bodynodes.apply_steady_handorfoot_ref"
    bl_label = "Apply Steady Hand or Foot Ref Operator"
    bl_description = "Apply steady algorithm on the selected hand or foot bone"

    def execute(self, context):
        apply_steady_handorfoot_ref()
        return {"FINISHED"}


class BodynodesRepeatMirrorOperator(bpy.types.Operator):
    """Repeat Mirror"""

    bl_idname = "bodynodes.repeat_mirror"
    bl_label = "Repeat Mirror Operator"
    bl_description = "Repeat Mirror"

    def execute(self, context):
        repeat_mirror()
        return {"FINISHED"}


class BodynodesStartDoneRotChangeAnimationOperator(bpy.types.Operator):
    """Apply rotation changes of bones to all animation frames"""

    bl_idname = "bodynodes.startdone_rot_change_animation"
    bl_label = "StartDone Change Animation Operator"
    bl_description = "Apply rotation changes of bones to all animation frames"

    def execute(self, context):
        if bodynodes_panel_anim["rot_change"]:
            done_rot_change_animation()
            bodynodes_panel_anim["rot_change"] = False
        else:
            start_rot_change_animation()
            bodynodes_panel_anim["rot_change"] = True
        return {"FINISHED"}


class BodynodesStartDoneLocChangeAnimationOperator(bpy.types.Operator):
    """Apply location changes of root bone to all animation frames"""

    bl_idname = "bodynodes.startdone_loc_change_animation"
    bl_label = "StartDone Loc Change Animation Operator"
    bl_description = "Apply location changes of root bone to all animation frames"

    def execute(self, context):
        if bodynodes_panel_anim["loc_change"]:
            done_loc_change_animation()
            bodynodes_panel_anim["loc_change"] = False
        else:
            start_loc_change_animation()
            bodynodes_panel_anim["loc_change"] = True
        return {"FINISHED"}


def register_animation():
    """Register the Bodynodes Animation panel"""

    find_players()
    bpy.utils.register_class(BodynodesLoadAnimationOperator)
    bpy.utils.register_class(BodynodesBakeAnimationOperator)
    bpy.utils.register_class(BodynodesCreateAnimationEditorMovesOperator)
    bpy.utils.register_class(BodynodesUpdateAnimationEditorMovesOperator)
    bpy.utils.register_class(BodynodesSaveAnimationEditorMovesOperator)
    bpy.utils.register_class(BodynodesDestroyAnimationEditorMovesOperator)
    bpy.utils.register_class(BodynodesApplyWalkAutoOperator)
    bpy.utils.register_class(BodynodesApplyWalkRef2DOperator)
    bpy.utils.register_class(BodynodesApplyWalkRef3DOperator)
    bpy.utils.register_class(BodynodesApplySteadyFeetRefOperator)
    bpy.utils.register_class(BodynodesCreateSteadyHandorfootObjOperator)
    bpy.utils.register_class(BodynodesApplySteadyHandorfootRefOperator)
    bpy.utils.register_class(BodynodesRepeatMirrorOperator)
    bpy.utils.register_class(BodynodesStartDoneRotChangeAnimationOperator)
    bpy.utils.register_class(BodynodesStartDoneLocChangeAnimationOperator)
    bpy.utils.register_class(BodynodesSaveAnimationJSONOperator)
    bpy.utils.register_class(BodynodesLoadFBXOperator)
    bpy.utils.register_class(BodynodesSaveAnimationFBXOperator)
    bpy.utils.register_class(BodynodesSaveModelFBXOperator)

    bpy.utils.register_class(PANEL_PT_BodynodesAnimation)


def unregister_animation():
    """Unregister the Bodynodes Animation panel"""

    bpy.utils.unregister_class(BodynodesLoadAnimationOperator)
    bpy.utils.unregister_class(BodynodesBakeAnimationOperator)
    bpy.utils.unregister_class(BodynodesCreateAnimationEditorMovesOperator)
    bpy.utils.unregister_class(BodynodesUpdateAnimationEditorMovesOperator)
    bpy.utils.unregister_class(BodynodesSaveAnimationEditorMovesOperator)
    bpy.utils.unregister_class(BodynodesDestroyAnimationEditorMovesOperator)
    bpy.utils.unregister_class(BodynodesApplyWalkAutoOperator)
    bpy.utils.unregister_class(BodynodesApplyWalkRef2DOperator)
    bpy.utils.unregister_class(BodynodesApplyWalkRef3DOperator)
    bpy.utils.unregister_class(BodynodesApplySteadyFeetRefOperator)
    bpy.utils.unregister_class(BodynodesCreateSteadyHandorfootObjOperator)
    bpy.utils.unregister_class(BodynodesApplySteadyHandorfootRefOperator)
    bpy.utils.unregister_class(BodynodesRepeatMirrorOperator)
    bpy.utils.unregister_class(BodynodesStartDoneRotChangeAnimationOperator)
    bpy.utils.unregister_class(BodynodesStartDoneLocChangeAnimationOperator)
    bpy.utils.unregister_class(BodynodesSaveAnimationJSONOperator)
    bpy.utils.unregister_class(BodynodesLoadFBXOperator)
    bpy.utils.unregister_class(BodynodesSaveAnimationFBXOperator)
    bpy.utils.unregister_class(BodynodesSaveModelFBXOperator)

    bpy.utils.unregister_class(PANEL_PT_BodynodesAnimation)


if __name__ == "__main__":
    print(
        "Meant to be called withing Blender from a main script using the functionalities in here"
    )
