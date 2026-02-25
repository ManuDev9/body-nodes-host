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
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""BLE Mouse app based on Bodynodes"""

import sys
import os
import time
from dataclasses import dataclass

# pip install pyautogui
import pyautogui

# Disable the failsafe feature
pyautogui.FAILSAFE = False

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../modules/pythonlib")
sys.path.append(
    os.path.dirname(os.path.abspath(__file__)) + "/../../body-nodes-common/python"
)

import bnblebodynodeshost  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
from bncommon import (  # pylint: disable=wrong-import-position # reason: Need to remove Blender cached modules before reimporting
    BnConstants,
)


@dataclass
class Internal:
    """Internal module data dataclass"""

    is_button_left_down = False
    is_button_right_down = False


internal = Internal()


def mouse_move(angvel_rel):
    """Move mouse depending on relative angular velocity"""

    # print(angvel_rel)
    val_x = 0
    val_y = 0
    if abs(angvel_rel[2]) > 1.3:
        val_x = -angvel_rel[2] * 500
    elif abs(angvel_rel[2]) > 1.0:
        val_x = -angvel_rel[2] * 300
    elif abs(angvel_rel[2]) > 0.8:
        val_x = -angvel_rel[2] * 200
    else:
        val_x = -angvel_rel[2] * 100

    if abs(angvel_rel[1]) > 1.3:
        val_y = -angvel_rel[1] * 500
    elif abs(angvel_rel[1]) > 1.0:
        val_y = -angvel_rel[1] * 300
    elif abs(angvel_rel[1]) > 0.8:
        val_y = -angvel_rel[1] * 200
    else:
        val_y = -angvel_rel[1] * 100

    pyautogui.moveRel(val_x, val_y, duration=0.1)


def mouse_click(glove_vals):
    """Click mouse depending on glove value"""

    print(glove_vals)
    if glove_vals[BnConstants.GLOVE_TOUCH_INDICE_INDEX] == 1:
        pyautogui.mouseDown(button="left")
        internal.is_button_left_down = True
    elif (
        glove_vals[BnConstants.GLOVE_TOUCH_INDICE_INDEX] == 0
        and internal.is_button_left_down
    ):
        pyautogui.mouseUp(button="left")
        internal.is_button_left_down = False

    if glove_vals[BnConstants.GLOVE_TOUCH_MEDIO_INDEX] == 1:
        pyautogui.mouseDown(button="right")
        internal.is_button_right_down = True
    elif (
        glove_vals[BnConstants.GLOVE_TOUCH_MEDIO_INDEX] == 0
        and internal.is_button_right_down
    ):
        pyautogui.mouseUp(button="right")
        internal.is_button_right_down = False


class BlenderBodynodeListener(bnblebodynodeshost.BodynodeListener):
    """Bodynode Host listener"""

    def __init__(self):
        print("This is the Blender listener")

    def on_message_received(self, player, bodypart, sensortype, value):
        # print(player)
        # print(bodypart)
        # print(sensortype)
        if sensortype == BnConstants.SENSORTYPE_ANGULARVELOCITY_REL_TAG:
            mouse_move(value)
        elif sensortype == BnConstants.SENSORTYPE_GLOVE_TAG:
            mouse_click(value)

    def is_of_interest(self, player, bodypart, sensortype):
        if sensortype in (
            BnConstants.SENSORTYPE_ANGULARVELOCITY_REL_TAG,
            BnConstants.SENSORTYPE_GLOVE_TAG,
        ):
            return True
        return False


blenderbnlistener = BlenderBodynodeListener()
# bnhost = bnwifibodynodeshost.BnWifiHostCommunicator()
bnhost = bnblebodynodeshost.BnBLEHostCommunicator()


if __name__ == "__main__":
    bnhost.start(["Bodynod0"])  # Just for the MakerFaire
    bnhost.add_listener(blenderbnlistener)

    try:
        print("Bodynodes BLE Mouse is running. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCtrl+C pressed. Exiting...")
        bnhost.remove_listener(blenderbnlistener)
        bnhost.stop()
