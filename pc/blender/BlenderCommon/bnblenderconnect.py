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

# Implements Specification version 1.0

import glob
import os
import sys
import json
import bpy
from mathutils import *
import struct
import time

if "bnwifibodynodeshost" in sys.modules:
    del sys.modules["bnwifibodynodeshost"]
if "bnblebodynodeshost" in sys.modules:
    del sys.modules["bnblebodynodeshost"]
if "bnblenderutils" in sys.modules:
    del sys.modules["bnblenderutils"]

import bnwifibodynodeshost
import bnblebodynodeshost
import bnblenderutils

mConnectListener = None

# This script is made for the FullSuit-11 and it is required to create connections with the nodes

bodynodes_panel_connect = {
    "server" : {
        "running": False,
        "status": "Start server"
    },
    "ble" : {
        "running": False,
        "status": "Start BLE"
    }
}

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
        mConnectListener.read_sensordata_callback(data_json)

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
        mConnectListener.read_sensordata_callback(data_json)

    def isOfInterest(self, player, bodypart, sensortype):
        # Everything is of interest
        return True

bleblenderbnlistener = BLEBlenderBodynodeListener()
bnblehost = bnblebodynodeshost.BnBLEHostCommunicator()

wifiblenderbnlistener = WifiBlenderBodynodeListener()
bnwifihost = bnwifibodynodeshost.BnWifiHostCommunicator()

def start_server():
    print("start_server")
    if bnwifihost.isRunning():
        print("Wifi BnHost is already there...")
        return

    mConnectListener.reinit_bn_data()
    bnwifihost.start(["BN"])
    bnwifihost.addListener(wifiblenderbnlistener)

    bodynodes_panel_connect["server"]["status"] = "Server running"
    bodynodes_panel_connect["server"]["running"] = True

def stop_server():
    print("stop_server")
    if not bnwifihost.isRunning():
        print("Wifi BnHost was already stopped...")
        return

    bnwifihost.removeListener(wifiblenderbnlistener)
    bnwifihost.stop();
        
    mConnectListener.reinit_bn_data()
    bodynodes_panel_connect["server"]["status"] = "Server not running"
    bodynodes_panel_connect["server"]["running"] = False

def start_ble():
    print("start_ble")
    if bnwifihost.isRunning():
        print("BLE BnHost is already there...")
        return

    mConnectListener.reinit_bn_data()
    bnblehost.start(["Bodynode"]) # Just for the Maker Faire
    bnblehost.addListener(bleblenderbnlistener)

    bodynodes_panel_connect["ble"]["status"] = "BLE running"
    bodynodes_panel_connect["ble"]["running"] = True


def stop_ble():
    print("stop_ble")
    if not bnblehost.isRunning():
        print("BLE BnHost was already stopped...")
        return

    mConnectListener.reinit_bn_data()
    bnblehost.removeListener(bleblenderbnlistener)
    bnblehost.stop();
        
    bodynodes_panel_connect["ble"]["status"] = "BLE not running"
    bodynodes_panel_connect["ble"]["running"] = False


def create_bodynodesobjs():
    for bodypart in bnblenderutils.bodynode_bones_init:
        if bodypart == "Hip":
            continue
        if bodypart+"_ori" not in bpy.data.objects and "hand_" not in bodypart:
            # For now we are not having orientation hands objects
            bpy.ops.object.add()
            bpy.context.active_object.name = bodypart+"_ori"
            bpy.context.active_object.location = Vector((0,0,-20))
            bpy.context.active_object.rotation_mode = "QUATERNION"
        if "hand_" in bodypart or "katana" in bodypart:
            for finger in bnblenderutils.bodynode_fingers_init:
                if bodypart+"_"+finger not in bpy.data.objects:
                    bpy.ops.object.add()
                    bpy.context.active_object.name = bodypart+"_"+finger
                    bpy.context.active_object.location = Vector((0,0,-30))
                    bpy.context.active_object.rotation_mode = "XYZ"

class PANEL_PT_BodynodesConnect(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'View'
    bl_label = "Bodynodes Connect"

    def draw(self, context):
        layout = self.layout
        
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
    bl_description = "Starts/Stop the local ble central device. It resets position of the sensors at every start"

    def execute(self, context):
        if bodynodes_panel_connect["ble"]["running"]:
            stop_ble()
        else:
            bpy.app.timers.register(start_ble, first_interval=4.0)

        return {'FINISHED'}


def register_connect(connectListener):

    global mConnectListener
    mConnectListener = connectListener

    bpy.utils.register_class(BodynodesStartStopServerOperator)
    bpy.utils.register_class(BodynodesStartStopBLEOperator)

    bpy.utils.register_class(PANEL_PT_BodynodesConnect)
    create_bodynodesobjs()

def unregister_connect():

    mConnectListener = None

    bpy.utils.unregister_class(BodynodesStartStopServerOperator)
    bpy.utils.unregister_class(BodynodesStartStopBLEOperator)

    bpy.utils.unregister_class(PANEL_PT_BodynodesConnect)
    stop_server()

def stop_at_last_frame(scene):
    if scene.frame_current == scene.frame_end-1:
        stop_animation()

if __name__ == "__main__" :
    register_connect()
    




