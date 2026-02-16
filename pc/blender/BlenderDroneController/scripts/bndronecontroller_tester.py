#
# MIT License
#
# Copyright (c) 2024-2026 Manuel Bottini
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

"""Drone Controller Application"""

# The point of this script is to find out the relationships between orientations of
# different connected parts that make the position of an end point. Two body parts
# will be considered and the equations to find out the final position will be
# found

import glob
import os
import sys
import mathutils
import bpy

# The Tello drone creates an witi hotspot that the PC is expected to connect to and send commands as HTTP requests
# This means the that PC cannot connect to a generic Wifi.
# But the Bodynodes need a generic Wifi that supports Multicast...
# Which the Windows Hotspot does not supports
# Let's try to make the Bodynodes and the PC to the Drone hotspot, and let's hope that multicast is supported somehow
# Otherwise the only other way is to use BLE sensors

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
if "bnblenderconnect" in sys.modules:
    del sys.modules["bnblenderconnect"]
if "bnblenderaxis" in sys.modules:
    del sys.modules["bnblenderaxis"]

import bncommon  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
import bnblenderconnect  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
import bnblenderaxis  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
from bnblenderaxis import (  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
    BodynodesAxis,
)

bodynodes_panel_connect = {
    "drone": {"tracking": False, "status": "Disconnected", "operation": "None"}
}

droneposition_obj = {
    "name": "droneposition_obj",
    "location": [0, 0, 0],
    "prev_location": [0, 0, 0],
    "constrloc": [[10, 20], [-5, 5], [-5, 5]],
    "initial_relpos": [10, 0, 0],
}

DRONE_OPERATION_THR = 2
VIRTUAL_WORLD_OBJ = "virtual_world_env"

bodynodes_data = {
    "firstOrientationAbs": {},
    "startingBodypartQuat": {},
    "readOrientationAbs": {},
    "readGloveAngle": {},
    "readGloveTouch": {},
    "reset": 0,
}


bpy.types.Scene.drone_operation_text = bpy.props.StringProperty(
    name="Drone Operation Text",
    default="None",
    update=lambda self, context: (
        context.area.tag_redraw() if context.area else None
    ),  # Force UI redraw
)


def read_sensordata(data_json):
    """Read sensor data"""

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
    """Read orientations function"""

    bodypart_o = str(data_json["bodypart"]).replace("\x00", "")
    # print("read_orientations")
    # print(data_json)

    if bodypart_o not in BodynodesAxis.Config:
        print("Bodypart " + str(bodypart_o) + " not in bodynodes configuration")
        return

    bodynodes_data["readOrientationAbs"][bodypart_o] = [
        data_json["value"][0],
        data_json["value"][1],
        data_json["value"][2],
        data_json["value"][3],
    ]


bnmotiontrack = bncommon.BnMotionTracking_2Nodes(
    initialPosition=[0, 0, 0],
    armVector1=[10, 0, 0],
    armVector2=[10, 0, 0],
    locationConstraints=droneposition_obj["constrloc"],
)


def main_read_orientations():
    """Main read orientations function"""

    # That's where we move the objects
    # print(bodynodes_data["readOrientationAbs"])
    for bodypart in bodynodes_data["readOrientationAbs"]:

        if bodypart not in BodynodesAxis.Config:
            print("Bodypart = " + bodypart + " not in armature conf")
            continue

        if bodypart + "_obj" not in bpy.data.objects:
            print("Bodypart = " + bodypart + " does not have an _obj object")
            continue

        if bodypart not in bpy.data.objects:
            print("Bodypart = " + bodypart + " does not have an object")
            continue

        if bodynodes_data["readOrientationAbs"][bodypart] and bodypart != "katana":
            player_bodypart = bpy.data.objects[bodypart]

            if bodypart not in bodynodes_data["firstOrientationAbs"]:
                first_quat = None
                bodynodes_data["startingBodypartQuat"][bodypart] = mathutils.Quaternion(
                    (bpy.data.objects[bodypart].rotation_quaternion)
                )
            else:
                first_quat = bodynodes_data["firstOrientationAbs"][bodypart]

            starting_quat = bodynodes_data["startingBodypartQuat"][bodypart]
            rawquat = bodynodes_data["readOrientationAbs"][bodypart]
            bodynodes_axis_config = BodynodesAxis.Config[bodypart]

            env_quat = bpy.data.objects[VIRTUAL_WORLD_OBJ].rotation_quaternion

            [object_new_quat, first_quat] = bncommon.BnUtils.transform_sensor_quat(
                rawquat, first_quat, starting_quat, env_quat, bodynodes_axis_config
            )
            bodynodes_data["firstOrientationAbs"][bodypart] = first_quat

            player_bodypart.rotation_quaternion = object_new_quat

            bodynodes_data["readOrientationAbs"][bodypart] = None

    # Position Estimation via Sensor Orientation
    # droneposition_obj["location"] = bnmotiontrack.compute(
    #    bpy.data.objects["lowerarm_right"].rotation_quaternion,
    #    bpy.data.objects["upperarm_right"].rotation_quaternion
    # )

    # bpy.data.objects[droneposition_obj["name"]].location.x = droneposition_obj["location"][0]
    # bpy.data.objects[droneposition_obj["name"]].location.y = droneposition_obj["location"][1]
    # bpy.data.objects[droneposition_obj["name"]].location.z = droneposition_obj["location"][2]

    droneposition_obj["location"][0] = bpy.data.objects[
        "droneposition_obj"
    ].matrix_world.translation[0]
    droneposition_obj["location"][1] = bpy.data.objects[
        "droneposition_obj"
    ].matrix_world.translation[1]
    droneposition_obj["location"][2] = bpy.data.objects[
        "droneposition_obj"
    ].matrix_world.translation[2]

    return 0.02


def main_drone_function():
    """Main drone function"""

    # TO DO
    # Ping the drone and set the Status
    # If status is connected

    # Check location and prev_location to decide where we want to send the drone. Just process one displacement at a time and having
    # the prev_location set correctly (you need to test timings and how far each single operation moves the drone)

    # Let's get the biggest displacement
    abs_diffs = [
        abs(droneposition_obj["location"][0] - droneposition_obj["prev_location"][0]),
        abs(droneposition_obj["location"][1] - droneposition_obj["prev_location"][1]),
        abs(droneposition_obj["location"][2] - droneposition_obj["prev_location"][2]),
    ]

    # print(abs_diffs)

    if (
        abs_diffs[0] >= abs_diffs[1]
        and abs_diffs[0] >= abs_diffs[2]
        and abs_diffs[0] >= DRONE_OPERATION_THR
    ):
        # X axis, let's got Forwards or Backwards
        if droneposition_obj["location"][0] > droneposition_obj["prev_location"][0]:
            bodynodes_panel_connect["operation"] = "Forwards"
        else:
            bodynodes_panel_connect["operation"] = "Backwards"

        droneposition_obj["prev_location"][0] = droneposition_obj["location"][0]

    elif (
        abs_diffs[1] >= abs_diffs[0]
        and abs_diffs[1] >= abs_diffs[2]
        and abs_diffs[1] >= DRONE_OPERATION_THR
    ):
        # Y axis, let's got Left or Right
        if droneposition_obj["location"][1] > droneposition_obj["prev_location"][1]:
            bodynodes_panel_connect["operation"] = "Left"
        else:
            bodynodes_panel_connect["operation"] = "Right"

        droneposition_obj["prev_location"][1] = droneposition_obj["location"][1]

    elif (
        abs_diffs[2] >= abs_diffs[1]
        and abs_diffs[2] >= abs_diffs[0]
        and abs_diffs[2] >= DRONE_OPERATION_THR
    ):
        # Z axis, let's got Up or Down
        if droneposition_obj["location"][2] > droneposition_obj["prev_location"][2]:
            bodynodes_panel_connect["operation"] = "Up"
        else:
            bodynodes_panel_connect["operation"] = "Down"

        droneposition_obj["prev_location"][2] = droneposition_obj["location"][2]

    else:
        bodynodes_panel_connect["operation"] = "None"

    # Think about a rescaler slider to make operations bigger

    bpy.context.scene.drone_operation_text = str(bodynodes_panel_connect["operation"])

    return 1.0


def reset_objects():
    """Reset bodynodes objects is use"""

    bpy.data.objects["upperarm_right"].rotation_quaternion = mathutils.Quaternion(
        (0.707, 0, 0.707, 0)
    )
    bpy.data.objects["lowerarm_right"].rotation_quaternion = mathutils.Quaternion(
        (1, 0, 0, 0)
    )
    bodynodes_data["firstOrientationAbs"] = {}
    bodynodes_data["startingBodypartQuat"] = {}
    bodynodes_data["readOrientationAbs"] = {}


def drone_test():
    """Drone test function"""

    # Joystick / IMU failure -> add delays between commands
    # IMU failure -> do a calibration procedure
    # TO DO


def drone_tracking_toggle():
    """Drone tracking toggle"""

    # TO DO
    return


class PANEL_PT_BodynodesMain(
    bpy.types.Panel
):  # pylint: disable=invalid-name # reason: Blender naming convention
    """Main Application Panel"""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"
    bl_label = "Bodynodes Main"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator("bodynodes.close_main", text="Close")

        row = layout.row()
        row.operator("bodynodes.reset_objects", text="Reset")

        layout.label(text="-----")

        row = layout.row()
        row.scale_y = 0.5
        row.label(text=f"Location X:   {droneposition_obj["location"][0]:.5f}")
        row = layout.row()
        row.scale_y = 0.5
        row.label(text=f"Location Y:   {droneposition_obj["location"][1]:.5f}")
        row = layout.row()
        row.scale_y = 0.5
        row.label(text=f"Location Z:   {droneposition_obj["location"][2]:.5f}")

        row = layout.row()
        row.scale_y = 0.5
        row.label(
            text=f"Prev Location X:   {droneposition_obj["prev_location"][0]:.5f}"
        )
        row = layout.row()
        row.scale_y = 0.5
        row.label(
            text=f"Prev Location Y:   {droneposition_obj["prev_location"][1]:.5f}"
        )
        row = layout.row()
        row.scale_y = 0.5
        row.label(
            text=f"Prev Location Z:   {droneposition_obj["prev_location"][2]:.5f}"
        )


class PANEL_PT_BodynodesDroneController(
    bpy.types.Panel
):  # pylint: disable=invalid-name # reason: Blender naming convention
    """Drone Panel"""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"
    bl_label = "Bodynodes Drone Controller"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.scale_y = 1.0
        row.label(text="Connect to Drone Wifi")

        row = layout.row()
        row.scale_y = 1.0
        row.label(text="Drone:   " + bodynodes_panel_connect["drone"]["status"])

        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator("bodynodes.drone_test", text="Test")
        col1.enabled = True

        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator(
            "bodynodes.dronetrack_toggle",
            text="Stop" if bodynodes_panel_connect["drone"]["tracking"] else "Start",
        )
        col1.enabled = True

        layout.label(text="-----")

        row = layout.row()
        row.scale_y = 0.5
        row.label(text="Drone Operation:   " + context.scene.drone_operation_text)


class BodynodesResetObjectsOperator(bpy.types.Operator):
    """It resets position of the objects"""

    bl_idname = "bodynodes.reset_objects"
    bl_label = "Reset Objects Operator"
    bl_description = "It resets position of the objects"

    def execute(self, context):
        reset_objects()
        return {"FINISHED"}


class BodynodesDroneTestOperator(bpy.types.Operator):
    """Run a few tests for the drone"""

    bl_idname = "bodynodes.drone_test"
    bl_label = "Drone Test"
    bl_description = "Run a few tests for the drone"

    def execute(self, context):
        drone_test()
        return {"FINISHED"}


class BodynodesDroneTrackingOperator(bpy.types.Operator):
    """Toggles the tracking of the drone"""

    bl_idname = "bodynodes.dronetrack_toggle"
    bl_label = "Drone Tracking Toggle"
    bl_description = "Toggles the tracking of the drone"

    def execute(self, context):
        drone_tracking_toggle()
        return {"FINISHED"}


class BodynodesCloseMainOperator(bpy.types.Operator):
    """Close all the Bodynodes panels"""

    bl_idname = "bodynodes.close_main"
    bl_label = "Close Main Panel Operator"
    bl_description = "Close all the Bodynodes panels"

    def execute(self, context):
        unregister_all()
        return {"FINISHED"}


class BnConnectListener:
    """Blender Bodynodes Connect listener"""

    def read_sensordata_callback(self, data_json):
        """Read sensor data callback"""

        read_sensordata(data_json)

    def reinit_bn_data(self):
        """Reinitilize Bodynodes data"""

        reset_objects()


connect_listener = BnConnectListener()


def unregister_all():
    """Unregister Application panels"""

    bpy.utils.unregister_class(BodynodesResetObjectsOperator)
    bpy.utils.unregister_class(BodynodesDroneTestOperator)
    bpy.utils.unregister_class(BodynodesCloseMainOperator)
    bpy.utils.unregister_class(PANEL_PT_BodynodesMain)

    bpy.utils.unregister_class(BodynodesDroneTrackingOperator)
    bpy.utils.unregister_class(PANEL_PT_BodynodesDroneController)

    bpy.app.timers.unregister(main_read_orientations)
    bpy.app.timers.unregister(main_drone_function)

    bnblenderconnect.unregister_connect()
    bnblenderaxis.unregister_axis()


def register_all():
    """Register Application panels"""

    bpy.utils.register_class(BodynodesResetObjectsOperator)
    bpy.utils.register_class(BodynodesDroneTestOperator)
    bpy.utils.register_class(BodynodesCloseMainOperator)
    bpy.utils.register_class(PANEL_PT_BodynodesMain)

    bpy.utils.register_class(BodynodesDroneTrackingOperator)
    bpy.utils.register_class(PANEL_PT_BodynodesDroneController)

    bpy.app.timers.register(main_read_orientations)
    bpy.app.timers.register(main_drone_function)

    bnblenderconnect.register_connect(connect_listener)
    bnblenderaxis.register_axis()

    bnblenderaxis.load_axis_config_default(os.path.realpath(__file__))


if __name__ == "__main__":
    register_all()
