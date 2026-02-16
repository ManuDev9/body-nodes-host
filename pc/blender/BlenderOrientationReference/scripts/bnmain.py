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

"""Blender Bodynodes Orientation Reference Application"""

import glob
import os
import sys
from dataclasses import dataclass
import bpy
import mathutils

dir_path = os.path.dirname(os.path.realpath(__file__))

# Removing the scripts saved in cache so that Blender uses the last updated version of the scritps
for file in glob.glob(
    os.path.join(
        os.path.abspath(__file__ + "/../../scripts/__pycache__"),
        "bnmain.cpython*.pyc",
    )
):
    os.remove(file)

for file in glob.glob(
    os.path.join(
        os.path.abspath(__file__ + "/../../../../modules/pythonlib/__pycache__"),
        "bnwifibodynodeshost.cpython*.pyc",
    )
):
    os.remove(file)

for file in glob.glob(
    os.path.join(
        os.path.abspath(__file__ + "/../../../../modules/pythonlib/__pycache__"),
        "bnblebodynodeshost.cpython*.pyc",
    )
):
    os.remove(file)

sys.path.append(os.path.abspath(__file__) + "/../../scripts")
sys.path.append(os.path.abspath(__file__) + "/../../../BlenderCommon")
sys.path.append(os.path.abspath(__file__) + "/../../../../../modules/pythonlib")
sys.path.append(os.path.abspath(__file__) + "/../../../../../body-nodes-common/python")

if "bncommon" in sys.modules:
    del sys.modules["bncommon"]
if "bnblebodynodeshost" in sys.modules:
    del sys.modules["bnblebodynodeshost"]
if "bnwifibodynodeshost" in sys.modules:
    del sys.modules["bnwifibodynodeshost"]

import bncommon  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
import bnblebodynodeshost  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
import bnwifibodynodeshost  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting

bodynodes_panel_connect = {
    "server": {"running": False, "status": "Start server"},
    "ble": {"running": False, "status": "Start BLE"},
}

bodynodes_axis_config_esp12e = {
    "new_w_sign": 1,
    "new_x_sign": -1,
    "new_y_sign": -1,
    "new_z_sign": 1,
    "new_w_val": 0,
    "new_x_val": 1,
    "new_y_val": 2,
    "new_z_val": 3,
}


bodynodes_axis_config = bodynodes_axis_config_esp12e


@dataclass
class Internal:
    """Internal module data dataclass"""

    starting_quat = None
    first_quat = None
    katana_rawquat = None


internal = Internal()


class BLEBlenderBodynodeListener(bnblebodynodeshost.BodynodeListener):
    """BLE Host listerer"""

    def __init__(self):
        print("This is the BLE Blender listener")

    def on_message_received(self, player, bodypart, sensortype, value):
        """Message received callback"""

        # data_json = {
        #    "player": player,
        #    "bodypart": bodypart,
        #    "sensortype": sensortype,
        #    "value": value,
        # }
        internal.katana_rawquat = [1, 0, 0, 0]
        internal.katana_rawquat[0] = value[0]
        internal.katana_rawquat[1] = value[1]
        internal.katana_rawquat[2] = value[2]
        internal.katana_rawquat[3] = value[3]
        # print(data_json)

    def is_of_interest(self, player, bodypart, sensortype):
        """Indicate parameters fo interest"""

        if bodypart in bpy.data.objects and sensortype == "orientation_abs":
            return True
        return False


class WifiBlenderBodynodeListener(bnwifibodynodeshost.BodynodeListener):
    """Wifi Host listerer"""

    def __init__(self):
        print("This is the Wifi Blender listener")

    def on_message_received(self, player, bodypart, sensortype, value):
        """Message received callback"""

        # data_json = {
        #    "player": player,
        #    "bodypart": bodypart,
        #    "sensortype": sensortype,
        #    "value": value,
        # }
        internal.katana_rawquat = [1, 0, 0, 0]
        internal.katana_rawquat[0] = value[0]
        internal.katana_rawquat[1] = value[1]
        internal.katana_rawquat[2] = value[2]
        internal.katana_rawquat[3] = value[3]
        # print(data_json)

    def is_of_interest(self, player, bodypart, sensortype):
        """Indicate parameters fo interest"""

        if bodypart in bpy.data.objects and sensortype == "orientation_abs":
            return True
        return False


bleblenderbnlistener = BLEBlenderBodynodeListener()
bnblehost = bnblebodynodeshost.BnBLEHostCommunicator()

wifiblenderbnlistener = WifiBlenderBodynodeListener()
bnwifihost = bnwifibodynodeshost.BnWifiHostCommunicator()


def main_read_orientations():
    """Main read orientation function"""

    # print(internal.katana_rawquat)
    if internal.starting_quat is None:
        print("No internal.starting_quat somehow, have you pressed start_server")
        return 1.00

    if internal.katana_rawquat is not None:

        env_quat = bpy.data.objects["katana_env"].rotation_quaternion

        [object_new_quat, internal.first_quat] = bncommon.BnUtils.transform_sensor_quat(
            internal.katana_rawquat,
            internal.first_quat,
            internal.starting_quat,
            env_quat,
            bodynodes_axis_config,
        )

        bpy.data.objects["katana"].rotation_quaternion = object_new_quat

        internal.katana_rawquat = None

    return 0.02


def reset_objs():
    """Reset objects"""

    internal.starting_quat = mathutils.Quaternion(
        [
            bpy.data.objects["katana"].rotation_quaternion[0],
            bpy.data.objects["katana"].rotation_quaternion[1],
            bpy.data.objects["katana"].rotation_quaternion[2],
            bpy.data.objects["katana"].rotation_quaternion[3],
        ]
    )
    internal.first_quat = None


def start_server():
    """Start WIFI"""

    print("start_server")
    if bnwifihost.is_running():
        print("Wifi BnHost is already there...")
        bodynodes_panel_connect["server"]["status"] = "Server running"
        bodynodes_panel_connect["server"]["running"] = True
        return

    reset_objs()

    # bnblenderutils.reinit_bn_data()
    bnwifihost.start(["BN"])
    bnwifihost.add_listener(wifiblenderbnlistener)

    bodynodes_panel_connect["server"]["status"] = "Server running"
    bodynodes_panel_connect["server"]["running"] = True


def stop_server():
    """Stop WIFI"""

    print("stop_server")
    if not bnwifihost.is_running():
        print("Wifi BnHost was already stopped...")
        bodynodes_panel_connect["server"]["status"] = "Server not running"
        bodynodes_panel_connect["server"]["running"] = False
        return

    bnwifihost.remove_listener(wifiblenderbnlistener)
    bnwifihost.stop()

    bpy.data.objects["katana"].rotation_quaternion = internal.starting_quat
    internal.starting_quat = None
    bodynodes_panel_connect["server"]["status"] = "Server not running"
    bodynodes_panel_connect["server"]["running"] = False


def start_ble():
    """Start BLE"""

    print("start_ble")
    if bnblehost.is_running():
        print("BLE BnHost is already there...")
        bodynodes_panel_connect["ble"]["status"] = "BLE running"
        bodynodes_panel_connect["ble"]["running"] = True
        return

    reset_objs()

    bnblehost.start(["Bodynode"])
    bnblehost.add_listener(bleblenderbnlistener)

    bodynodes_panel_connect["ble"]["status"] = "BLE running"
    bodynodes_panel_connect["ble"]["running"] = True


def stop_ble():
    """Stop BLE"""

    print("stop_ble")
    if not bnblehost.is_running():
        print("BLE BnHost wass already stopped...")
        bodynodes_panel_connect["ble"]["status"] = "BLE not running"
        bodynodes_panel_connect["ble"]["running"] = False
        return

    bnblehost.remove_listener(bleblenderbnlistener)
    bnblehost.stop()

    bpy.data.objects["katana"].rotation_quaternion = internal.starting_quat
    internal.starting_quat = None
    bodynodes_panel_connect["ble"]["status"] = "BLE not running"
    bodynodes_panel_connect["ble"]["running"] = False


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


def update_w_axis(
    self, context
):  # pylint: disable=unused-argument # reason: Blender callback
    """Update w axis"""

    new_axis = int(self.new_w_axis)
    if new_axis > 3:
        bodynodes_axis_config["new_w_sign"] = -1
        new_axis -= 4
    else:
        bodynodes_axis_config["new_w_sign"] = 1

    bodynodes_axis_config["new_w_val"] = new_axis
    internal.first_quat = None


def update_x_axis(
    self, context
):  # pylint: disable=unused-argument # reason: Blender callback
    """Update x axis"""

    new_axis = int(self.new_x_axis)
    if new_axis > 3:
        bodynodes_axis_config["new_x_sign"] = -1
        new_axis -= 4
    else:
        bodynodes_axis_config["new_x_sign"] = 1

    bodynodes_axis_config["new_x_val"] = new_axis
    internal.first_quat = None


def update_y_axis(
    self, context
):  # pylint: disable=unused-argument # reason: Blender callback
    """Update y axis"""

    new_axis = int(self.new_y_axis)
    if new_axis > 3:
        bodynodes_axis_config["new_y_sign"] = -1
        new_axis -= 4
    else:
        bodynodes_axis_config["new_y_sign"] = 1

    bodynodes_axis_config["new_y_val"] = new_axis
    internal.first_quat = None


def update_z_axis(
    self, context
):  # pylint: disable=unused-argument # reason: Blender callback
    """Update z axis"""

    new_axis = int(self.new_z_axis)
    if new_axis > 3:
        bodynodes_axis_config["new_z_sign"] = -1
        new_axis -= 4
    else:
        bodynodes_axis_config["new_z_sign"] = 1

    bodynodes_axis_config["new_z_val"] = new_axis
    internal.first_quat = None


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

        layout.label(text="Server:   " + bodynodes_panel_connect["server"]["status"])

        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator(
            "bodynodes.startstop_server",
            text="Stop" if bodynodes_panel_connect["server"]["running"] else "Start",
        )
        col1.enabled = True

        layout.label(text="BLE:   " + bodynodes_panel_connect["ble"]["status"])

        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator(
            "bodynodes.startstop_ble",
            text="Stop" if bodynodes_panel_connect["ble"]["running"] else "Start",
        )
        col1.enabled = True

        row = layout.row()
        row.operator("bodynodes.axis_config", text="Axis Config")

        row = layout.row()
        row.operator("bodynodes.close_main", text="Close")


class BodynodesCloseMainOperator(bpy.types.Operator):
    """Close all the Bodynodes panels"""

    bl_idname = "bodynodes.close_main"
    bl_label = "Close Main Panel Operator"
    bl_description = "Close all the Bodynodes panels"

    def execute(self, context):
        unregister_all()
        return {"FINISHED"}


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


class BodynodesStartStopBLEOperator(bpy.types.Operator):
    """Starts/Stop the local BLE central device"""

    bl_idname = "bodynodes.startstop_ble"
    bl_label = "StartStop BLE Operator"
    bl_description = "Starts/Stop the local BLE central device. It resets position of the sensors at every start"

    def execute(self, context):
        if bodynodes_panel_connect["ble"]["running"]:
            stop_ble()
        else:
            bpy.app.timers.register(start_ble, first_interval=4.0)

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


def unregister_all():
    """Unregister Application panel"""

    bpy.utils.unregister_class(BodynodesStartStopServerOperator)
    bpy.utils.unregister_class(BodynodesStartStopBLEOperator)
    bpy.utils.unregister_class(BodynodesAxisConfigOperator)
    bpy.utils.unregister_class(BodynodesCloseMainOperator)
    bpy.utils.unregister_class(PANEL_PT_BodynodesMain)
    bpy.app.timers.unregister(main_read_orientations)
    stop_server()


def register_all():
    """Register Application panel"""

    bpy.utils.register_class(BodynodesStartStopServerOperator)
    bpy.utils.register_class(BodynodesStartStopBLEOperator)
    bpy.utils.register_class(BodynodesAxisConfigOperator)
    bpy.utils.register_class(BodynodesCloseMainOperator)
    bpy.utils.register_class(PANEL_PT_BodynodesMain)
    bpy.app.timers.register(main_read_orientations)


if __name__ == "__main__":
    register_all()
