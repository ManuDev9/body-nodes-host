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

// Implements Dev BodynodesHost Specification 1.0
#define __WIFI_NODES
using UnityEngine;
using System.Collections.Generic;
using System.Text;
using System;
using Newtonsoft.Json.Linq;

#if __WIFI_NODES && ( __BUILD_WINDOWS_PC || __BUILD_ANDROID || UNITY_EDITOR )
using System.Threading;
using System.Net;
using System.Net.Sockets;
#endif //__WIFI_NODES && ( __BUILD_WINDOWS_PC || __BUILD_ANDROID || UNITY_EDITOR )

public class BNIUnityWifi : BodynodesHostInterface
{
 
    private Dictionary<string, string> mMessages = new Dictionary<string, string>();
    List<JObject> mActionsList = new List<JObject>();

#if __WIFI_NODES && (__BUILD_WINDOWS_PC || __BUILD_ANDROID || UNITY_EDITOR)
    private Dictionary<string, IPEndPoint> mIPAddresses = new Dictionary<string, IPEndPoint>();
#endif //__WIFI_NODES && ( __BUILD_WINDOWS_PC || __BUILD_ANDROID || UNITY_EDITOR )

    //Here I put all the android dependent code
    private TextMesh mDebugUI = null;

    public void update()
    {
        //nothing to do here
    }


#if __WIFI_NODES && ( __BUILD_WINDOWS_PC || __BUILD_ANDROID || UNITY_EDITOR )
    private UdpClient mClient;
	private Thread mReceiveDataTh = null;
#endif //__WIFI_NODES && ( __BUILD_WINDOWS_PC || __BUILD_ANDROID || UNITY_EDITOR )

    private bool toStop;
    public void start()
    {

#if __WIFI_NODES && ( __BUILD_WINDOWS_PC || __BUILD_ANDROID || UNITY_EDITOR )
        // Start TcpServer background thread 		
        toStop = false;

        mReceiveDataTh = new Thread(new ThreadStart(receiveBytes));
        mReceiveDataTh.Start();
#endif //__WIFI_NODES && ( __BUILD_WINDOWS_PC || __BUILD_ANDROID || UNITY_EDITOR )
    }

    public void stop()
    {
#if __WIFI_NODES && ( __BUILD_WINDOWS_PC || __BUILD_ANDROID || UNITY_EDITOR )
        //nothing to be done
        Debug.Log("Socket closed");
		mClient.Close ();
		if (mReceiveDataTh != null) {
            mReceiveDataTh.Abort ();
		}
		toStop = true;
#endif //__WIFI_NODES && ( __BUILD_WINDOWS_PC || __BUILD_ANDROID || UNITY_EDITOR )
    }

#if __WIFI_NODES && ( __BUILD_WINDOWS_PC || __BUILD_ANDROID || UNITY_EDITOR )
    void sendACK(IPEndPoint nodeIP)
    {
        Debug.Log("Sending ACK");
        Byte[] ackResponse = Encoding.ASCII.GetBytes("ACK");
        mClient.Send(ackResponse, ackResponse.Length, nodeIP);
    }

    void parseJSON(IPEndPoint ipAddress, JArray jsonMessages)
    {
        foreach (JObject jsonMessage in jsonMessages)
        {
            //Debug.Log("jsonMessage =  " + jsonMessage);
            if (
                jsonMessage[BodynodesConstants.MESSAGE_PLAYER_TAG] == null || 
                jsonMessage[BodynodesConstants.MESSAGE_BODYPART_TAG] == null ||
                jsonMessage[BodynodesConstants.MESSAGE_SENSORTYPE_TAG] == null ||
                jsonMessage[BodynodesConstants.MESSAGE_VALUE_TAG] == null)
            {
                return;
            }
            string player = jsonMessage[BodynodesConstants.MESSAGE_PLAYER_TAG].ToString();
            string bodypart = jsonMessage[BodynodesConstants.MESSAGE_BODYPART_TAG].ToString();
            string sensortype = jsonMessage[BodynodesConstants.MESSAGE_SENSORTYPE_TAG].ToString();
            string valueStr = jsonMessage[BodynodesConstants.MESSAGE_VALUE_TAG].ToString();

            mIPAddresses[player+"_"+bodypart] = ipAddress;
            mMessages[player + "_" + bodypart + "_" + sensortype] = valueStr;
            //Debug.Log("mMessages["+player + "_" + bodypart + "_" + sensortype+"] = " + mMessages[player + "_" + bodypart + "_" + sensortype]);
        }
    }

    private void receiveBytes(){
        Debug.Log("UdpClient to start");
        mClient = new UdpClient(12345);
        Debug.Log("UdpClient mounted, listening to port 12345");
        while (!toStop)
        {
            try
            {
                IPEndPoint anyIP = new IPEndPoint(IPAddress.Any, 0);
                //Debug.Log("Here 1");
                byte[] data = mClient.Receive(ref anyIP);
                // encode UTF8-coded bytes to text format
                string message = Encoding.UTF8.GetString(data);
                if (message == "" || message == null) return;
                Debug.Log("Receiving from" + anyIP.Address.ToString());
                Debug.Log("message = " + message);
                if (message.Contains("ACK"))
                {
                    sendACK(anyIP);
                }
                else
                {
                    JArray jsonMessages = JArray.Parse(message);
                    parseJSON(anyIP, jsonMessages);
                }

            }
            catch (Exception err)
            {
                Debug.Log(err.ToString());
            }
        }
    }
#endif //__WIFI_NODES && ( __BUILD_WINDOWS_PC || __BUILD_ANDROID || UNITY_EDITOR )

    public bool getMessageValue(string player, string bodypart, string sensortype, float[] outvalue)
    {
        //Debug.Log("Looking for " + player + "_" + bodypart + "_" + sensortype);
        if (mMessages.ContainsKey(player + "_" + bodypart + "_" + sensortype))
        {
            //Debug.Log("And found it");
            string valuesStr = mMessages[player + "_" + bodypart + "_" + sensortype];
            string[] valuesArr = valuesStr.Replace('[',' ').Replace(']', ' ').Split(',');
            outvalue[0] = float.Parse(valuesArr[0]);
            outvalue[1] = float.Parse(valuesArr[1]);
            outvalue[2] = float.Parse(valuesArr[2]);
            outvalue[3] = float.Parse(valuesArr[3]);
            mMessages.Remove(player + "_" + bodypart + "_" + sensortype);
            return true;
        }
        return false;
    }

    public void addAction(JObject action)
    {
        mActionsList.Add(action);
    }

    public void sendAllActions()
    {
#if __WIFI_NODES && ( __BUILD_WINDOWS_PC || __BUILD_ANDROID || UNITY_EDITOR )
        foreach (JObject action in mActionsList) {
            string player = action["player"].ToString();
            string bodypart = action["bodypart"].ToString();
            if(mIPAddresses.ContainsKey(player + "_" + bodypart)) 
            {
                IPEndPoint node_ip_address = mIPAddresses[player + "_" + bodypart];
                byte[] buf = Encoding.UTF8.GetBytes(action.ToString().ToCharArray());
                mClient.Send(buf, buf.Length, node_ip_address);
            }
        }
        mActionsList.Clear();
#endif //__WIFI_NODES && ( __BUILD_WINDOWS_PC || __BUILD_ANDROID || UNITY_EDITOR )
    }

    public void addDebugger(TextMesh debugUI)
    {
        mDebugUI = debugUI;
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
}