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
using Newtonsoft.Json.Linq;

public class BodynodeControllerX : MonoBehaviour
{

    public string mBodyPart;
    public BodynodesPlayer mMainPlayer;
    private volatile BodynodesHostInterface mBodynodes;

    //Internal positioning
    private Transform mBodyPartTransform;

    private bool mRepositioning;

    private Quaternion mTargetQuat;
    private Quaternion mReadQuat;
    private Quaternion mOffsetQuat;
    private Quaternion mStartQuat;

    //Communication
    private bool mReceivingMessages;

    // Use this for initialization
    void Start()
    {
        //I get the components
        //cDebugText = null;
        mRepositioning = false;
        mBodyPartTransform = GetComponent<Transform>();
        mBodynodes = mMainPlayer.mMainBodynodes;

        Debug.Log("mBodynodes = " + mBodynodes);

        mOffsetQuat = new Quaternion(0, 0, 0, 0);
        mReadQuat = new Quaternion(0, 0, 0, 0);
        mTargetQuat = new Quaternion(0, 0, 0, 0);

        mStartQuat = new Quaternion(
            mBodyPartTransform.rotation.x,
            mBodyPartTransform.rotation.y,
            mBodyPartTransform.rotation.z,
            mBodyPartTransform.rotation.w);
        mReceivingMessages = false;

    }

    // Update is called once per frame
    void Update()
    {
        performQuatAction();
    }

    void LateUpdate()
    {
        gotoTargetQuat();
    }

    void TriggerRepositioning(int seconds)
    {
        if (!mRepositioning)
        {
            StartCoroutine(SetOffsetStart(seconds));
        }
    }

    WaitForSeconds wait1sec = new WaitForSeconds(1);

    IEnumerator SetOffsetStart(int seconds)
    {
        mRepositioning = true;
        for (int i = seconds; i > 0; i--)
        {
            yield return wait1sec;
        }

        mOffsetQuat = Quaternion.Inverse(mReadQuat);
        mRepositioning = false;
    }

    private float timeToRotate = 0;

    private void gotoTargetQuat()
    {
        if (!mReceivingMessages)
        {
            return;
        }

        //Debug.Log ("mTargetQuar " + mBodyPart + " -> " + mTargetQuat.w + "|" + mTargetQuat.x + "|" + mTargetQuat.y+ "|" + mTargetQuat.z);

        //mBodyPartTransform.rotation = Quaternion.Euler(mTargetAngle);
        //mBodyPartTransform.localRotation = Quaternion.Euler(mTargetAngle);

        //mBodyPartTransform.rotation = mTargetQuat;
        if (Time.fixedTime >= timeToRotate)
        {
            // Do your thing
            timeToRotate = Time.fixedTime + 0.060f;

            mBodyPartTransform.SetPositionAndRotation(
                mBodyPartTransform.position,
                Quaternion.Slerp(mBodyPartTransform.rotation, mTargetQuat, 0.7f)
            );
            /*
			mBodyPartTransform.SetPositionAndRotation (
				mBodyPartTransform.position,
				mTargetQuat
			);
			*/
        }
    }

    public void resetPosition()
    {
        mOffsetQuat = new Quaternion(0, 0, 0, 0);
        mBodyPartTransform.rotation = mStartQuat;
    }
    
    private string[] values;

    private void performQuatAction()
    {
        float[] values = new float[4];
        bool something = mBodynodes.getMessageValue(BodynodesConstants.PLAYER_DEFAULT_VALUE_TAG, mBodyPart, BodynodesConstants.MESSAGE_SENSORTYPE_ORIENTATION_ABS_TAG, values);
        if (!something)
        {
            return;
        }
        Debug.Log(mBodyPart + " values.Length = "+ values.Length);
        Debug.Log(mBodyPart + " values = " + values[0] + ", " + values[1] + ", " + values[2] + ", " + values[3]);

        mReceivingMessages = true;
        float w = values[0];
        float x = values[1];
        float y = values[2];
        float z = values[3];

        float new_w = w;
        float new_x = x;
        float new_y = y;
        float new_z = z;
        if (mMainPlayer.getAxisVal('x') == 'x')
        {
            new_x = x;
        }
        else if (mMainPlayer.getAxisVal('x') == 'y')
        {
            new_x = y;
        }
        else if (mMainPlayer.getAxisVal('x') == 'z')
        {
            new_x = z;
        }
        else if (mMainPlayer.getAxisVal('x') == 'w')
        {
            new_x = w;
        }

        if (mMainPlayer.getAxisVal('y') == 'x')
        {
            new_y = x;
        }
        else if (mMainPlayer.getAxisVal('y') == 'y')
        {
            new_y = y;
        }
        else if (mMainPlayer.getAxisVal('y') == 'z')
        {
            new_y = z;
        }
        else if (mMainPlayer.getAxisVal('y') == 'w')
        {
            new_y = w;
        }

        if (mMainPlayer.getAxisVal('z') == 'x')
        {
            new_z = x;
        }
        else if (mMainPlayer.getAxisVal('z') == 'y')
        {
            new_z = y;
        }
        else if (mMainPlayer.getAxisVal('z') == 'z')
        {
            new_z = z;
        }
        else if (mMainPlayer.getAxisVal('z') == 'w')
        {
            new_z = w;
        }

        if (mMainPlayer.getAxisVal('w') == 'x')
        {
            new_w = x;
        }
        else if (mMainPlayer.getAxisVal('w') == 'y')
        {
            new_w = y;
        }
        else if (mMainPlayer.getAxisVal('w') == 'z')
        {
            new_w = z;
        }
        else if (mMainPlayer.getAxisVal('w') == 'w')
        {
            new_w = w;
        }

        if (mMainPlayer.getAxisSign('x') == '-')
        {
            new_x = -new_x;
        }
        if (mMainPlayer.getAxisSign('y') == '-')
        {
            new_y = -new_y;
        }
        if (mMainPlayer.getAxisSign('z') == '-')
        {
            new_z = -new_z;
        }
        if (mMainPlayer.getAxisSign('w') == '-')
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

    public void HapticFeedback()
    {
        Debug.Log("BodynodeControllerX - HapticFeedback");
        JObject action = new JObject();
        action[BodynodesConstants.ACTION_PLAYER_TAG] = BodynodesConstants.PLAYER_DEFAULT_VALUE_TAG;
        action[BodynodesConstants.ACTION_BODYPART_TAG ] = mBodyPart;
        action["duration_ms"] = "250";
        action["strength"] = "200";
        mBodynodes.addAction(action);
    }
}
