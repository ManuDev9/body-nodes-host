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
from socket import *
import threading
import json
import bpy
from mathutils import *
import struct
import time

if "bnwifibodynodeshost" in sys.modules:
    del sys.modules["bnwifibodynodeshost"]
if "bnblenderutils" in sys.modules:
    del sys.modules["bnblenderutils"]

import bnwifibodynodeshost
import bnblenderutils

fullsuit_keys = [
    "lowerarm_left",
    "lowerarm_right",
    "head",
    "lowerbody",
    "lowerleg_left",
    "lowerleg_right",
    "upperarm_left",
    "upperarm_right",
    "upperbody",
    "upperleg_left",
    "upperleg_right",
    "hand_left",
    "hand_right"
]

# This script is made for the FullSuit-11 and it is required to create connections with the nodes

bodynodes_panel_connect = {
    "server" : {
        "running": False,
        "status": "Start server"
    }
}

class BlenderBodynodeListener(bnwifibodynodeshost.BodynodeListener):
    def __init__(self):
        print("This is the Blender listener")

    def onMessageReceived(self, player, bodypart, sensortype, value):
        data_json = {
            "player": player,
            "bodypart": bodypart,
            "sensortype": sensortype,
            "value": value
        }
        bnblenderutils.read_sensordata(data_json)

    def isOfInterest(self, player, bodypart, sensortype):
        # Everything is of interest
        return True

blenderbnlistener = BlenderBodynodeListener()
bnhost = bnwifibodynodeshost.BnWifiHostCommunicator()

def start_server():
    # print("start_server")
    if bnhost.isRunning():
        print("BnHost is already there...")
        return

    bnblenderutils.reinit_bn_data()
    bnhost.start(["BN"])
    bnhost.addListener(blenderbnlistener)

    bodynodes_panel_connect["server"]["status"] = "Server running"
    bodynodes_panel_connect["server"]["running"] = True


def stop_server():
    print("stop_server")
    if not bnhost.isRunning():
        print("BnHost wass already stopped...")
        return

    bnhost.removeListener(blenderbnlistener)
    bnhost.stop();
        
    bodynodes_panel_connect["server"]["status"] = "Server not running"
    bodynodes_panel_connect["server"]["running"] = False

def create_bodynodesobjs():
    global fullsuit_keys
    for bodypart in fullsuit_keys:
        if bodypart+"_ori" not in bpy.data.objects and "hand_" not in bodypart:
            # For now we are not having orientation hands objects
            bpy.ops.object.add()
            bpy.context.active_object.name = bodypart+"_ori"
            bpy.context.active_object.location = Vector((0,0,-20))
            bpy.context.active_object.rotation_mode = "QUATERNION"
        if "hand_" in bodypart:
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


def register_connect():
    bpy.utils.register_class(BodynodesStartStopServerOperator)

    bpy.utils.register_class(PANEL_PT_BodynodesConnect)
    create_bodynodesobjs()

def unregister_connect() :
    bpy.utils.unregister_class(BodynodesStartStopServerOperator)

    bpy.utils.unregister_class(PANEL_PT_BodynodesConnect)
    stop_server()

def stop_at_last_frame(scene):
    if scene.frame_current == scene.frame_end-1:
        stop_animation()

if __name__ == "__main__" :
    register_connect()
    




