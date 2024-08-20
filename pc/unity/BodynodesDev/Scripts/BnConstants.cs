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

namespace BodynodesDev
{
    class BnConstants
    {
        public static string PLAYER_DEFAULT_VALUE_TAG = "playerone";
        public static string PLAYER_ALL_TAG = "all";
        public static string PLAYER_NONE_TAG = "none";

        public static string ACTION_PLAYER_TAG              = "player";
        public static string ACTION_BODYPART_TAG            = "bodypart";
        public static string ACTION_TYPE_TAG                = "type";

        public static string ACTION_TYPE_NONE_TAG           = "none";
        public static string ACTION_TYPE_HAPTIC_TAG         = "haptic";
        public static string ACTION_TYPE_SETPLAYER_TAG      = "set_player";
        public static string ACTION_TYPE_SETBODYPART_TAG    = "set_bodypart";
        public static string ACTION_TYPE_ENABLESENSOR_TAG   = "enable_sensor";
        public static string ACTION_TYPE_SETWIFI_TAG        = "set_wifi";

        public static string ACTION_HAPTIC_DURATION_MS_TAG          = "duration_ms";
        public static string ACTION_HAPTIC_STRENGTH_TAG             = "strength";
        public static string ACTION_SETPLAYER_NEWPLAYER_TAG         = "new_player";
        public static string ACTION_SETBODYPART_NEWBODYPART_TAG     = "new_bodypart";
        public static string ACTION_ENABLESENSOR_SENSORTYPE_TAG     = "sensortype";
        public static string ACTION_ENABLESENSOR_ENABLE_TAG         = "enable";
        public static string ACTION_SETWIFI_SSID_TAG                = "ssid";
        public static string ACTION_SETWIFI_PASSWORD_TAG            = "password";
        public static string ACTION_SETWIFI_MULTICASTMESSAGE_TAG    = "multicast_message";


        public static string MESSAGE_PLAYER_TAG             = "player";
        public static string MESSAGE_BODYPART_TAG           = "bodypart";
        public static string MESSAGE_SENSORTYPE_TAG         = "sensortype";
        public static string MESSAGE_VALUE_TAG              = "value";
        public static string MESSAGE_VALUE_RESET_TAG        = "reset";

        // SENSOR TYPE
        public static string SENSORTYPE_NONE_TAG                = "none";
        public static string SENSORTYPE_ORIENTATION_ABS_TAG     = "orientation_abs";
        public static string SENSORTYPE_ACCELERATION_REL_TAG    = "acceleration_rel";
        public static string SENSORTYPE_GLOVE_TAG               = "glove";
        public static string SENSORTYPE_SHOE_TAG                = "shoe";

        public static string BODYPART_NONE_TAG                  = "none";
        public static string BODYPART_HEAD_TAG                  = "head";
        public static string BODYPART_HAND_LEFT_TAG             = "hand_left";
        public static string BODYPART_LOWERARM_LEFT_TAG         = "lowerarm_left";
        public static string BODYPART_UPPERARM_LEFT_TAG         = "upperarm_left";
        public static string BODYPART_BODY_TAG                  = "body";
        public static string BODYPART_LOWERARM_RIGHT_TAG        = "lowerarm_right";
        public static string BODYPART_UPPERARM_RIGHT_TAG        = "upperarm_right";
        public static string BODYPART_HAND_RIGHT_TAG            = "hand_right";
        public static string BODYPART_LOWERLEG_LEFT_TAG         = "lowerleg_left";
        public static string BODYPART_UPPERLEG_LEFT_TAG         = "upperleg_left";
        public static string BODYPART_FOOT_LEFT_TAG             = "foot_left";
        public static string BODYPART_LOWERLEG_RIGHT_TAG        = "lowerleg_right";
        public static string BODYPART_UPPERLEG_RIGHT_TAG        = "upperleg_right";
        public static string BODYPART_FOOT_RIGHT_TAG            = "foot_right";
        public static string BODYPART_UPPERBODY_TAG             = "upperbody";
        public static string BODYPART_LOWERBODY_TAG             = "lowerbody";
        public static string BODYPART_KATANA_TAG                = "katana";
        public static string BODYPART_UNTAGGED_TAG              = "untagged";
        public static string BODYPART_ALL_TAG                   = "all";



        // COMMUNICATOR STATUS
        public static uint CONNECTION_STATUS_NOT_CONNECTED = 1;
        public static uint CONNECTION_STATUS_WAITING_ACK = 2;
        public static uint CONNECTION_STATUS_CONNECTED = 3;


        // Wifi
        public static int BODYNODES_PORT = 12345;
        public static int BODYNODES_MULTICAST_PORT = 12346;
        public static string BODYNODES_MULTICASTGROUP_DEFAULT = "239.192.1.99";
        public static string BODYNODES_MULTICASTMESSAGE_DEFAULT = "BN";
    }
}