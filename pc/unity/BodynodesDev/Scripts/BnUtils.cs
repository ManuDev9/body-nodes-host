/**
* MIT License
* 
* Copyright (c) 2023-2024 Manuel Bottini
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
using System;


namespace BodynodesDev
{

    public class BnUtils
    {

        public static bool doesKeyContainBodypart(string key, string bodypart)
        {
            if (key[0] == bodypart[0] && key[1] == bodypart[1] && key[2] == bodypart[2] && key[3] == bodypart[3])
            {
                return true;
            }
            else
            {
                return false;
            }
        }

        public static bool doesKeyContainPlayer(string key, string player)
        {
            if (key[4] == player[0] && key[5] == player[1] && key[6] == player[2] && key[7] == player[3])
            {
                return true;
            }
            else
            {
                return false;
            }
        }
        // Buf is a 4 bytes char array
        public static string createBodypartKey(BnDatatypes.BnBodypart bodypart)
        {
            return new string(bodypart.value);
        }

        // Buf is a 4 bytes char array
        public static string createPlayerKey(BnDatatypes.BnName player)
        {
            return new string(player.value);
        }

        // Buf is a 8 bytes char array
        public static string createPlayerBodypartKey(BnDatatypes.BnName player, BnDatatypes.BnBodypart bodypart)
        {
            return new string(player.value +"_"+bodypart.value);
        }

        // Buf is a 12 bytes char array
        public static string createPlayerBodypartSensortypeKey(BnDatatypes.BnName player, BnDatatypes.BnBodypart bodypart, BnDatatypes.BnType sensortype)
        {
            return new string(player.value + "_" + bodypart.value + "_"  +sensortype.value);
        }
    }
}