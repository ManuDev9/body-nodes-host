/**
 * MIT License
 *
 * Copyright (c) 2019-2025 Manuel Bottini
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

package eu.bodynodesdev.host;

import android.util.Log;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;

import eu.bodynodesdev.common.BnConstants;

public class BnUtils {

    private final static String TAG = "BnUtils";

    public static float convertBytesToFloat(byte[] value_bytes, int from){
        byte[] partial_value_bytes = Arrays.copyOfRange(value_bytes, from, from + 4);
        return ByteBuffer.wrap(partial_value_bytes).order(ByteOrder.BIG_ENDIAN).getFloat();
    }


    public static JSONObject createJsonMessageFromBLEChara (  String charaUUID, byte[] valuesBytes  ){
        JSONObject jsonMessage = new JSONObject();

        try {
            if (BnConstants.BLE_CHARA_ORIENTATION_ABS_VALUE_UUID.equalsIgnoreCase(charaUUID)) {
                float[] values_float = new float[4];
                values_float[0] = convertBytesToFloat(valuesBytes, 0);
                values_float[1] = convertBytesToFloat(valuesBytes, 4);
                values_float[2] = convertBytesToFloat(valuesBytes, 8);
                values_float[3] = convertBytesToFloat(valuesBytes, 12);
                jsonMessage.put(BnConstants.MESSAGE_SENSORTYPE_TAG, BnConstants.SENSORTYPE_ORIENTATION_ABS_TAG);
                JSONArray jsonArray = new JSONArray();
                for (float value : values_float) {
                    jsonArray.put(value);
                }
                jsonMessage.put(BnConstants.MESSAGE_VALUE_TAG, jsonArray);
            } else if (BnConstants.BLE_CHARA_ACCELERATION_REL_VALUE_UUID.equalsIgnoreCase(charaUUID)) {
                float[] values_float = new float[3];
                values_float[0] = convertBytesToFloat(valuesBytes, 0);
                values_float[1] = convertBytesToFloat(valuesBytes, 4);
                values_float[2] = convertBytesToFloat(valuesBytes, 8);
                jsonMessage.put(BnConstants.MESSAGE_SENSORTYPE_TAG, BnConstants.SENSORTYPE_ACCELERATION_REL_TAG);
                JSONArray jsonArray = new JSONArray();
                for (float value : values_float) {
                    jsonArray.put(value);
                }
                jsonMessage.put(BnConstants.MESSAGE_VALUE_TAG, jsonArray);
            } else if (BnConstants.BLE_CHARA_ANGULARVELOCITY_REL_VALUE_UUID.equalsIgnoreCase(charaUUID)) {
                float[] values_float = new float[3];
                values_float[0] = convertBytesToFloat(valuesBytes, 0);
                values_float[1] = convertBytesToFloat(valuesBytes, 4);
                values_float[2] = convertBytesToFloat(valuesBytes, 8);
                jsonMessage.put(BnConstants.MESSAGE_SENSORTYPE_TAG, BnConstants.SENSORTYPE_ANGULARVELOCITY_REL_TAG);
                JSONArray jsonArray = new JSONArray();
                for (float value : values_float) {
                    jsonArray.put(value);
                }
                jsonMessage.put(BnConstants.MESSAGE_VALUE_TAG, jsonArray);
            } else if(BnConstants.BLE_CHARA_GLOVE_VALUE_UUID.equalsIgnoreCase(charaUUID)){
                int[] values_int = new int[9];
                values_int[0] = valuesBytes[0];
                values_int[1] = valuesBytes[1];
                values_int[2] = valuesBytes[2];
                values_int[3] = valuesBytes[3];
                values_int[4] = valuesBytes[4];
                values_int[5] = valuesBytes[5] & 0x1;
                values_int[6] = valuesBytes[6] & 0x1;
                values_int[7] = valuesBytes[7] & 0x1;
                values_int[8] = valuesBytes[8] & 0x1;
                jsonMessage.put(BnConstants.MESSAGE_SENSORTYPE_TAG, BnConstants.SENSORTYPE_GLOVE_TAG);
                JSONArray jsonArray = new JSONArray();
                for (int value : values_int) {
                    jsonArray.put(value);
                }
                jsonMessage.put(BnConstants.MESSAGE_VALUE_TAG, jsonArray);
            } else if(BnConstants.BLE_CHARA_SHOE_UUID.equalsIgnoreCase(charaUUID)){
                jsonMessage.put(BnConstants.MESSAGE_SENSORTYPE_TAG, BnConstants.SENSORTYPE_SHOE_TAG);
                JSONArray jsonArray = new JSONArray();
                jsonArray.put(valuesBytes[0]);
                jsonMessage.put(BnConstants.MESSAGE_VALUE_TAG,jsonArray );
            }
        } catch (JSONException e) {
            // Return an empty json if something failed
            Log.e(TAG, "Couldn't create the json, "+ e);
            jsonMessage = new JSONObject();
        }

        return jsonMessage;
    }

}
