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

"""Connect Panel to connect Blender to Bodynodes Sensors"""

import sys
from dataclasses import dataclass
import bpy
import mathutils

if "bnwifibodynodeshost" in sys.modules:
    del sys.modules["bnwifibodynodeshost"]
if "bnblebodynodeshost" in sys.modules:
    del sys.modules["bnblebodynodeshost"]
if "bnblenderutils" in sys.modules:
    del sys.modules["bnblenderutils"]

import bnwifibodynodeshost  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
import bnblebodynodeshost  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
import bnblenderutils  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting


@dataclass
class Internal:
    """Internal module data dataclass"""

    bn_listener = None
    bodynodes_panel_connect = {
        "server": {"running": False, "status": "Start server"},
        "ble": {"running": False, "status": "Start BLE"},
    }


internal = Internal()


class BLEBlenderBodynodeListener(bnblebodynodeshost.BodynodeListener):
    """BLE Host Listener"""

    def __init__(self):
        print("This is the BLE Blender listener")

    def on_message_received(self, player, bodypart, sensortype, value):
        """Called back when a message is received via BLE"""
        data_json = {
            "player": player,
            "bodypart": bodypart,
            "sensortype": sensortype,
            "value": value,
        }
        internal.bn_listener.read_sensordata_callback(data_json)

    def is_of_interest(
        self, player, bodypart, sensortype
    ):  # pylint: disable=unused-argument # reason: Needed for the callback definition
        """Indicates which params the listerner is interested on"""
        return True


class WifiBlenderBodynodeListener(bnwifibodynodeshost.BodynodeListener):
    """Wifi Host Listener"""

    def __init__(self):
        print("This is the Wifi Blender listener")

    def on_message_received(self, player, bodypart, sensortype, value):
        """Called back when a message is received via Wifi"""

        data_json = {
            "player": player,
            "bodypart": bodypart,
            "sensortype": sensortype,
            "value": value,
        }
        internal.bn_listener.read_sensordata_callback(data_json)

    def is_of_interest(
        self, player, bodypart, sensortype
    ):  # pylint: disable=unused-argument # reason: Needed for the callback definition
        """Indicates which params the listerner is interested on"""
        return True


bleblenderbnlistener = BLEBlenderBodynodeListener()
bnblehost = bnblebodynodeshost.BnBLEHostCommunicator()

wifiblenderbnlistener = WifiBlenderBodynodeListener()
bnwifihost = bnwifibodynodeshost.BnWifiHostCommunicator()


def start_server():
    """Start Wifi Host"""

    if bnwifihost.is_running():
        print("Wifi BnHost is already there...")
        return

    internal.bn_listener.reinit_bn_data()
    bnwifihost.start(["BN"])
    bnwifihost.add_listener(wifiblenderbnlistener)

    internal.bodynodes_panel_connect["server"]["status"] = "Server running"
    internal.bodynodes_panel_connect["server"]["running"] = True


def stop_server():
    """Stop Wifi Host"""

    if not bnwifihost.is_running():
        print("Wifi BnHost was already stopped...")
        return

    bnwifihost.remove_listener(wifiblenderbnlistener)
    bnwifihost.stop()

    internal.bn_listener.reinit_bn_data()
    internal.bodynodes_panel_connect["server"]["status"] = "Server not running"
    internal.bodynodes_panel_connect["server"]["running"] = False


def start_ble():
    """Start BLE Host"""

    if bnwifihost.is_running():
        print("BLE BnHost is already there...")
        return

    internal.bn_listener.reinit_bn_data()
    bnblehost.start(["Bodynode"])  # Just for the Maker Faire
    bnblehost.add_listener(bleblenderbnlistener)

    internal.bodynodes_panel_connect["ble"]["status"] = "BLE running"
    internal.bodynodes_panel_connect["ble"]["running"] = True


def stop_ble():
    """Stop BLE Host"""

    if not bnblehost.is_running():
        print("BLE BnHost was already stopped...")
        return

    internal.bn_listener.reinit_bn_data()
    bnblehost.remove_listener(bleblenderbnlistener)
    bnblehost.stop()

    internal.bodynodes_panel_connect["ble"]["status"] = "BLE not running"
    internal.bodynodes_panel_connect["ble"]["running"] = False


def create_bodynodesobjs():
    """Create the Blender objects to each bodypart on the bones"""

    for bodypart in bnblenderutils.bodynode_bones_init:
        if bodypart == "Hip":
            continue
        if bodypart + "_ori" not in bpy.data.objects and "hand_" not in bodypart:
            # For now we are not having orientation hands objects
            bpy.ops.object.add()
            bpy.context.active_object.name = bodypart + "_ori"
            bpy.context.active_object.location = mathutils.Vector((0, 0, -20))
            bpy.context.active_object.rotation_mode = "QUATERNION"
        if "hand_" in bodypart or "katana" in bodypart:
            for finger in bnblenderutils.bodynode_fingers_init:
                if bodypart + "_" + finger not in bpy.data.objects:
                    bpy.ops.object.add()
                    bpy.context.active_object.name = bodypart + "_" + finger
                    bpy.context.active_object.location = mathutils.Vector((0, 0, -30))
                    bpy.context.active_object.rotation_mode = "XYZ"


class PANEL_PT_BodynodesConnect(
    bpy.types.Panel
):  # pylint: disable=invalid-name # reason: Blender naming convention
    """Bodynodes Connect Blender Panel"""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"
    bl_label = "Bodynodes Connect"

    def draw(self, context):
        layout = self.layout

        layout.label(
            text="Server:   " + internal.bodynodes_panel_connect["server"]["status"]
        )

        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator(
            "bodynodes.startstop_server",
            text=(
                "Stop"
                if internal.bodynodes_panel_connect["server"]["running"]
                else "Start"
            ),
        )
        col1.enabled = True

        layout.label(text="BLE:   " + internal.bodynodes_panel_connect["ble"]["status"])

        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator(
            "bodynodes.startstop_ble",
            text=(
                "Stop"
                if internal.bodynodes_panel_connect["ble"]["running"]
                else "Start"
            ),
        )
        col1.enabled = True


class BodynodesStartStopServerOperator(bpy.types.Operator):
    """Start Stop Wifi Server Button Operator"""

    bl_idname = "bodynodes.startstop_server"
    bl_label = "StartStop Server Operator"
    bl_description = (
        "Starts/Stop the local server. It resets position of the sensors at every start"
    )

    def execute(self, context):
        if internal.bodynodes_panel_connect["server"]["running"]:
            stop_server()
        else:
            bpy.app.timers.register(start_server, first_interval=4.0)

        return {"FINISHED"}


class BodynodesStartStopBLEOperator(bpy.types.Operator):
    """Start Stop BLE Button Operator"""

    bl_idname = "bodynodes.startstop_ble"
    bl_label = "StartStop BLE Operator"
    bl_description = "Starts/Stop the local ble central device. It resets position of the sensors at every start"

    def execute(self, context):
        if internal.bodynodes_panel_connect["ble"]["running"]:
            stop_ble()
        else:
            bpy.app.timers.register(start_ble, first_interval=4.0)

        return {"FINISHED"}


def register_connect(connect_listener):
    """Register the Bodynodes Connect panel"""

    internal.bn_listener = connect_listener

    bpy.utils.register_class(BodynodesStartStopServerOperator)
    bpy.utils.register_class(BodynodesStartStopBLEOperator)

    bpy.utils.register_class(PANEL_PT_BodynodesConnect)
    create_bodynodesobjs()


def unregister_connect():
    """Unregister the Bodynodes Connect panel"""

    internal.bn_listener = None

    bpy.utils.unregister_class(BodynodesStartStopServerOperator)
    bpy.utils.unregister_class(BodynodesStartStopBLEOperator)

    bpy.utils.unregister_class(PANEL_PT_BodynodesConnect)
    stop_server()


if __name__ == "__main__":
    print(
        "Meant to be called withing Blender from a main script using the functionalities in here"
    )
