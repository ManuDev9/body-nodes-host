/**
* MIT License
* 
* Copyright (c) 2024-2025 Manuel Bottini
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

using System.Collections.Generic;
using UnityEngine;
using BodynodesDev.Common;

namespace BodynodesDev
{
    public class BodynodesHostCommunicator
    {
        public TextMesh mDebugText = null;

        private BodynodesHostInterface mBodynodesHost = null;

        // Use this for initialization
        //Called before Start() of all the other objects
        public void start(List<string> parameters)
        {
#if __WIFI_NODES
            mBodynodesHost = new UnityWifiHostCommunicator();
#else
#error "You need to set up the preprocessing host communicator type flag and (optionally) platform type in Unity: 'File' -> 'Buil Settings' -> 'Player Settings' -> 'Player' -> 'Script Compilation'. Click on + and then add one of the following combination flags: __WIFI_NODES or __BUILD_WINDOWS_PC"
#endif
            mBodynodesHost.start(parameters);
            mBodynodesHost.setDebugUI(mDebugText);
            Debug.Log("mBodynodesHost = " + mBodynodesHost);
        }

        public BodynodesHostInterface getInternalHostCommunicator()
        {
            return mBodynodesHost;
        }

        public void addAction(BnDatatypes.BnAction action) { 
            mBodynodesHost.addAction(action);
        }

        // Update is called once per frame
        public void update()
        {
            mBodynodesHost.update();
            mBodynodesHost.sendAllActions();
        }

        public void stop()
        {
            if(mBodynodesHost != null)
            {
                mBodynodesHost.stop();
            }
        }

        public string anyNodeRequesting()
        {
            return mBodynodesHost.anyNodeRequesting();
        }

        public void acceptNodeRequesting(string identifier)
        {
            mBodynodesHost.acceptNodeRequesting(identifier);
        }

        public bool isRunning() {
            if (mBodynodesHost != null)
            {
                return mBodynodesHost.isRunning();
            }
            else {
                return false;
            }
        }
    }
}
