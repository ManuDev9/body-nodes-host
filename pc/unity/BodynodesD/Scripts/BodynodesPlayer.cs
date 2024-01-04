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

public class BodynodesPlayer : MonoBehaviour
{

    //For this particular game	
    private char new_w_val = 'w';
    private char new_x_val = 'z';
    private char new_y_val = 'y';
    private char new_z_val = 'x';

    private char new_w_sign = '+';
    private char new_x_sign = '+';
    private char new_y_sign = '+';
    private char new_z_sign = '+';

    public void setAxisVal(char game_axis, char sens_axis) {
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

    public BodynodesHostInterface mMainBodynodes;
    public GameObject mInfoText;
    public TextMesh mDebugText = null;

    public bool mIsFirstPerson;

    // Use this for initialization
    //Called before Start() of all the other objects
    void Awake()
    {
        mIsFirstPerson = false;
#if UNITY_EDITOR && __WIFI_NODES
        mMainBodynodes = new BNIUnityWifi();
#elif __BUILD_ANDROID && __WIFI_NODES
        mMainBodynodes = new BNIUnityWifi();
		//mIsFirstPerson = true;
#elif __BUILD_WINDOWS_PC && __WIFI_NODES
        mMainBodynodes = new BNIUnityWifi();
#else
        mMainBodynodes = null; //Let it crash, because it is not a considered case
#endif
        mMainBodynodes.start();
        mMainBodynodes.addDebugger(mDebugText);
        Debug.Log("mMainBodynodes = " + mMainBodynodes);
    }

    // Update is called once per frame
    void Update()
    {
        mMainBodynodes.update();
        mMainBodynodes.sendAllActions();
    }

    void OnDestroy()
    {
        mMainBodynodes.stop();
    }
}
