/**
* MIT License
* 
* Copyright (c) 2019-2021 Manuel Bottini
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

using Newtonsoft.Json.Linq;
using UnityEngine;

public interface BodynodesHostInterface
{
    //Starts and initializes the receiver object 
    void start();
    //Stops the receiver
    void stop();

    //Updates the values. Necessary only for the implementations that required optimization
    void update();

    // It puts in outvalue the value of the message of the requested player_bodypart_sensortype
    // It also returns true if any value has been read, false otherwise
    bool getMessageValue(string player, string bodypart, string sensortype, float[] outvalue);

    // Adds an action to the queue
    void addAction(JObject action);

    // Sends all the actions in the queue
    void sendAllActions();

    void addDebugger(TextMesh debugUI);
    void printLog(string text);
}

