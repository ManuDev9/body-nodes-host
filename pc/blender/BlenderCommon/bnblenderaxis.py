#
# MIT License
#
# Copyright (c) 2025-2026 Manuel Bottini
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

"""Bodynodes Axis Blender module"""

import json
import os
import sys
from dataclasses import dataclass
import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper

if "bnblenderutils" in sys.modules:
    del sys.modules["bnblenderutils"]

import bnblenderutils  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting


@dataclass
class BodynodesAxis:
    """Bodynodes Axis data"""

    Config = {}
    Basic = {
        "new_w_sign": 1,
        "new_x_sign": 1,
        "new_y_sign": 1,
        "new_z_sign": 1,
        "new_w_val": 0,
        "new_x_val": 1,
        "new_y_val": 2,
        "new_z_val": 3,
    }


def load_axis_config(filepath):
    """Load axis configuration from a file"""

    with open(filepath, encoding="utf-8") as file:
        BodynodesAxis.Config = json.load(file)


def load_axis_config_default(fullpath):
    """Load axis configuration from a default file"""

    dir_path = os.path.dirname(fullpath)
    dir_path = dir_path.split("\\")[:-1]
    dir_path = "\\".join(dir_path)
    conf_file = dir_path + "\\configs\\bodynodes_axis_config_esp12e.json"
    if os.path.isfile(conf_file):
        load_axis_config(conf_file)
    else:
        print("Default config file does not exist: " + conf_file)


def save_axis_config(filepath):
    """Save axis configuration in a file"""

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(json.dumps(BodynodesAxis.Config, indent=4, sort_keys=True))


list_axis = [
    ("0", "W", ""),
    ("1", "X", ""),
    ("2", "Y", ""),
    ("3", "Z", ""),
    ("4", "-W", ""),
    ("5", "-X", ""),
    ("6", "-Y", ""),
    ("7", "-Z", ""),
]


class PANEL_PT_BodynodesAxis(
    bpy.types.Panel
):  # pylint: disable=invalid-name # reason: Blender naming convention
    """Bodynodes Axis Panel"""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"
    bl_label = "Bodynodes Axis"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator("bodynodes.load_axis_config", text="Load Axis Config")
        row.enabled = True

        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.label(text="Axis Config:")
        col1.ui_units_x = 15
        col2 = row.column()
        col2.operator("bodynodes.change_axis_config", text="Change")
        col2.enabled = True
        col3 = row.column()
        col3.operator("bodynodes.save_axis_config", text="Save")
        col3.enabled = True

        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        if "_id" in BodynodesAxis.Config:
            col1.label(text="Name: " + BodynodesAxis.Config["_id"])
        else:
            col1.label(text="No Axis loaded")


class BodynodesChangeAxisConfigMenu(bpy.types.Operator):
    """Change the axis configuration, bodypart, Bodynodes sensor"""

    bl_idname = "bodynodes.change_axis_config"
    bl_label = "Change Axis Config"
    bl_description = "Change the axis configuration, bodypart, Bodynodes sensor"
    bl_options = {"REGISTER", "UNDO"}

    bodypart_to_change: bpy.props.EnumProperty(
        items=[
            ("none", "none", ""),
            ("head", "head", ""),
            ("lowerarm_right", "lowerarm_right", ""),
            ("lowerarm_left", "lowerarm_left", ""),
            ("upperleg_left", "upperleg_left", ""),
            ("lowerleg_right", "lowerleg_right", ""),
            ("lowerleg_left", "lowerleg_left", ""),
            ("upperleg_right", "upperleg_right", ""),
            ("upperarm_right", "upperarm_right", ""),
            ("upperarm_left", "upperarm_left", ""),
            ("lowerbody", "lowerbody", ""),
            ("upperbody", "upperbody", ""),
            ("katana", "katana", ""),
        ],
        name="Bodypart",
    )

    bones_items = ()

    bones_items = bones_items + (("none", "none", ""),)
    for bone in bnblenderutils.bodynode_bones_init:
        bones_items = bones_items + ((bone, bone, ""),)

    new_bone_name: bpy.props.EnumProperty(items=bones_items, name="Bone Name")

    new_w_axis: bpy.props.EnumProperty(items=list_axis, name="Axis W")

    new_x_axis: bpy.props.EnumProperty(items=list_axis, name="Axis X")

    new_y_axis: bpy.props.EnumProperty(items=list_axis, name="Axis Y")

    new_z_axis: bpy.props.EnumProperty(items=list_axis, name="Axis Z")

    def execute(self, context):

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
            BodynodesAxis.Config[bodypart_to_change]["new_w_sign"] = -1
            new_w_axis -= 4
        else:
            BodynodesAxis.Config[bodypart_to_change]["new_w_sign"] = 1

        if new_x_axis > 3:
            BodynodesAxis.Config[bodypart_to_change]["new_x_sign"] = -1
            new_x_axis -= 4
        else:
            BodynodesAxis.Config[bodypart_to_change]["new_x_sign"] = 1

        if new_y_axis > 3:
            BodynodesAxis.Config[bodypart_to_change]["new_y_sign"] = -1
            new_y_axis -= 4
        else:
            BodynodesAxis.Config[bodypart_to_change]["new_y_sign"] = 1

        if new_z_axis > 3:
            BodynodesAxis.Config[bodypart_to_change]["new_z_sign"] = -1
            new_z_axis -= 4
        else:
            BodynodesAxis.Config[bodypart_to_change]["new_z_sign"] = 1

        BodynodesAxis.Config[bodypart_to_change]["new_w_val"] = new_w_axis
        BodynodesAxis.Config[bodypart_to_change]["new_x_val"] = new_x_axis
        BodynodesAxis.Config[bodypart_to_change]["new_y_val"] = new_y_axis
        BodynodesAxis.Config[bodypart_to_change]["new_z_val"] = new_z_axis
        BodynodesAxis.Config[bodypart_to_change]["bone_name"] = new_bone_name

        return {"FINISHED"}


class BodynodesSaveAxisConfigOperator(bpy.types.Operator, ExportHelper):
    """Save Axis configuration in a json file"""

    bl_idname = "bodynodes.save_axis_config"
    bl_label = "Save Axis Config Operator"
    bl_description = "Save the axis configuration in a json file"
    filepath = None

    # ExportHelper mixin class uses this
    filename_ext = ".json"

    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={"HIDDEN"},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        save_axis_config(self.filepath)
        return {"FINISHED"}


class BodynodesLoadAxisConfigOperator(bpy.types.Operator, ImportHelper):
    """Load Axis configuration from a json file"""

    bl_idname = "bodynodes.load_axis_config"
    bl_label = "Load Axis Configuration Operator"
    bl_description = "Load Axis configuration from a json file"
    filepath = None

    filter_glob: bpy.props.StringProperty(default="*.json", options={"HIDDEN"})

    def execute(self, context):
        load_axis_config(self.filepath)
        return {"FINISHED"}


def register_axis():
    """Register the Bodynodes Axis panel"""

    bpy.utils.register_class(BodynodesChangeAxisConfigMenu)
    bpy.utils.register_class(BodynodesSaveAxisConfigOperator)
    bpy.utils.register_class(BodynodesLoadAxisConfigOperator)

    bpy.utils.register_class(PANEL_PT_BodynodesAxis)


def unregister_axis():
    """Unregister the Bodynodes Axis panel"""

    bpy.utils.unregister_class(BodynodesChangeAxisConfigMenu)
    bpy.utils.unregister_class(BodynodesSaveAxisConfigOperator)
    bpy.utils.unregister_class(BodynodesLoadAxisConfigOperator)

    bpy.utils.unregister_class(PANEL_PT_BodynodesAxis)


if __name__ == "__main__":
    print(
        "Meant to be called withing Blender from a main script using the functionalities in here"
    )
