#
# MIT License
#
# Copyright (c) 2024-2025 Manuel Bottini
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

"""Exploration between position and orientation with Bodynodes data"""

# The point of this script is to find out the relationships between orientations of
# different connected parts that make the position of an end point. Two body parts
# will be considered and the equations to find out the final position will be
# found

import glob
import os
import sys
import math
import mathutils
import bpy

bodynodes_axis_config = {
    "new_w_sign": 1,
    "new_x_sign": 1,
    "new_y_sign": -1,
    "new_z_sign": 1,
    "new_w_val": 0,
    "new_x_val": 2,
    "new_y_val": 1,
    "new_z_val": 3,
}


bodynodes_axis_config_alt = {
    "new_w_sign": -1,
    "new_x_sign": 1,
    "new_y_sign": -1,
    "new_z_sign": -1,
    "new_w_val": 1,
    "new_x_val": 3,
    "new_y_val": 0,
    "new_z_val": 2,
}

dir_path = os.path.dirname(os.path.realpath(__file__))

print(dir_path)

BN_COMMON_PATH = "/../../../../../body-nodes-common/python"
BLENDER_COMMON_PATH = "/../../../BlenderCommon"
PYTHONLIB_WIFI_PATH = "/../../../../../modules/pythonlib"

# Removing the scripts saved in cache so that Blender uses the last updated version of the scritps
for file in glob.glob(
    os.path.join(
        os.path.abspath(__file__ + "/../../scripts/__pycache__"),
        "bndronecontroller_tester.cpython*.pyc",
    )
):
    os.remove(file)

for file in glob.glob(
    os.path.join(
        os.path.abspath(BN_COMMON_PATH + "/__pycache__"), "bncommon.cpython*.pyc"
    )
):
    os.remove(file)

for file in glob.glob(
    os.path.join(
        os.path.abspath(BLENDER_COMMON_PATH + "/__pycache__"),
        "bnblenderutils.cpython*.pyc",
    )
):
    os.remove(file)

for file in glob.glob(
    os.path.join(
        os.path.abspath(__file__ + "/../../../common/__pycache__"),
        "bnblenderconnect.cpython*.pyc",
    )
):
    os.remove(file)

for file in glob.glob(
    os.path.join(
        os.path.abspath(__file__ + "/../../../common/__pycache__"),
        "bnblenderaxis.cpython*.pyc",
    )
):
    os.remove(file)

sys.path.append(os.path.abspath(__file__) + BN_COMMON_PATH)
sys.path.append(os.path.abspath(__file__) + BLENDER_COMMON_PATH)
sys.path.append(os.path.abspath(__file__) + PYTHONLIB_WIFI_PATH)

if "bncommon" in sys.modules:
    del sys.modules["bncommon"]
if "bnblenderutils" in sys.modules:
    del sys.modules["bnblenderutils"]
if "bnwifibodynodeshost" in sys.modules:
    del sys.modules["bnwifibodynodeshost"]

import bncommon  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
import bnwifibodynodeshost  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting

bodynodes_panel_connect = {
    "server": {
        "running": False,
        "status": "Start server",
    }
}

bodynodes_data = {
    "offsetOrientationAbs": {},
    "readOrientationAbs": {},
    "readGloveAngle": {},
    "readGloveTouch": {},
    "reset": 0,
}

position1_obj = {
    "name": "position1_obj",
    "location": [0, 0, 0],
    "initial_relpos": [10, 0, 0],
}

position2_obj = {
    "name": "position2_obj",
    "location": [0, 0, 0],
    "constrloc": [[10, 20], [-5, 5], [-5, 5]],
    "clocation": [0, 0, 0],
    "initial_relpos": [10, 0, 0],
}

VIRTUAL_WORLD_OBJ1 = "virtual_world_axis1"
VIRTUAL_WORLD_OBJ2 = "virtual_world_axis2"
VIRTUAL_WORLD_OBJ3 = "virtual_world_axis3"

robotarm1_obj = {"name": "robotarm1_obj", "rotation": [0, 0, 0], "crotation": [0, 0, 0]}

robotarm2_obj = {"name": "robotarm2_obj", "rotation": [0, 0, 0], "crotation": [0, 0, 0]}

crobotarm1_obj = {"name": "crobotarm1_obj"}

crobotarm2_obj = {"name": "crobotarm2_obj"}


def read_sensordata(data_json):
    """Read sensor data function"""

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
    # elif data_json["sensortype"] == "glove":
    #    read_glove(data_json)
    elif data_json["sensortype"] == "acceleration_abs":
        print("Acceleration data is not yet used")


def read_orientations(data_json):
    """Read orientation function"""

    bodypart_o = data_json["bodypart"]
    # print("read_orientations")
    # print(data_json)

    if data_json["value"] == "reset":
        bodynodes_data["reset"] = 1
    else:
        bodynodes_data["readOrientationAbs"][bodypart_o] = (
            bncommon.BnUtils.create_quanternion(
                bodynodes_axis_config, data_json["value"]
            )
        )


class BlenderBodynodeListener(bnwifibodynodeshost.BodynodeListener):
    """Bodynodes listener"""

    def __init__(self):
        print("This is the Blender listener")

    def on_message_received(self, player, bodypart, sensortype, value):
        """Message received callback"""

        data_json = {
            "player": player,
            "bodypart": bodypart,
            "sensortype": sensortype,
            "value": value,
        }
        read_sensordata(data_json)

    def is_of_interest(self, player, bodypart, sensortype):
        """Indicate parameters of interest"""

        # Everything is of interest
        return True


blenderbnlistener = BlenderBodynodeListener()
bnhost = bnwifibodynodeshost.BnWifiHostCommunicator()

bnmotiontrack = bncommon.BnMotionTracking_2Nodes(
    initialPosition=[0, 0, 0],
    armVector1=[10, 0, 0],
    armVector2=[10, 0, 0],
    locationConstraints=position2_obj["constrloc"],
)

bnaik = bncommon.BnRobotIK_ArmZYY(lengthRA1=0, lengthRA2=10, lengthRA3=10)


def main_read_orientations():
    """Main read orientations function"""

    # That's where we move the objects

    env_orientation = bpy.data.objects[
        VIRTUAL_WORLD_OBJ1
    ].rotation_quaternion  # @ Quaternion((0 ,0,-0.707107,-0.707107))
    for bodypart in bodynodes_data["readOrientationAbs"]:
        if bodynodes_data["readOrientationAbs"][bodypart] is not None:
            if bodypart not in bpy.data.objects:
                print("Bodypart " + bodypart + " not found in Blender")
                continue

            bodypart_obj_rot = bpy.data.objects[bodypart].rotation_quaternion
            if bodypart not in bodynodes_data["offsetOrientationAbs"]:
                bodynodes_data["offsetOrientationAbs"][bodypart] = (
                    bodynodes_data["readOrientationAbs"][bodypart].inverted()
                    @ bodypart_obj_rot
                )

            # Recompute only with what is changing, instead of everything every time
            target_ori = (
                bodynodes_data["readOrientationAbs"][bodypart]
                @ bodynodes_data["offsetOrientationAbs"][bodypart]
                @ env_orientation
            )
            bpy.data.objects[bodypart].rotation_quaternion = target_ori

            bodynodes_data["readOrientationAbs"][bodypart] = None

    # Position Estimation via Sensor Orientation
    loc1_vector = bpy.data.objects[
        position1_obj["name"]
    ].matrix_world.translation  # location
    loc2_vector = bpy.data.objects[
        position2_obj["name"]
    ].matrix_world.translation  # location
    position1_obj["location"] = [loc1_vector[0], loc1_vector[1], loc1_vector[2]]
    position2_obj["location"] = [loc2_vector[0], loc2_vector[1], loc2_vector[2]]

    position2_obj["clocation"] = bnmotiontrack.compute(
        bpy.data.objects["lowerarm_right"].rotation_quaternion,
        bpy.data.objects["upperarm_right"].rotation_quaternion,
    )

    # Robotic Arm Parts Rotations Estimation via Position with IK
    angles1_vector = bpy.data.objects[robotarm1_obj["name"]].matrix_world.to_euler(
        "XYZ"
    )
    angles2_vector = bpy.data.objects[robotarm2_obj["name"]].matrix_world.to_euler(
        "XYZ"
    )

    robotarm1_obj["rotation"] = [
        angles1_vector[0],
        angles1_vector[1],
        angles1_vector[2],
    ]
    robotarm2_obj["rotation"] = [
        angles2_vector[0],
        angles2_vector[1],
        angles2_vector[2],
    ]

    robotarm1_obj["rotation"] = [math.degrees(x) for x in robotarm1_obj["rotation"]]
    robotarm2_obj["rotation"] = [math.degrees(x) for x in robotarm2_obj["rotation"]]

    # tmp = bpy.data.objects["positionIK_obj"].location  # location
    # endpoint_vector = [tmp[0] + 20, tmp[1], tmp[2]]

    # aik_angles = bnaik.compute( endpoint_vector )
    # It might crash, make use of the proper try-catch
    aik_angles = bnaik.compute(position2_obj["clocation"])

    bpy.data.objects[crobotarm1_obj["name"]].rotation_euler.z = aik_angles[0]
    bpy.data.objects[crobotarm1_obj["name"]].rotation_euler.y = aik_angles[1]
    bpy.data.objects[crobotarm2_obj["name"]].rotation_euler.y = aik_angles[2]

    return 0.02


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


def reset_objects():
    """Reset objects"""

    bpy.data.objects["upperarm_right"].rotation_quaternion = mathutils.Quaternion(
        (1, 0, 0, 0)
    )
    bpy.data.objects["lowerarm_right"].rotation_quaternion = mathutils.Quaternion(
        (1, 0, 0, 0)
    )
    bodynodes_data["offsetOrientationAbs"] = {}
    bodynodes_data["readOrientationAbs"] = {}


def update_w_axis(
    self, context
):  # pylint: disable=unused-argument # reason: Blender callback
    """Update W axis"""

    new_axis = int(self.new_w_axis)
    if new_axis > 3:
        bodynodes_axis_config["new_w_sign"] = -1
        new_axis -= 4
    else:
        bodynodes_axis_config["new_w_sign"] = 1

    bodynodes_axis_config["new_w_val"] = new_axis
    reset_objects()


def update_x_axis(
    self, context
):  # pylint: disable=unused-argument # reason: Blender callback
    """Update X axis"""

    new_axis = int(self.new_x_axis)
    if new_axis > 3:
        bodynodes_axis_config["new_x_sign"] = -1
        new_axis -= 4
    else:
        bodynodes_axis_config["new_x_sign"] = 1

    bodynodes_axis_config["new_x_val"] = new_axis
    reset_objects()


def update_y_axis(
    self, context
):  # pylint: disable=unused-argument # reason: Blender callback
    """Update Y axis"""

    new_axis = int(self.new_y_axis)
    if new_axis > 3:
        bodynodes_axis_config["new_y_sign"] = -1
        new_axis -= 4
    else:
        bodynodes_axis_config["new_y_sign"] = 1

    bodynodes_axis_config["new_y_val"] = new_axis
    reset_objects()


def update_z_axis(
    self, context
):  # pylint: disable=unused-argument # reason: Blender callback
    """Update Z axis"""

    new_axis = int(self.new_z_axis)
    if new_axis > 3:
        bodynodes_axis_config["new_z_sign"] = -1
        new_axis -= 4
    else:
        bodynodes_axis_config["new_z_sign"] = 1

    bodynodes_axis_config["new_z_val"] = new_axis
    reset_objects()


def start_server():
    """Start Wifi host"""

    # print("start_server")
    if bnhost.is_running():
        print("BnHost is already there...")
        return

    # bnblenderutils.reinit_bn_data()
    bnhost.start(["BN"])
    bnhost.add_listener(blenderbnlistener)

    bodynodes_panel_connect["server"]["status"] = "Server running"
    bodynodes_panel_connect["server"]["running"] = True


def stop_server():
    """Stop Wifi host"""

    print("stop_server")
    if not bnhost.is_running():
        print("BnHost wass already stopped...")
        return

    bnhost.remove_listener(blenderbnlistener)
    bnhost.stop()

    bodynodes_panel_connect["server"]["status"] = "Server not running"
    bodynodes_panel_connect["server"]["running"] = False


class PANEL_PT_BodynodesMain(
    bpy.types.Panel
):  # pylint: disable=invalid-name # reason: Blender naming convention
    """Main Application panel"""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"
    bl_label = "Bodynodes Main"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Server:   " + bodynodes_panel_connect["server"]["status"])

        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator(
            "bodynodes.startstop_server",
            text="Stop" if bodynodes_panel_connect["server"]["running"] else "Start",
        )
        col1.enabled = True

        row = layout.row()
        row.operator("bodynodes.axis_config", text="Axis Config")

        row = layout.row()
        row.scale_y = 0.5
        row.label(text=f"Position2 X:   {position2_obj["location"][0]:.5f}")
        row = layout.row()
        row.scale_y = 0.5
        row.label(text=f"Position2 Y:   {position2_obj["location"][1]:.5f}")
        row = layout.row()
        row.scale_y = 0.5
        row.label(text=f"Position2 Z:   {position2_obj["location"][2]:.5f}")

        row = layout.row()
        row.scale_y = 0.5
        row.label(text=f"CPosition2 X:   {position2_obj["clocation"][0]:.5f}")
        row = layout.row()
        row.scale_y = 0.5
        row.label(text=f"CPosition2 Y:   {position2_obj["clocation"][1]:.5f}")
        row = layout.row()
        row.scale_y = 0.5
        row.label(text=f"CPosition2 Z:   {position2_obj["clocation"][2]:.5f}")

        layout.label(text="-----")

        row = layout.row()
        row.operator("bodynodes.close_main", text="Close")


class BodynodesStartStopServerOperator(bpy.types.Operator):
    """Starts/Stop the local server"""

    bl_idname = "bodynodes.startstop_server"
    bl_label = "StartStop Server Operator"
    bl_description = (
        "Starts/Stop the local server. It resets position of the sensors at every start"
    )

    def execute(self, context):
        if bodynodes_panel_connect["server"]["running"]:
            stop_server()
        else:
            bpy.app.timers.register(start_server, first_interval=4.0)

        return {"FINISHED"}


class BodynodesAxisConfigOperator(bpy.types.Operator):
    """Helper to configure the Axis system"""

    bl_idname = "bodynodes.axis_config"
    bl_label = "Bodynodes Axis Configuration"
    bl_description = "Helper to configure the Axis system"

    new_w_axis: bpy.props.EnumProperty(
        items=list_axis, name="Axis W", update=update_w_axis
    )

    new_x_axis: bpy.props.EnumProperty(
        items=list_axis, name="Axis X", update=update_x_axis
    )

    new_y_axis: bpy.props.EnumProperty(
        items=list_axis, name="Axis Y", update=update_y_axis
    )

    new_z_axis: bpy.props.EnumProperty(
        items=list_axis, name="Axis Z", update=update_z_axis
    )

    def invoke(self, context, event):
        new_w_axis_default = bodynodes_axis_config["new_w_val"]
        if bodynodes_axis_config["new_w_sign"] < 0:
            new_w_axis_default = new_w_axis_default + 4
        new_x_axis_default = bodynodes_axis_config["new_x_val"]
        if bodynodes_axis_config["new_x_sign"] < 0:
            new_x_axis_default = new_x_axis_default + 4
        new_y_axis_default = bodynodes_axis_config["new_y_val"]
        if bodynodes_axis_config["new_y_sign"] < 0:
            new_y_axis_default = new_y_axis_default + 4
        new_z_axis_default = bodynodes_axis_config["new_z_val"]
        if bodynodes_axis_config["new_z_sign"] < 0:
            new_z_axis_default = new_z_axis_default + 4

        self.new_w_axis = str(new_w_axis_default)
        self.new_x_axis = str(new_x_axis_default)
        self.new_y_axis = str(new_y_axis_default)
        self.new_z_axis = str(new_z_axis_default)
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        # self.report({'INFO'}, f"Selected: {self.menu_items}")
        print(bodynodes_axis_config)
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        # Dropdown menu in the popup
        layout.label(
            text="Double check configs, stay away from PC and monitors, calibrate"
        )
        layout.prop(self, "new_w_axis")
        layout.prop(self, "new_x_axis")
        layout.prop(self, "new_y_axis")
        layout.prop(self, "new_z_axis")


class BodynodesCloseMainOperator(bpy.types.Operator):
    """Close all the Bodynodes panels"""

    bl_idname = "bodynodes.close_main"
    bl_label = "Close Main Panel Operator"
    bl_description = "Close all the Bodynodes panels"

    def execute(self, context):
        unregister_all()
        return {"FINISHED"}


def unregister_all():
    """Unregister application panel"""

    stop_server()
    bpy.utils.unregister_class(BodynodesStartStopServerOperator)
    bpy.utils.unregister_class(BodynodesAxisConfigOperator)
    bpy.utils.unregister_class(BodynodesCloseMainOperator)
    bpy.utils.unregister_class(PANEL_PT_BodynodesMain)
    bpy.app.timers.unregister(main_read_orientations)


def register_all():
    """Register application panel"""

    bpy.utils.register_class(BodynodesStartStopServerOperator)
    bpy.utils.register_class(BodynodesAxisConfigOperator)
    bpy.utils.register_class(BodynodesCloseMainOperator)
    bpy.utils.register_class(PANEL_PT_BodynodesMain)
    bpy.app.timers.register(main_read_orientations)


if __name__ == "__main__":
    register_all()
