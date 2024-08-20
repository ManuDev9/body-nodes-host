/**
* MIT License
* 
* Copyright (c) 2024 Manuel Bottini
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

using System.Collections;
using System.Collections.Generic;
using UnityEngine;

#if __BODYNODES_DEV
using BodynodesDev;
#elif __BODYNODES_P
using BodynodesP;
#else
#error "You need to set up the preprocessing environment flag in Unity: 'File' -> 'Buil Settings' -> 'Player Settings' -> 'Player' -> 'Script Compilation'. Click on + and then add __BODYNODES_P or __BODYNODES_DEV, depending if you you want an prod or dev environment"
#endif

public class BodynodesHostCommunicator : MonoBehaviour
{
    public TextMesh mDebugText = null;

#if __BODYNODES_DEV
    private BodynodesDev.BodynodesHostCommunicator mHostCommunicator = new BodynodesDev.BodynodesHostCommunicator();
#elif __BODYNODES_P
    private BodynodesP.BodynodesHostCommunicatorP mHostCommunicator = new BodynodesP.BodynodesHostCommunicator();
#endif
    public BodynodesHostInterface getInternalHostCommunicator()
    {
        return mHostCommunicator.getInternalHostCommunicator();
    }

    // Use this for initialization
    //Called before Start() of all the other objects
    void Awake()
    {
        mHostCommunicator.mDebugText = mDebugText;
        mHostCommunicator.Awake();
    }

    public void addAction(BnDatatypes.BnAction action)
    {
        mHostCommunicator.addAction(action);
    }

    public void setHostName(string name)
    {
        mHostCommunicator.setHostName(name);
    }

    // Update is called once per frame
    void Update()
    {
        mHostCommunicator.Update();
    }

    void OnDestroy()
    {
        mHostCommunicator.OnDestroy();
    }

    public string anyNodeRequesting()
    {
        return mHostCommunicator.anyNodeRequesting();
    }

    public void acceptNodeRequesting(string identifier)
    {
        mHostCommunicator.acceptNodeRequesting(identifier);
    }
}
