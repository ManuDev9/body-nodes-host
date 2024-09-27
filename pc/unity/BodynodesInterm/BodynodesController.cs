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
using System.Reflection;
using System;

#if __BODYNODES_DEV
using BodynodesDev;
using BodynodesDev.Common;
#elif __BODYNODES_P
using BodynodesP;
using BodynodesP.Common;
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
    private BnReorientAxis mReorientAxis;

    //Communication
    private bool mReceivingMessages;

    public char new_w_val = 'w';
    public char new_x_val = 'z';
    public char new_y_val = 'y';
    public char new_z_val = 'x';

    public char new_w_sign = '+';
    public char new_x_sign = '-';
    public char new_y_sign = '+';
    public char new_z_sign = '+';

    private void setupReiorient()
    {
        int[] ioAxis = new int[] { 0, 1, 2, 3 };
        int[] ioSign = new int[] { -1, 1, 1, 1 };

        if (new_w_val == 'w')
        {
            ioAxis[0] = 0;
        }
        else if (new_w_val == 'x' )
        {
            ioAxis[0] = 1;
        }
        else if (new_w_val == 'y')
        {
            ioAxis[0] = 2;
        }
        else if (new_w_val == 'z')
        {
            ioAxis[0] = 3;
        }

        /////////
        if (new_x_val == 'w')
        {
            ioAxis[1] = 0;
        }
        else if (new_x_val == 'x')
        {
            ioAxis[1] = 1;
        }
        else if (new_x_val == 'y')
        {
            ioAxis[1] = 2;
        }
        else if (new_x_val == 'z')
        {
            ioAxis[1] = 3;
        }

        /////////
        if (new_y_val == 'w')
        {
            ioAxis[2] = 0;
        }
        else if (new_y_val == 'x')
        {
            ioAxis[2] = 1;
        }
        else if (new_y_val == 'y')
        {
            ioAxis[2] = 2;
        }
        else if (new_y_val == 'z')
        {
            ioAxis[2] = 3;
        }

        /////////
        if (new_z_val == 'w')
        {
            ioAxis[3] = 0;
        }
        else if (new_z_val == 'x')
        {
            ioAxis[3] = 1;
        }
        else if (new_z_val == 'y')
        {
            ioAxis[3] = 2;
        }
        else if (new_z_val == 'z')
        {
            ioAxis[3] = 3;
        }

        //////////
        if (new_w_sign == '+')
        {
            ioSign[0] = 1;
        }
        else if (new_w_sign == '-')
        {
            ioSign[0] = -1;
        }

        //////////
        if (new_x_sign == '+')
        {
            ioSign[1] = 1;
        }
        else if (new_x_sign == '-')
        {
            ioSign[1] = -1;
        }

        //////////
        if (new_y_sign == '+')
        {
            ioSign[2] = 1;
        }
        else if (new_y_sign == '-')
        {
            ioSign[2] = -1;
        }

        //////////
        if (new_z_sign == '+')
        {
            ioSign[3] = 1;
        }
        else if (new_z_sign == '-')
        {
            ioSign[3] = -1;
        }

        mReorientAxis.config(ioAxis, ioSign);
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
        mBodynodesHost =  BodynodesHostCommunicator.Instance.getInternalHostCommunicator();

        Debug.Log("mBodynodes = " + mBodynodesHost);
        mReorientAxis = new BnReorientAxis();

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

        float[] valuesTmp = message.getData().getValuesFloat();
        float[] values = new float[valuesTmp.Length];
        values[0] = valuesTmp[0];
        values[1] = valuesTmp[1];
        values[2] = valuesTmp[2];
        values[3] = valuesTmp[3];

        Debug.Log(mBodypart + " values.Length = " + values.Length);
        Debug.Log(mBodypart + " values = " + values[0] + ", " + values[1] + ", " + values[2] + ", " + values[3]);

        mReceivingMessages = true;

        setupReiorient();
        mReorientAxis.apply(values);
        Debug.Log(mBodypart + " after values = " + values[0] + ", " + values[1] + ", " + values[2] + ", " + values[3]);



        mReadQuat.Set(values[0], values[1], values[2], values[3]);

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
