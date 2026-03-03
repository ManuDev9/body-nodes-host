/**
* MIT License
* 
* Copyright (c) 2026 Manuel Bottini
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

using BodynodesDev;
using BodynodesDev.Common;

public interface BodynodesHostInterface
{

    // Starts and initializes the receiver object 
    // Set the name of the host. It can be used to identify itself to the nodes
    void start(List<string> parameters);
    // Stops the receiver
    void stop();

    // Updates the values. Necessary only for the implementations that required optimization
    void update();

    // It returns the message of the requested player bodypart sensortype containing value
    BnDatatypes.BnMessage getMessage(BnDatatypes.BnPlayer player, BnDatatypes.BnBodypart bodypart, BnDatatypes.BnSensorType sensortype);

    // Adds a new action in the queue of actions to be sent
    public void addAction(BnDatatypes.BnAction action);

    // Sends all actions in the queue and clears it
    public void sendAllActions();

    // If any node requesting it returns identifier, otherwise null
    public string? anyNodeRequesting();

    // It accepts the node requesting to connect
    public void acceptNodeRequesting(string identifier);

    // It returns if the host is running or not
    public bool isRunning();

}
