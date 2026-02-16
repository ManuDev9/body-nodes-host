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

"""Blender Animation application based on Bodynodes"""

import glob
import os
import sys
import bpy

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
        os.path.abspath(__file__ + "/../../../BlenderCommon/__pycache__"),
        "bnblenderconnect.cpython*.pyc",
    )
):
    os.remove(file)

for file in glob.glob(
    os.path.join(
        os.path.abspath(__file__ + "/../../../BlenderCommon/__pycache__"),
        "bnblenderanimation.cpython*.pyc",
    )
):
    os.remove(file)

for file in glob.glob(
    os.path.join(
        os.path.abspath(__file__ + "/../../../BlenderCommon/__pycache__"),
        "bnblenderrecording.cpython*.pyc",
    )
):
    os.remove(file)

for file in glob.glob(
    os.path.join(
        os.path.abspath(__file__ + "/../../../BlenderCommon/__pycache__"),
        "bnblenderaxis.cpython*.pyc",
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

print(os.path.abspath(__file__) + "/../../../BlenderCommon")

if "bnblenderanimation" in sys.modules:
    del sys.modules["bnblenderanimation"]
if "bnblenderconnect" in sys.modules:
    del sys.modules["bnblenderconnect"]
if "bnblenderrecording" in sys.modules:
    del sys.modules["bnblenderrecording"]
if "bnblenderaxis" in sys.modules:
    del sys.modules["bnblenderaxis"]

import bnblenderconnect  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
import bnblenderanimation  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
import bnblenderrecording  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
import bnblenderaxis  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting


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


class BodynodesCloseMainOperator(bpy.types.Operator):
    """Close all the Bodynodes panels"""

    bl_idname = "bodynodes.close_main"
    bl_label = "Close Main Panel Operator"
    bl_description = "Close all the Bodynodes panels"

    def execute(self, context):
        unregister_all()
        return {"FINISHED"}


class BnConnectListener:
    """Connect module listener"""

    def read_sensordata_callback(self, data_json):
        """Read sensor callback"""

        bnblenderrecording.read_sensordata(data_json)

    def reinit_bn_data(self):
        """Trigger to reinitialise data"""

        bnblenderrecording.reinit_bn_data()


connect_listener = BnConnectListener()


def unregister_all():
    """Unregister the application panel"""

    bpy.utils.unregister_class(BodynodesCloseMainOperator)
    bpy.utils.unregister_class(PANEL_PT_BodynodesMain)

    bnblenderconnect.unregister_connect()
    bnblenderanimation.unregister_animation()
    bnblenderrecording.unregister_recording()
    bnblenderaxis.unregister_axis()


def register_all():
    """Register the application panel"""

    bpy.utils.register_class(BodynodesCloseMainOperator)
    bpy.utils.register_class(PANEL_PT_BodynodesMain)

    bnblenderconnect.register_connect(connect_listener)
    bnblenderanimation.register_animation()
    bnblenderrecording.register_recording()
    bnblenderaxis.register_axis()

    bnblenderaxis.load_axis_config_default(os.path.realpath(__file__))


if __name__ == "__main__":
    register_all()
