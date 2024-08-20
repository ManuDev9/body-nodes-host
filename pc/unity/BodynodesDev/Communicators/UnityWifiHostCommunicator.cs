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

// Implements BodynodesHost Specification Dev 1.0
//#define __WIFI_NODES
using UnityEngine;
using System.Collections.Generic;
using System.Text;
using System;
using Newtonsoft.Json.Linq;

using System.Threading;
using System.Net;
using System.Net.Sockets;

namespace BodynodesDev
{
    public class UnityWifiHostCommunicator : BodynodesHostInterface
    {

        List<BnDatatypes.BnAction> mActionsList = new List<BnDatatypes.BnAction>();
        private Dictionary<string, BnDatatypes.BnMessage> mMessagesMap = new Dictionary<string, BnDatatypes.BnMessage>();
        private Dictionary<string, IPEndPoint> mConnectionsMap = new Dictionary<string, IPEndPoint>();
        private List<string> mAcceptedConnections = new List<string>();
        private object mConnectionMapLock = new object();

        //Here I put all the android dependent code
        private TextMesh mDebugUI = null;

        private Thread mDataConnectionThread = null;
        private Thread mMulticastConnectionThread = null;
        private UdpClient mConnector;
        private UdpClient mMulticastConnector;
        private static IPAddress mMulticastGroupAddress = IPAddress.Parse(BnConstants.BODYNODES_MULTICASTGROUP_DEFAULT);
        private static IPEndPoint mMulticastGroupEndpoint = new IPEndPoint(mMulticastGroupAddress, BnConstants.BODYNODES_MULTICAST_PORT);
        private string mMulticastMessage = null;
        private string mIpRequesting = null;

        private bool mToStop;

        public void start()
        {
            // Start TcpServer background thread 		
            mToStop = false;
            mIpRequesting = null;

            mDataConnectionThread = new Thread(new ThreadStart(run_connection_background));
            mDataConnectionThread.Start();
            mMulticastConnectionThread = new Thread(new ThreadStart(run_multicast_background));
            mMulticastConnectionThread.Start();
        }

        public void stop()
        {
            //nothing to be done
            Debug.Log("Closing sockets");
            mToStop = true;
            mIpRequesting = null;
            mConnector.Close();
            if (mDataConnectionThread != null)
            {
                mDataConnectionThread.Abort();
                mDataConnectionThread = null;
            }
            mMulticastConnector.Close();
            if (mMulticastConnectionThread != null)
            {
                mMulticastConnectionThread.Abort();
                mMulticastConnectionThread = null;
            }
        }

        public void update()
        {
            //nothing to do here
        }

        public void setHostName(string name)
        {
            mMulticastMessage = name;
        }

        void sendACKH(IPEndPoint ipEndpoint)
        {
            Debug.Log("Sending ACKH");
            Byte[] ackResponse = Encoding.ASCII.GetBytes("ACKH");
            mConnector.Send(ackResponse, ackResponse.Length, ipEndpoint);
        }

        void sendMulticastBN()
        {
            if (mMulticastMessage == null)
            {
                return;
            }
            Debug.Log("Sending multicast BN");
            Byte[] bn_bytes = Encoding.ASCII.GetBytes(mMulticastMessage);
            mMulticastConnector.Send(bn_bytes, bn_bytes.Length, mMulticastGroupEndpoint);
        }

        private void run_multicast_background()
        {
            Debug.Log("run_multicast_background starting");
            mMulticastConnector = new UdpClient(BnConstants.BODYNODES_MULTICAST_PORT);
            Debug.Log("mMulticastConnector listening to port " + BnConstants.BODYNODES_MULTICAST_PORT);

            // MulticastOption multicastOption = new MulticastOption(mMulticastGroupAddress);
            // IPAddress group = multicastOption.Group;
            // long interfaceIndex = multicastOption.InterfaceIndex;

#if UNITY_STANDALONE_WIN
            string localIPAddress = GetLocalIPAddress();
            Debug.Log("GetLocalIPAddress() = " + localIPAddress);
            mMulticastConnector.JoinMulticastGroup(mMulticastGroupAddress, IPAddress.Parse(localIPAddress));
#else
            mMulticastConnector.JoinMulticastGroup(mMulticastGroupAddress);
#endif // UNITY_STANDALONE_WIN
            while (!mToStop)
            {
                try
                {
                    //Debug.Log("GetLocalIPAddress() = " + localIPAddress);
                    sendMulticastBN();
                    Thread.Sleep(5000);
                }
                catch (Exception err)
                {
                    Debug.Log(err.ToString());
                }
            }
        }

        private static string GetLocalIPAddress()
        {
            var host = Dns.GetHostEntry(Dns.GetHostName());
            foreach (var ip in host.AddressList)
            {
                if (ip.AddressFamily == AddressFamily.InterNetwork)
                {
                    string ipstring = ip.ToString();
                    if (ipstring.Contains("192.168.0.") || ipstring.Contains("192.168.1.")
                         || ipstring.Contains("192.168.2.") || ipstring.Contains("192.168.3.")
                         || ipstring.Contains("192.168.4.") || ipstring.Contains("192.168.5.")
                         || ipstring.Contains("192.168.6.") || ipstring.Contains("192.168.7.")
                         || ipstring.Contains("192.168.8.") || ipstring.Contains("192.168.9.")
                         || ipstring.Contains("192.168.10.") || ipstring.Contains("192.168.11.")
                         )
                    {
                        return ip.ToString();
                    }
                }
            }
            throw new Exception("No network adapters with an IPv4 address in the system!");
        }

        private void run_connection_background()
        {
            Debug.Log("UdpClient to start");
            mConnector = new UdpClient(BnConstants.BODYNODES_PORT);
            Debug.Log("UdpClient mounted, listening to port " + BnConstants.BODYNODES_PORT);
            while (!mToStop)
            {
                try
                {
                    IPEndPoint anyIP = new IPEndPoint(IPAddress.Any, 0);
                    byte[] received_bytes = mConnector.Receive(ref anyIP);

                    // encode UTF8-coded bytes to text format
                    if (received_bytes.Length == 0) return;
                    //Debug.Log("Receiving from " + anyIP.Address.ToString());

                    // Checking this connection
                    string ipstring = anyIP.Address.ToString();
                    if (!mAcceptedConnections.Contains(ipstring))
                    {
                        if (mIpRequesting == null)
                        {
                            mIpRequesting = ipstring;
                            //Debug.Log("Enabled the request");
                        }
                        else
                        {
                            //Debug.Log("Another request is in progress");
                        }
                        //Debug.Log("This ip has not been accepted yet");
                        continue;
                    }

                    // Check if the byte array contains 'A', 'C', 'K', 'N'
                    if (received_bytes[0] == 65 && received_bytes[1] == 67 &&
                        received_bytes[2] == 75 && received_bytes[3] == 78)
                    {
                        sendACKH(anyIP);
                    }
                    else
                    {
                        string receivedPacket = Encoding.UTF8.GetString(received_bytes);
                        Debug.Log("receivedPacket = "+ receivedPacket);
                        parseMessage(anyIP, receivedPacket);
                    }
                }
                catch (Exception err)
                {
                    Debug.Log(err.ToString());
                }
            }
        }

        void parseMessage(IPEndPoint ipAddress, string messagesStr)
        {
            JArray jsonMessages = JArray.Parse(messagesStr);
            foreach (JObject jsonMessage in jsonMessages)
            {
                BnDatatypes.BnMessage message = new BnDatatypes.BnMessage();
                message.parseString(jsonMessage.ToString());
                //Debug.Log("Datapacket has been parsed");
                //message.print();

                string player_bodypart_key = BnUtils.createPlayerBodypartKey(message.getPlayer(), message.getBodypart());
                string player_bodypart_sensortype_key = BnUtils.createPlayerBodypartSensortypeKey(message.getPlayer(), message.getBodypart(), message.getData().getType());

                //Debug.Log("Setting message for player_bodypart_sensortype_key = " + player_bodypart_sensortype_key);
                //Debug.Log("jsonMessage.ToString() = " + jsonMessage.ToString());
                lock (mConnectionMapLock)
                {
                    mConnectionsMap[player_bodypart_key] = ipAddress;
                }
                mMessagesMap[player_bodypart_sensortype_key] = message;
            }
        }

        public BnDatatypes.BnMessage getMessage(BnDatatypes.BnName player, BnDatatypes.BnBodypart bodypart, BnDatatypes.BnType sensortype)
        {
            string player_bodypart_sensortype_key = BnUtils.createPlayerBodypartSensortypeKey(
                player,
                bodypart,
                sensortype);
            //Debug.Log("Looking for player_bodypart_sensortype_key = " + player_bodypart_sensortype_key);
            if (mMessagesMap.ContainsKey(player_bodypart_sensortype_key))
            {
                BnDatatypes.BnMessage message = mMessagesMap[player_bodypart_sensortype_key];
                mMessagesMap.Remove(player + "_" + bodypart + "_" + sensortype);
                return message;
            }
            return new BnDatatypes.BnMessage();
        }

        public void addAction(BnDatatypes.BnAction action)
        {
            //Debug.Log("Adding action: " + action.ToString());
            mActionsList.Add(action);
        }

        public void sendAllActions()
        {
            lock (mConnectionMapLock)
            {
                /*
                if (mConnectionsMap.Count > 0)
                {
                    string log = "These are the available connections:\n";
                    foreach (string key in mConnectionsMap.Keys)
                    {
                        log += "->" + mConnectionsMap[key].ToString() + "\n";
                    }
                    Debug.Log(log);
                }
                */

                for (int index = mActionsList.Count - 1; index >= 0; --index)
                {
                    BnDatatypes.BnAction action = mActionsList[index];
                    // Collect all the endpoints we wnat to send the action to
                    HashSet<IPEndPoint> listIps = new HashSet<IPEndPoint>();
                    if (action.getPlayer().value == BnConstants.PLAYER_ALL_TAG && action.getBodypart().value == BnConstants.BODYPART_ALL_TAG)
                    {
                        //Debug.Log("Sending action to everything");
                        foreach (string key in mConnectionsMap.Keys)
                        {
                            listIps.Add(mConnectionsMap[key]);
                        }
                    }
                    else if (action.getPlayer().value == BnConstants.PLAYER_ALL_TAG && action.getBodypart().value != BnConstants.BODYPART_ALL_TAG)
                    {
                        string bodypart_key = BnUtils.createBodypartKey(action.getBodypart());
                        //Debug.Log("Sending action to bodypart_key = " + bodypart_key);
                        foreach (string key in mConnectionsMap.Keys)
                        {
                            if (BnUtils.doesKeyContainBodypart(key, bodypart_key))
                            {
                                listIps.Add(mConnectionsMap[key]);
                            }
                        }
                    }
                    else if (action.getPlayer().value != BnConstants.PLAYER_ALL_TAG && action.getBodypart().value == BnConstants.BODYPART_ALL_TAG)
                    {
                        string player_key = BnUtils.createPlayerKey(action.getPlayer());
                        //Debug.Log("Sending action to player_key = " + player_key);
                        foreach (string key in mConnectionsMap.Keys)
                        {
                            if (BnUtils.doesKeyContainPlayer(key, player_key))
                            {
                                listIps.Add(mConnectionsMap[key]);
                            }
                        }
                    }
                    else
                    {
                        string player_bodypart_key = BnUtils.createPlayerBodypartKey(action.getPlayer(), action.getBodypart());
                        Debug.Log("Sending action " + action.ToString() + " to player_bodypart_key = " + player_bodypart_key);
                        if (mConnectionsMap.ContainsKey(player_bodypart_key))
                        {
                            listIps.Add(mConnectionsMap[player_bodypart_key]);
                        }
                        else
                        {
                            Debug.Log("But it doesn't exist");
                        }
                    }
                    if (listIps.Count > 0)
                    {
                        // Let's send to the collected endpoints
                        foreach (IPEndPoint node_ip_address in listIps)
                        {
                            byte[] action_bytes = Encoding.UTF8.GetBytes(action.getString());
                            //Debug.Log("Sending action "+ action.ToString() +" to " + node_ip_address.ToString() + " num_bytes = "+ num_bytes);
                            mConnector.Send(action_bytes, action_bytes.Length, node_ip_address);
                            Thread.Sleep(1);
                        }
                        mActionsList.RemoveAt(index);
                    }
                }
                // mActionsList.Clear();
            }
        }

        public void printLog(string text)
        {
            if (mDebugUI == null)
            {
                Debug.Log(text);
            }
            else
            {
                mDebugUI.text = text;
            }
        }

        public void setDebugUI(TextMesh debugUI)
        {
            mDebugUI = debugUI;
        }

        public string anyNodeRequesting()
        {
            return mIpRequesting;
        }

        public void acceptNodeRequesting(string identifier)
        {
            if (mIpRequesting == identifier)
            {
                mAcceptedConnections.Add(identifier);
                mIpRequesting = null;
                Debug.Log("Id = " + identifier + " got accepted");
            }
            else
            {
                Debug.Log("Another identifer gor accepted id = " + identifier + " mIpRequesting = " + mIpRequesting);
            }
        }
    }
}