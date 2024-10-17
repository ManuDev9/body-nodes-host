#
# MIT License
# 
# Copyright (c) 2024 Manuel Bottini
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


import glob
import os
import sys
import json
import bpy
import mathutils
import time

dir_path = os.path.dirname(os.path.realpath(__file__))

# Removing the scripts saved in cache so that Blender uses the last updated version of the scritps
[os.remove(file) for file in glob.glob(os.path.join(os.path.abspath(__file__ + "/../../scripts/__pycache__"), "bnmain.cpython*.pyc"))]
[os.remove(file) for file in glob.glob(os.path.join(os.path.abspath(__file__ + "/../../../common/__pycache__"), "bnblenderutils.cpython*.pyc"))]
[os.remove(file) for file in glob.glob(os.path.join(os.path.abspath(__file__ + "/../../../../modules/pythonlib/__pycache__"), "bnwifibodynodeshost.cpython*.pyc"))]
[os.remove(file) for file in glob.glob(os.path.join(os.path.abspath(__file__ + "/../../../../modules/pythonlib/__pycache__"), "bnblebodynodeshost.cpython*.pyc"))]

sys.path.append(os.path.abspath(__file__)+"/../../scripts")
sys.path.append(os.path.abspath(__file__)+"/../../../common")
sys.path.append(os.path.abspath(__file__)+"/../../../../../modules/pythonlib")

if "bnblenderutils" in sys.modules:
    del sys.modules["bnblenderutils"]

import bnblenderutils
import bnblebodynodeshost

bodynodes_panel_connect = {
    "server" : {
        "running": False,
        "status": "Start server"
    }
}

katana_quat = [1, 0, 0, 0]

class BlenderBodynodeListener(bnblebodynodeshost.BodynodeListener):
    def __init__(self):
        print("This is the Blender listener")

    def onMessageReceived(self, player, bodypart, sensortype, value):
        data_json = {
            "player": player,
            "bodypart": bodypart,
            "sensortype": sensortype,
            "value": value
        }
        global katana_quat
        katana_quat[0] = value[0]
        katana_quat[1] = value[1]
        katana_quat[2] = value[2]
        katana_quat[3] = value[3]

    def isOfInterest(self, player, bodypart, sensortype):
        if bodypart in bpy.data.objects and sensortype == "orientation_abs":
            return True
        return False

blenderbnlistener = BlenderBodynodeListener()
#bnhost = bnwifibodynodeshost.BnWifiHostCommunicator()
bnhost = bnblebodynodeshost.BnBLEHostCommunicator()


def main_read_orientations():
    global katana_quat
    bpy.data.objects["katana"].rotation_quaternion = mathutils.Quaternion(katana_quat)
    return 0.02

def start_server():
    # print("start_server")
    if bnhost.isRunning():
        print("BnHost is already there...")
        return

    bnblenderutils.reinit_bn_data()
    #bnhost.start(["BN"])
    bnhost.start(["Bodynode"])
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

class PANEL_PT_BodynodesMain(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'View'
    bl_label = "Bodynodes Main"

    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Server:   "  + bodynodes_panel_connect["server"]["status"])
        
        row = layout.row()
        row.scale_y = 1.0
        col1 = row.column()
        col1.operator("bodynodes.startstop_server",
            text="Stop" if bodynodes_panel_connect["server"]["running"] else "Start")
        col1.enabled = True
        
        row = layout.row()
        row.operator("bodynodes.close_main", text="Close")


class BodynodesCloseMainOperator(bpy.types.Operator):
    bl_idname = "bodynodes.close_main"
    bl_label = "Close Main Panel Operator"
    bl_description = "Close all the Bodynodes panels"

    def execute(self, context):
        unregister_all()
        return {'FINISHED'}

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

def unregister_all():

    bpy.utils.unregister_class(BodynodesStartStopServerOperator)
    bpy.utils.unregister_class(BodynodesCloseMainOperator)
    bpy.utils.unregister_class(PANEL_PT_BodynodesMain)
    bpy.app.timers.unregister(main_read_orientations)
    stop_server()
    

def register_all():

    bpy.utils.register_class(BodynodesStartStopServerOperator)
    bpy.utils.register_class(BodynodesCloseMainOperator)
    bpy.utils.register_class(PANEL_PT_BodynodesMain)
    bpy.app.timers.register(main_read_orientations)    
	
if __name__ == "__main__" :
    register_all()




