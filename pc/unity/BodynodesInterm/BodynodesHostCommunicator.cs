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
using DG.Tweening.Core.Easing;
using UnityEngine.SocialPlatforms.Impl;
using System.Security.Cryptography;

#if __BODYNODES_DEV
using BodynodesDev;
using BodynodesDev.Common;
#elif __BODYNODES_P
using BodynodesP;
using BodynodesP.Common;
#else
#error "You need to set up the preprocessing environment flag in Unity: 'File' -> 'Buil Settings' -> 'Player Settings' -> 'Player' -> 'Script Compilation'. Click on + and then add __BODYNODES_P or __BODYNODES_DEV, depending if you you want an prod or dev environment"
#endif

public class BodynodesHostCommunicator
{

#if __BODYNODES_DEV
    private BodynodesDev.BodynodesHostCommunicator mHostCommunicator = new BodynodesDev.BodynodesHostCommunicator();
#elif __BODYNODES_P
    private BodynodesP.BodynodesHostCommunicatorP mHostCommunicator = new BodynodesP.BodynodesHostCommunicator();
#endif

    // The static instance of the class (the singleton)
    private static BodynodesHostCommunicator _instance;

    // Public accessor to get the singleton instance
    public static BodynodesHostCommunicator Instance
    {
        get
        {
            // If the instance hasn't been created yet, create it
            if (_instance == null)
            {
                _instance = new BodynodesHostCommunicator();
            }
            return _instance;
        }
    }

    // Private constructor to prevent instantiation from outside
    private BodynodesHostCommunicator()
    {
    }

    public BodynodesHostInterface getInternalHostCommunicator()
    {
        return mHostCommunicator.getInternalHostCommunicator();
    }

    // Use this for initialization
    //Called before Start() of all the other objects
    public void start(List<string> parameters)
    {
        mHostCommunicator.start(parameters);
    }

    public void addAction(BnDatatypes.BnAction action)
    {
        mHostCommunicator.addAction(action);
    }

    // Update is called once per frame
    public void update()
    {
        mHostCommunicator.update();
    }

    public void stop()
    {
        mHostCommunicator.stop();
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
