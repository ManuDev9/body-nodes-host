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

using System.Net;
using System;
using UnityEngine;
using Newtonsoft.Json.Linq;
using System.Linq;
using UnityEditor;

namespace BodynodesDev
{
    public class BnDatatypes
    {
        public static uint MAX_RECEIVED_BYTES_LENGTH = 150;

        public struct BnType
        {
            public string value;

            internal void setFromString(string type)
            {
                // SENSORTYPE
                if (BnConstants.SENSORTYPE_NONE_TAG.Equals(type))
                {
                    value = BnConstants.SENSORTYPE_NONE_TAG;
                }
                else if (BnConstants.SENSORTYPE_ORIENTATION_ABS_TAG.Equals(type))
                {
                    value = BnConstants.SENSORTYPE_ORIENTATION_ABS_TAG;
                }
                else if (BnConstants.SENSORTYPE_ACCELERATION_REL_TAG.Equals(type))
                {
                    value = BnConstants.SENSORTYPE_ACCELERATION_REL_TAG;
                }
                else if (BnConstants.SENSORTYPE_GLOVE_TAG.Equals(type))
                {
                    value = BnConstants.SENSORTYPE_GLOVE_TAG;
                }
                else if (BnConstants.SENSORTYPE_SHOE_TAG.Equals(type))
                {
                    value = BnConstants.SENSORTYPE_SHOE_TAG;
                }
            }
        }

        public struct BnBodypart
        {
            public String value;

            internal void setFromString(string bodypart)
            {
                if (BnConstants.BODYPART_NONE_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_NONE_TAG;
                }
                else if (BnConstants.BODYPART_HEAD_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_HEAD_TAG;
                }
                else if (BnConstants.BODYPART_HAND_LEFT_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_HAND_LEFT_TAG;
                }
                else if (BnConstants.BODYPART_LOWERARM_LEFT_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_LOWERARM_LEFT_TAG;
                }
                else if (BnConstants.BODYPART_UPPERARM_LEFT_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_UPPERARM_LEFT_TAG;
                }
                else if (BnConstants.BODYPART_BODY_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_BODY_TAG;
                }
                else if (BnConstants.BODYPART_LOWERARM_RIGHT_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_LOWERARM_RIGHT_TAG;
                }
                else if (BnConstants.BODYPART_UPPERARM_RIGHT_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_UPPERARM_RIGHT_TAG;
                }
                else if (BnConstants.BODYPART_HAND_RIGHT_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_HAND_RIGHT_TAG;
                }
                else if (BnConstants.BODYPART_LOWERLEG_LEFT_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_LOWERLEG_LEFT_TAG;
                }
                else if (BnConstants.BODYPART_UPPERLEG_LEFT_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_UPPERLEG_LEFT_TAG;
                }
                else if (BnConstants.BODYPART_FOOT_LEFT_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_FOOT_LEFT_TAG;
                }
                else if (BnConstants.BODYPART_LOWERLEG_RIGHT_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_LOWERLEG_RIGHT_TAG;
                }
                else if (BnConstants.BODYPART_UPPERLEG_RIGHT_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_UPPERLEG_RIGHT_TAG;
                }
                else if (BnConstants.BODYPART_FOOT_RIGHT_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_FOOT_RIGHT_TAG;
                }
                else if (BnConstants.BODYPART_UPPERBODY_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_UPPERBODY_TAG;
                }
                else if (BnConstants.BODYPART_LOWERBODY_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_LOWERBODY_TAG;
                }
                else if (BnConstants.BODYPART_KATANA_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_KATANA_TAG;
                }
                else if (BnConstants.BODYPART_UNTAGGED_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_UNTAGGED_TAG;
                }
                else if (BnConstants.BODYPART_ALL_TAG.Equals(bodypart))
                {
                    value = BnConstants.BODYPART_ALL_TAG;
                }
            }
        }

        public struct BnName
        {
            public String value;
        }



        class BnIPConnectionData
        {
            public void setDisconnected()
            {
                conn_status = BnConstants.CONNECTION_STATUS_NOT_CONNECTED;
            }
            public void setWaitingACK()
            {
                conn_status = BnConstants.CONNECTION_STATUS_WAITING_ACK;
            }
            public void setConnected()
            {
                conn_status = BnConstants.CONNECTION_STATUS_CONNECTED;
            }
            public bool isWaitingACK()
            {
                return conn_status == BnConstants.CONNECTION_STATUS_WAITING_ACK;
            }

            public bool isDisconnected()
            {
                return conn_status == BnConstants.CONNECTION_STATUS_NOT_CONNECTED;
            }
            public bool isConnected()
            {
                return conn_status == BnConstants.CONNECTION_STATUS_CONNECTED;
            }
            public void cleanBytes()
            {
                num_received_bytes = 0;
            }

            uint conn_status = BnConstants.CONNECTION_STATUS_NOT_CONNECTED;
#if __WIFI_NODES && (__BUILD_WINDOWS_PC || __BUILD_ANDROID || UNITY_EDITOR)
            IPEndPoint ip_address;
#endif //__WIFI_NODES && ( __BUILD_WINDOWS_PC || __BUILD_ANDROID || UNITY_EDITOR )
            bool has_ip_address;

            byte[] received_bytes = new byte[MAX_RECEIVED_BYTES_LENGTH];
            uint num_received_bytes = 0;

            ulong last_sent_time = 0;
            ulong last_rec_time = 0;
        }

        public class BnSensorData
        {
            public void setValues(float[] values, BnType sensortype)
            {
                sd_num_values = 0;
                if (sensortype.value == BnConstants.SENSORTYPE_ORIENTATION_ABS_TAG)
                {
                    sd_sensortype.value = sensortype.value;
                    sd_num_values = 4;
                }
                else if (sensortype.value == BnConstants.SENSORTYPE_ACCELERATION_REL_TAG)
                {
                    sd_sensortype.value = sensortype.value;
                    sd_num_values = 3;
                }
                sd_values_float = new float[sd_num_values];
                for (uint index = 0; index < sd_num_values; ++index)
                {
                    sd_values_float[index] = values[index];
                }
            }

            public void setValues(Int32[] values, BnType sensortype)
            {
                sd_num_values = 0;
                if (sensortype.value == BnConstants.SENSORTYPE_GLOVE_TAG)
                {
                    sd_num_values = 9;
                    sd_sensortype = sensortype;
                }
                else if (sensortype.value == BnConstants.SENSORTYPE_SHOE_TAG)
                {
                    sd_num_values = 1;
                    sd_sensortype.value = sensortype.value;
                }
                sd_values_int = new Int32[sd_num_values];
                for (uint index = 0; index < sd_num_values; ++index)
                {
                    sd_values_int[index] = values[index];
                }
            }

            public void setValues(String valuesStr, BnType sensortype)
            {
                sd_num_values = 0;
                if (sensortype.value == BnConstants.SENSORTYPE_ORIENTATION_ABS_TAG)
                {
                    sd_sensortype.value = sensortype.value;
                    sd_num_values = 4;
                }
                else if (sensortype.value == BnConstants.SENSORTYPE_ACCELERATION_REL_TAG)
                {
                    sd_sensortype.value = sensortype.value;
                    sd_num_values = 3;
                }
                sd_values_str = valuesStr;
            }

            public float[] getValuesFloat()
            {
                return sd_values_float;
            }

            public Int32[] getValuesInt()
            {
                return sd_values_int;
            }

            public String getValuesStr()
            {
                return sd_values_str;
            }

            public BnType getType()
            {
                return sd_sensortype;
            }

            public bool isEmpty()
            {
                return sd_sensortype.value == BnConstants.SENSORTYPE_NONE_TAG;
            }

            private uint sd_num_values = 0;
            private BnType sd_sensortype = new BnType { value = BnConstants.SENSORTYPE_NONE_TAG };
            private float[] sd_values_float;
            private Int32[] sd_values_int;
            private String sd_values_str;
        };

        public class BnMessage
        {
            public void create(BnName player, BnBodypart bodypart, BnSensorData sensorData)
            {
                m_player = player;
                m_bodypart = bodypart;
                m_sensorData = sensorData;
            }

            public void print()
            {
                String debugStr = "";
                debugStr += "Message = { ";
                debugStr += " player = ";
                debugStr += m_player.value;
                debugStr += " , ";
                debugStr += " bodypart = ";
                debugStr += m_bodypart.value;
                debugStr += " , ";
                debugStr += " value = ";
                if (m_sensorData.getType().value == BnConstants.SENSORTYPE_ORIENTATION_ABS_TAG)
                {
                    float[] values = m_sensorData.getValuesFloat();
                    debugStr += values[0];
                    debugStr += " ";
                    debugStr += values[1];
                    debugStr += " ";
                    debugStr += values[2];
                    debugStr += " ";
                    debugStr += values[3];
                }
                else if (m_sensorData.getType().value == BnConstants.SENSORTYPE_ACCELERATION_REL_TAG)
                {
                    float[] values = m_sensorData.getValuesFloat();
                    debugStr += values[0];
                    debugStr += " ";
                    debugStr += values[1];
                    debugStr += " ";
                    debugStr += values[2];
                }
                else if (m_sensorData.getType().value == BnConstants.SENSORTYPE_GLOVE_TAG)
                {
                    Int32[] values = m_sensorData.getValuesInt();
                    debugStr += values[0];
                    debugStr += " ";
                    debugStr += values[1];
                    debugStr += " ";
                    debugStr += values[2];
                    debugStr += " ";
                    debugStr += values[3];
                    debugStr += " ";
                    debugStr += values[4];
                    debugStr += " ";
                    debugStr += values[5];
                    debugStr += " ";
                    debugStr += values[6];
                    debugStr += " ";
                    debugStr += values[7];
                    debugStr += " ";
                    debugStr += values[8];
                }
                else if (m_sensorData.getType().value == BnConstants.SENSORTYPE_SHOE_TAG)
                {
                    Int32[] values = m_sensorData.getValuesInt();
                    debugStr += values[0];
                }
                debugStr += " }";
                Debug.Log(debugStr);
            }

            public void parseString(String messageStr)
            {
                JObject messageJson = JObject.Parse(messageStr);
                m_player.value =  messageJson[BnConstants.MESSAGE_PLAYER_TAG].ToString();
                m_bodypart.value = messageJson[BnConstants.MESSAGE_BODYPART_TAG].ToString();
                BnType sensortype = new BnType{ value = messageJson[BnConstants.MESSAGE_SENSORTYPE_TAG].ToString() };

                String messageValueStr = messageJson[BnConstants.MESSAGE_VALUE_TAG].ToString();
                if (BnConstants.MESSAGE_VALUE_RESET_TAG.Equals(messageValueStr))
                {
                    m_sensorData.setValues(BnConstants.MESSAGE_VALUE_RESET_TAG, sensortype);
                }
                else if( BnConstants.SENSORTYPE_GLOVE_TAG.Equals( sensortype.value ) )
                {
                    m_sensorData.setValues(messageJson[BnConstants.MESSAGE_VALUE_TAG].ToObject<Int32[]>(), sensortype);
                }
                else 
                {
                    m_sensorData.setValues(messageJson[BnConstants.MESSAGE_VALUE_TAG].ToObject<float[]>(), sensortype);
                }

            }

            public BnName getPlayer()
            {
                return m_player;
            }

            public BnBodypart getBodypart()
            {
                return m_bodypart;
            }

            public BnSensorData getData()
            {
                return m_sensorData;
            }

            public bool isOrientationAbsReset()
            {
                if (BnConstants.MESSAGE_VALUE_RESET_TAG.Equals(m_sensorData.getValuesStr())) { 
                    return true;
                }
                return false;
            }

            private BnName m_player = new BnName { value = BnConstants.PLAYER_NONE_TAG };
            private BnBodypart m_bodypart = new BnBodypart { value = BnConstants.BODYPART_NONE_TAG };
            private BnSensorData m_sensorData = new BnSensorData();
        };

        public class BnAction
        {
            public BnAction()
            {
                a_json = new JObject();
                a_json.Add(BnConstants.ACTION_TYPE_TAG, BnConstants.ACTION_TYPE_NONE_TAG);
                a_json.Add(BnConstants.ACTION_PLAYER_TAG, BnConstants.PLAYER_NONE_TAG);
                a_json.Add(BnConstants.ACTION_BODYPART_TAG, BnConstants.BODYPART_NONE_TAG);
            }

            public void createHaptic(BnName player, BnBodypart bodypart, ushort duration_ms, ushort strength)
            {
                a_json = new JObject();
                a_json.Add(BnConstants.ACTION_TYPE_TAG, BnConstants.ACTION_TYPE_HAPTIC_TAG);
                a_json.Add(BnConstants.ACTION_PLAYER_TAG, player.value);
                a_json.Add(BnConstants.ACTION_BODYPART_TAG, bodypart.value);
                a_json.Add(BnConstants.ACTION_HAPTIC_DURATION_MS_TAG, duration_ms);
                a_json.Add(BnConstants.ACTION_HAPTIC_STRENGTH_TAG, strength);
            }

            public void createSetPlayer(BnName player, BnBodypart bodypart, BnName new_player)
            {
                a_json = new JObject();
                a_json.Add(BnConstants.ACTION_TYPE_TAG, BnConstants.ACTION_TYPE_SETPLAYER_TAG);
                a_json.Add(BnConstants.ACTION_PLAYER_TAG, player.value);
                a_json.Add(BnConstants.ACTION_BODYPART_TAG, bodypart.value);
                a_json.Add(BnConstants.ACTION_SETPLAYER_NEWPLAYER_TAG, new_player.value);
            }

            public void createSetBodypart(BnName player, BnBodypart bodypart, BnBodypart new_bodypart)
            {
                a_json = new JObject();
                a_json.Add(BnConstants.ACTION_TYPE_TAG, BnConstants.ACTION_TYPE_SETBODYPART_TAG);
                a_json.Add(BnConstants.ACTION_PLAYER_TAG, player.value);
                a_json.Add(BnConstants.ACTION_BODYPART_TAG, bodypart.value);
                a_json.Add(BnConstants.ACTION_SETBODYPART_NEWBODYPART_TAG, new_bodypart.value);
            }

            public void createEnableSensor(BnName player, BnBodypart bodypart, BnType sensortype, bool toEnable)
            {
                a_json = new JObject();
                a_json.Add(BnConstants.ACTION_TYPE_TAG, BnConstants.ACTION_TYPE_ENABLESENSOR_TAG);
                a_json.Add(BnConstants.ACTION_PLAYER_TAG, player.value);
                a_json.Add(BnConstants.ACTION_BODYPART_TAG, bodypart.value);
                a_json.Add(BnConstants.ACTION_ENABLESENSOR_SENSORTYPE_TAG, bodypart.value);
                a_json.Add(BnConstants.ACTION_ENABLESENSOR_ENABLE_TAG, toEnable);
            }

            public String getString()
            {
                return a_json.ToString();
            }

            public bool isEmpty()
            {
                if (BnConstants.PLAYER_NONE_TAG.Equals(a_json[BnConstants.ACTION_PLAYER_TAG].ToString()))
                {
                    return true;
                }
                else
                {
                    return false;
                }
            }

            public BnType getType()
            {

                return new BnType { value = a_json[BnConstants.ACTION_TYPE_TAG].ToString() };
            }

            public BnBodypart getBodypart()
            {
                return new BnBodypart { value = a_json[BnConstants.ACTION_BODYPART_TAG].ToString() };
            }

            public BnName getPlayer()
            {
                return new BnName { value = a_json[BnConstants.ACTION_PLAYER_TAG].ToString() };
            }

            public void parseString(String actionStr) {
                a_json = JObject.Parse(actionStr);
            }

            public string ToString()
            {
                string printString = a_json.ToString();
                return printString;
            }
            public void print()
            {
                Debug.Log(ToString());
            }

            private JObject a_json = null;

        };
    }
}
