/**
* MIT License
* 
* Copyright (c) 2019-2024 Manuel Bottini
*
* Permission is hereby granted, free of charge, to any person obtaining a copy
* of this software and associated documentation files (the "Software"), to deal
* in the Software without restriction, including without limitation the rights
* to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
* copies of the Software, and to permit persons to whom the Software is
* furnished to do so, subject to the following conditions:

* The above copyright notice and this permission notice shall be included in all
* copies or substantial portions of the Software.

* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
* IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
* FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
* AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
* LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
* OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
* SOFTWARE.
*/

using UnityEngine;
using System.Collections;
using UnityEditor;

#if __BODYNODES_DEV
using BodynodesDev;
#elif __BODYNODES_P
using BodynodesP;
#else
#error "You need to set up the preprocessing environment flag in Unity: 'File' -> 'Buil Settings' -> 'Player Settings' -> 'Player' -> 'Script Compilation'. Click on + and then add __BODYNODES_P or __BODYNODES_DEV, depending if you you want an prod or dev environment"
#endif

public class BodynodesController : MonoBehaviour
{

    public string mBodypart;
    public BodynodesPlayer mMainPlayer;
    private volatile BodynodesHostInterface mBodynodesHost;

    private bool mIsReceiving;

    //Internal positioning
    public Transform mBodypartTransform;

    private Quaternion mTargetQuat;
    private Quaternion mReadQuat;
    private Quaternion mOffsetQuat;
    private Quaternion mStartQuat;

    //Communication
    private bool mReceivingMessages;

    public char new_w_val = 'w';
    public char new_x_val = 'z';
    public char new_y_val = 'y';
    public char new_z_val = 'x';

    public char new_w_sign = '+';
    public char new_x_sign = '+';
    public char new_y_sign = '+';
    public char new_z_sign = '+';
    public void setAxisVal(char game_axis, char sens_axis)
    {
        if (game_axis == 'w')
        {
            new_w_val = sens_axis;
        }
        else if (game_axis == 'x')
        {
            new_x_val = sens_axis;
        }
        else if (game_axis == 'y')
        {
            new_y_val = sens_axis;
        }
        else if (game_axis == 'z')
        {
            new_z_val = sens_axis;
        }
    }

    public void setAxisSign(char game_axis, char sign)
    {
        if (game_axis == 'w')
        {
            new_w_sign = sign;
        }
        else if (game_axis == 'x')
        {
            new_x_sign = sign;
        }
        else if (game_axis == 'y')
        {
            new_y_sign = sign;
        }
        else if (game_axis == 'z')
        {
            new_z_sign = sign;
        }
    }

    public char getAxisVal(char game_axis)
    {
        if (game_axis == 'w')
        {
            return new_w_val;
        }
        else if (game_axis == 'x')
        {
            return new_x_val;
        }
        else if (game_axis == 'y')
        {
            return new_y_val;
        }
        else if (game_axis == 'z')
        {
            return new_z_val;
        }
        return ' ';
    }
    public char getAxisSign(char game_axis)
    {
        if (game_axis == 'w')
        {
            return new_w_sign;
        }
        else if (game_axis == 'x')
        {
            return new_x_sign;
        }
        else if (game_axis == 'y')
        {
            return new_y_sign;
        }
        else if (game_axis == 'z')
        {
            return new_z_sign;
        }
        return ' ';
    }

    public bool isReceiving() {
        return mIsReceiving;
    }

    // Use this for initialization
    public void Start()
    {
        mIsReceiving = false;
        //I get the components
        //cDebugText = null;
        mBodynodesHost = mMainPlayer.getInternalHostCommunicator();

        Debug.Log("mBodynodes = " + mBodynodesHost);

        mOffsetQuat = new Quaternion(0, 0, 0, 0);
        mReadQuat = new Quaternion(0, 0, 0, 0);
        mTargetQuat = new Quaternion(0, 0, 0, 0);

        mStartQuat = new Quaternion(
            mBodypartTransform.rotation.x,
            mBodypartTransform.rotation.y,
            mBodypartTransform.rotation.z,
            mBodypartTransform.rotation.w);
        mReceivingMessages = false;

    }

    // Update is called once per frame
    public void Update()
    {
        performQuatAction();
    }

    public void LateUpdate()
    {
        gotoTargetQuat();
    }


    private float timeToRotate = 0;

    private void gotoTargetQuat()
    {
        if (!mReceivingMessages)
        {
            return;
        }

        //Debug.Log ("mTargetQuar " + mBodypart + " -> " + mTargetQuat.w + "|" + mTargetQuat.x + "|" + mTargetQuat.y+ "|" + mTargetQuat.z);

        //mBodypartTransform.rotation = Quaternion.Euler(mTargetAngle);
        //mBodypartTransform.localRotation = Quaternion.Euler(mTargetAngle);

        //mBodypartTransform.rotation = mTargetQuat;
        if (Time.fixedTime >= timeToRotate)
        {
            // Do your thing
            timeToRotate = Time.fixedTime + 0.060f;

            mBodypartTransform.SetPositionAndRotation(
                mBodypartTransform.position,
                Quaternion.Slerp(mBodypartTransform.rotation, mTargetQuat, 0.7f)
            );
            /*
            mBodypartTransform.SetPositionAndRotation (
                mBodypartTransform.position,
                mTargetQuat
            );
            */
        }
    }

    public void SetOffsetStart()
    {
        mOffsetQuat = Quaternion.Inverse(mReadQuat);
    }
    
    public void resetPosition()
    {
        mOffsetQuat = new Quaternion(0, 0, 0, 0);
        mBodypartTransform.rotation = mStartQuat;
        mTargetQuat = mStartQuat;
    }

    private string[] values;

    private void performQuatAction()
    {
        if (mMainPlayer.getPlayer().value == BnConstants.PLAYER_NONE_TAG) {
            return;
        }
        BnDatatypes.BnName player = mMainPlayer.getPlayer();
        BnDatatypes.BnBodypart bodypart = new BnDatatypes.BnBodypart();
        bodypart.setFromString(mBodypart);
        BnDatatypes.BnType sensortype = new BnDatatypes.BnType();
        sensortype.value = BnConstants.SENSORTYPE_ORIENTATION_ABS_TAG;
        BnDatatypes.BnMessage message = mBodynodesHost.getMessage(player, bodypart, sensortype);
        if (message.getBodypart().value == BnConstants.BODYPART_NONE_TAG)
        {
            //Debug.Log("Could not find messages of player = " + player.value + " bodypart = " + mBodypart + " sensortype = " + sensortype.value);
            return;
        }
        mIsReceiving = true;
        if (message.isOrientationAbsReset()) {
            Debug.Log("OrientationAbs Recalibrate message has been received for player = " + message.getPlayer().value + " bodypart = " + message.getBodypart().value);
            resetPosition();
            return;
        }

        float[] values = message.getData().getValuesFloat();

        Debug.Log(mBodypart + " values.Length = " + values.Length);
        Debug.Log(mBodypart + " values = " + values[0] + ", " + values[1] + ", " + values[2] + ", " + values[3]);

        mReceivingMessages = true;
        float w = values[0];
        float x = values[1];
        float y = values[2];
        float z = values[3];

        float new_w = w;
        float new_x = x;
        float new_y = y;
        float new_z = z;
        if (getAxisVal('x') == 'x')
        {
            new_x = x;
        }
        else if (getAxisVal('x') == 'y')
        {
            new_x = y;
        }
        else if (getAxisVal('x') == 'z')
        {
            new_x = z;
        }
        else if (getAxisVal('x') == 'w')
        {
            new_x = w;
        }

        if (getAxisVal('y') == 'x')
        {
            new_y = x;
        }
        else if (getAxisVal('y') == 'y')
        {
            new_y = y;
        }
        else if (getAxisVal('y') == 'z')
        {
            new_y = z;
        }
        else if (getAxisVal('y') == 'w')
        {
            new_y = w;
        }

        if (getAxisVal('z') == 'x')
        {
            new_z = x;
        }
        else if (getAxisVal('z') == 'y')
        {
            new_z = y;
        }
        else if (getAxisVal('z') == 'z')
        {
            new_z = z;
        }
        else if (getAxisVal('z') == 'w')
        {
            new_z = w;
        }

        if (getAxisVal('w') == 'x')
        {
            new_w = x;
        }
        else if (getAxisVal('w') == 'y')
        {
            new_w = y;
        }
        else if (getAxisVal('w') == 'z')
        {
            new_w = z;
        }
        else if (getAxisVal('w') == 'w')
        {
            new_w = w;
        }

        if (getAxisSign('x') == '-')
        {
            new_x = -new_x;
        }
        if (getAxisSign('y') == '-')
        {
            new_y = -new_y;
        }
        if (getAxisSign('z') == '-')
        {
            new_z = -new_z;
        }
        if (getAxisSign('w') == '-')
        {
            new_w = -new_w;
        }

        mReadQuat.Set(new_w, new_x, new_y, new_z);

        if (mOffsetQuat.w == 0 && mOffsetQuat.x == 0 && mOffsetQuat.y == 0 && mOffsetQuat.z == 0)
        {
            //first valid message received will trigger adjustation
            mOffsetQuat = Quaternion.Inverse(mReadQuat);
        }

        mTargetQuat = mStartQuat * mOffsetQuat * mReadQuat;

    }

    public void sendHapticAction(ushort duration_ms, ushort strength)
    {
        //Debug.Log("sendHapticAction player = " + mMainPlayer.getPlayer().value + " bodypart " + mBodypart + " duration_ms = " + duration_ms + " strength = " + strength);
        if (mMainPlayer.getPlayer().value == BnConstants.PLAYER_NONE_TAG)
        {
            return;
        }
        BnDatatypes.BnName player = mMainPlayer.getPlayer();
        BnDatatypes.BnBodypart bodypart = new BnDatatypes.BnBodypart();
        bodypart.setFromString(mBodypart);
        BnDatatypes.BnAction action = new BnDatatypes.BnAction();
        action.createHaptic(player, bodypart, duration_ms, strength);
        mBodynodesHost.addAction(action);
    }
}
