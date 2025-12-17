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

import android.annotation.SuppressLint;
import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGatt;
import android.bluetooth.BluetoothGattCallback;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattDescriptor;
import android.bluetooth.BluetoothGattService;
import android.bluetooth.BluetoothManager;
import android.bluetooth.BluetoothProfile;
import android.bluetooth.le.BluetoothLeScanner;
import android.bluetooth.le.ScanCallback;
import android.bluetooth.le.ScanFilter;
import android.bluetooth.le.ScanResult;
import android.bluetooth.le.ScanSettings;
import android.content.Context;
import android.os.Handler;
import android.util.Log;
import android.util.Pair;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import eu.bodynodesdev.common.BnConstants;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.function.BiFunction;

@SuppressLint("MissingPermission")
public class BnBLEHostCommunicator extends ScanCallback implements BnHostCommunicator {

    private final static String TAG = "BnBLEHostCommunicator";
    private Activity mActivity;

    private boolean mIsScanning;

    List<Pair<BluetoothGatt, BluetoothGattCharacteristic>> mCharacteristicsToParse = new ArrayList<>();

    private BluetoothLeScanner mBluetoothLeScanner;
    private List<String> mDiscoveredDevices = new ArrayList<>();

    private HashMap<BluetoothGatt, Pair<String, String>> mBLEGatts_PlayerBodypartMap = new HashMap<>();
    private HashMap<String, BluetoothGatt> mPlayerBodypart_BLEGattsMap = new HashMap<>();
    //private HashMap<String, BluetoothGattCharacteristic> mHapticActionCharacteristicsBN = new HashMap<>();

    private HashMap<String, String> mMessagesMap = new HashMap();

    private Handler mHandler = new Handler();
    private Handler mReadCharsHandler = new Handler();

    private static final long SCAN_INTERVAL = 5000;

    public BnBLEHostCommunicator(Activity activity) {
        mActivity = activity;
        final BluetoothManager bluetoothManager = (BluetoothManager) activity.getSystemService(Context.BLUETOOTH_SERVICE);
        final BluetoothAdapter bluetoothAdapter = bluetoothManager.getAdapter();
        mBluetoothLeScanner = bluetoothAdapter.getBluetoothLeScanner();
    }

    public void start() {
        ///Let's trigger a scan and stop it after 10 seconds OR device with mac found
        Log.d(TAG, "Start BLE scan ");

        mIsScanning = false;
        startScan();

    }

    public void stop() {
        Log.d(TAG, "Stop BLE scan ");
        //mHapticActionCharacteristicsBN.clear();
        mCharacteristicsToParse.clear();
        stopScan();
        mHandler.removeCallbacksAndMessages(null);
        for (String playerBodypartKey : mPlayerBodypart_BLEGattsMap.keySet()) {
            BluetoothGatt bleGatt = mPlayerBodypart_BLEGattsMap.get(playerBodypartKey);

            if (bleGatt != null) {
                bleGatt.disconnect();
                bleGatt.close();
            }
        }
        mPlayerBodypart_BLEGattsMap.clear();
    }

    public String getMessage(String player, String bodypart, String sensortype) {
        String playerBodypartSensortypeKey = player +"|"+ bodypart +"|"+ sensortype;
        if (mMessagesMap.containsKey(playerBodypartSensortypeKey)) {
            //Log.d(TAG, "Reading from playerBodypartSensortypeKey = " + playerBodypartSensortypeKey);
            String message = mMessagesMap.get(playerBodypartSensortypeKey);
            if (message != null) {
                return message;
            }
        }
        return "";
    }

    public String getMessages() {
        JSONArray jsonArray = new JSONArray();
        for (Map.Entry<String, String> entry : mMessagesMap.entrySet()) {
            JSONObject jsonObject = new JSONObject();
            String key = entry.getKey();
            String valueStr = entry.getValue();
            //Log.d(TAG, "Reading from playerBodypartSensortypeKey = " + key);
            String[] parts = key.split("\\|");
            try {
                jsonObject.put( BnConstants.MESSAGE_PLAYER_TAG, parts[0] );
                jsonObject.put( BnConstants.MESSAGE_BODYPART_TAG, parts[1] );
                jsonObject.put( BnConstants.MESSAGE_SENSORTYPE_TAG, parts[2] );
                jsonObject.put( BnConstants.MESSAGE_VALUE_TAG, valueStr );
                jsonArray.put(jsonObject);
            } catch (JSONException e) {
                Log.e(TAG, "Cannot create json");
            }

        }
        return jsonArray.toString();
    }

    @Override
    public void sendAction(JSONArray action) {
        Log.w(TAG, "Actions not implemented for BLE communication");
    }

    @Override
    public void onScanResult(int callbackType, ScanResult result) {
        BluetoothDevice bluetoothDevice = result.getDevice();
        //Log.d(TAG,"onLeScan device found name = "+bluetoothDevice.getName());
        if (mDiscoveredDevices.contains(bluetoothDevice.getAddress())) {
            //Log.d(TAG,"onLeScan device already seen");
            return;
        }
        mDiscoveredDevices.add(bluetoothDevice.getAddress());

        if (bluetoothDevice.getName() != null && bluetoothDevice.getName().contains("Bodynode")) {
            Log.d(TAG, "onLeScan device to connect to " + bluetoothDevice.getAddress());
            bluetoothDevice.connectGatt(mActivity, true, mGattCallback);
        }
    }

    private final BluetoothGattCallback mGattCallback = new BluetoothGattCallback() {
        @Override
        public void onConnectionStateChange(BluetoothGatt gatt, int status, int newState) {
            super.onConnectionStateChange(gatt, status, newState);

            if (newState == BluetoothProfile.STATE_CONNECTED) {
                //In this application a connection has a set of new values
                Log.d(TAG, "onConnectionStateChange newState is CONNECTED");
                boolean ans = gatt.discoverServices();
                Log.d(TAG, "Discover Services started: " + ans);
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                Log.d(TAG, "onConnectionStateChange newState is DISCONNECTED");
                boolean reconnect = gatt.connect();
                Log.d(TAG, "Reconnecting: " + reconnect);
            }
        }

        @Override
        // New services discovered
        public void onServicesDiscovered(final BluetoothGatt gatt, int status) {
            super.onServicesDiscovered(gatt, status);
            if (status == BluetoothGatt.GATT_SUCCESS) {
                Log.d(TAG, "onServicesDiscovered we discovered something!");
                for (BluetoothGattService service : gatt.getServices()) {
                    Log.d(TAG, "we discovered service UUID:" + service.getUuid());
                    if (BnConstants.BLE_SERVICE_UUID.equalsIgnoreCase( service.getUuid().toString())) {
                        for (BluetoothGattCharacteristic characteristic : service.getCharacteristics()) {
                            Log.d(TAG, "we discovered characteristic UUID:" + characteristic.getUuid());

                            if (BnConstants.BLE_CHARA_PLAYER_UUID.equalsIgnoreCase( characteristic.getUuid().toString()) ||
                                    BnConstants.BLE_CHARA_BODYPART_UUID.equalsIgnoreCase(characteristic.getUuid().toString()) ||
                                    BnConstants.BLE_CHARA_ORIENTATION_ABS_VALUE_UUID.equalsIgnoreCase(characteristic.getUuid().toString()) ||
                                    BnConstants.BLE_CHARA_ANGULARVELOCITY_REL_VALUE_UUID.equalsIgnoreCase(characteristic.getUuid().toString()) ||
                                    BnConstants.BLE_CHARA_ACCELERATION_REL_VALUE_UUID.equalsIgnoreCase(characteristic.getUuid().toString()) ||
                                    BnConstants.BLE_CHARA_GLOVE_VALUE_UUID.equalsIgnoreCase(characteristic.getUuid().toString()) ||
                                    BnConstants.BLE_CHARA_SHOE_UUID.equalsIgnoreCase(characteristic.getUuid().toString())) {
                                Log.d(TAG, "Adding characteristic to list");
                                mCharacteristicsToParse.add(new Pair<>(gatt, characteristic));
                            }
                        }
                    }
                }

                boolean requestMtuSuccess = gatt.requestMtu(24); // Request an MTU size of 24 bytes
                if (!requestMtuSuccess) {
                    Log.w(TAG, "requestMtu was not successful");
                }
                restartReadNextCharacteristic();
            } else {
                Log.w(TAG, "onServicesDiscovered received: " + status);
            }
        }

        @Override
        public void onCharacteristicRead(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic, int status) {
            super.onCharacteristicRead(gatt, characteristic, status);

            Log.d(TAG, "onCharacteristicRead something has been read from this UUID = " + characteristic.getUuid().toString());
            // Subscribe to the notifications of the characteristic
            String player = null;
            String bodypart = null;
            if( BnConstants.BLE_CHARA_PLAYER_UUID.equalsIgnoreCase(characteristic.getUuid().toString()) ) {
                player = characteristic.getStringValue(0);
                Log.d(TAG, "Player has been read = " + player);
            }

            if( BnConstants.BLE_CHARA_BODYPART_UUID.equalsIgnoreCase(characteristic.getUuid().toString()) ) {
                bodypart = characteristic.getStringValue(0);
                Log.d(TAG, "Bodypart has been read = " + bodypart);
            }

            if(!mBLEGatts_PlayerBodypartMap.containsKey(gatt) ){
                mBLEGatts_PlayerBodypartMap.put(gatt, new Pair<>("",""));
            }

            if( bodypart != null ){
                final String finalBodypart = bodypart;
                mBLEGatts_PlayerBodypartMap.computeIfPresent(gatt, new BiFunction<BluetoothGatt, Pair<String, String>, Pair<String, String>>() {
                    @Override
                    public Pair<String, String> apply(BluetoothGatt k, Pair<String, String> oldPair) {
                        return new Pair<>(oldPair.first, finalBodypart);
                    }
                });
            }
            if( player != null ){
                final String finalPlayer = player;
                mBLEGatts_PlayerBodypartMap.computeIfPresent(gatt, new BiFunction<BluetoothGatt, Pair<String, String>, Pair<String, String>>() {
                    @Override
                    public Pair<String, String> apply(BluetoothGatt k, Pair<String, String> oldPair) {
                        return new Pair<>(finalPlayer, oldPair.second);
                    }
                });
            }

            player = Objects.requireNonNull(mBLEGatts_PlayerBodypartMap.get(gatt)).first;
            bodypart = Objects.requireNonNull(mBLEGatts_PlayerBodypartMap.get(gatt)).second;
            if( !player.isEmpty() && !bodypart.isEmpty() ) {
                String playerBodypartKey = player +"|"+ bodypart;
                if( !mPlayerBodypart_BLEGattsMap.containsKey(playerBodypartKey) ) {
                    mPlayerBodypart_BLEGattsMap.put(playerBodypartKey, gatt);
                }
            }

            parseNextCharacteristic();
        }

        @Override
        public void onCharacteristicChanged(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic) {
            super.onCharacteristicChanged(gatt, characteristic);
            Log.d(TAG, "onCharacteristicChanged something has changed");
            byte[] value = characteristic.getValue();
            if (value != null) {
                StringBuilder hexString = new StringBuilder();
                for (byte b : value) {
                    hexString.append(String.format("%02X", b)).append(",");
                }
                Log.d(TAG, "Change length of value = " + value.length);
                Log.d(TAG, "Change in value = " + hexString);
                Log.d(TAG, "Getting the MAC address = " +  gatt.getDevice().getAddress());
                JSONObject jsonMessage = BnUtils.createJsonMessageFromBLEChara(characteristic.getUuid().toString(), value);
                Log.d(TAG, "Json created = " + jsonMessage.toString());

                String player = Objects.requireNonNull(mBLEGatts_PlayerBodypartMap.get(gatt)).first;
                String bodypart = Objects.requireNonNull(mBLEGatts_PlayerBodypartMap.get(gatt)).second;
                if( player.isEmpty()) {
                    Log.d(TAG, "Gatt device is missing  player = "+player);
                    return;
                }
                if (bodypart.isEmpty() ) {
                    Log.d(TAG, "Gatt device is missing bodypart ="+bodypart);
                    return;
                }

                String sensortype = null;
                String valuesStr = null;

                try {
                    sensortype = jsonMessage.getString(BnConstants.MESSAGE_SENSORTYPE_TAG);
                    valuesStr = jsonMessage.getString(BnConstants.MESSAGE_VALUE_TAG);
                } catch (JSONException e) {
                    Log.d(TAG, "Cannot parse the jsonMessage");
                    return;
                }
                //Log.d(TAG, "Change in playerBodypartSensortypeKey = " + playerBodypartSensortypeKey + " for UUID = " + characteristic.getUuid().toString());
                String playerBodypartSensortypeKey = player +"|"+ bodypart+"|"+sensortype;
                Log.d(TAG, "Change message of player "+player+ " bodypart " + bodypart +  " sensortype"+ sensortype + " to value =" + valuesStr );

                mMessagesMap.put(playerBodypartSensortypeKey, valuesStr );
            } else {
                Log.d(TAG, "characteristic value is empty");
            }
        }

        @Override
        public void onMtuChanged(BluetoothGatt gatt, int mtu, int status) {
            if (status == BluetoothGatt.GATT_SUCCESS) {
                Log.d(TAG, "onMtuChanged BluetoothGatt.GATT_SUCCESS mtu = "+mtu);
            } else {
                Log.d(TAG, "onMtuChanged status = "+status +"  mtu = "+mtu);
            }
        }

        @Override
        public void onDescriptorWrite(BluetoothGatt gatt, BluetoothGattDescriptor descriptor, int status) {
            Log.d(TAG, "Descriptor write callback UUID: " + descriptor.getUuid());
            Log.d(TAG, "Descriptor write status: " + status);
            parseNextCharacteristic();
        }

    };

    private Runnable mReadCharsRunnable = new Runnable() {
        @Override
        public void run() {
            parseNextCharacteristic();
        }
    };

    private void restartReadNextCharacteristic(){
        Log.d(TAG, "restartReadNextCharacteristic");
        mReadCharsHandler.removeCallbacks(mReadCharsRunnable);
        mReadCharsHandler.postDelayed(mReadCharsRunnable, 1000);
    }

    private void parseNextCharacteristic() {
        if (mCharacteristicsToParse.isEmpty()) {
            Log.d(TAG, "mCharacteristicsToRead is empty ");
            return;
        }

        BluetoothGattCharacteristic characteristic = mCharacteristicsToParse.get(0).second;
        BluetoothGatt gatt = mCharacteristicsToParse.get(0).first;
        mCharacteristicsToParse.remove(0);
        Log.d(TAG, "Remaining mCharacteristicsToRead = " + mCharacteristicsToParse.size());

        boolean somethingDone = false;
        if ((characteristic.getProperties() & BluetoothGattCharacteristic.PROPERTY_NOTIFY) > 0) {
            gatt.setCharacteristicNotification(characteristic, true);
            Log.d(TAG, "Trying to subscribe next chara = " + characteristic.getUuid().toString());
            // Find the CCCD descriptor and enable notifications
            BluetoothGattDescriptor cccdDescriptor = characteristic.getDescriptor(
                    UUID.fromString("00002902-0000-1000-8000-00805f9b34fb"));

            if (cccdDescriptor != null) {
                Log.d(TAG, "Found CCCD descriptor. Subscribing to notifications...");
                cccdDescriptor.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE);
                boolean result = gatt.writeDescriptor(cccdDescriptor);
                Log.d(TAG, "writeDescriptor result: " + result);
                somethingDone = true;
            } else {
                Log.e(TAG, "CCCD not found on this characteristic");
            }
        }
        Log.d(TAG, "Reading next chara = " + characteristic.getUuid().toString());
        boolean isReadable = ((characteristic.getProperties() & BluetoothGattCharacteristic.PROPERTY_READ) != 0);
        Log.d(TAG, "characteristic is readable = " + isReadable);
        if ((characteristic.getProperties() & BluetoothGattCharacteristic.PROPERTY_READ) > 0) {
            // Characteristic supports reading, you can proceed with read operation
            gatt.readCharacteristic(characteristic);
            somethingDone = true;

        }

        if(! somethingDone){
            // It is not possible to trigger the onRead, so let' just parse the next chara here
            parseNextCharacteristic();
        }
    }

    private void startScan() {
        Log.d(TAG, "startScan mIsScanning = " + mIsScanning);
        if (!mIsScanning) {
            mIsScanning = true;
            ScanSettings scanSettings = new ScanSettings.Builder()
                    .build();
            List<ScanFilter> filters = new ArrayList<>();
            //mBluetoothLeScanner.startScan(BnBLEHostCommunicator.this);
            mBluetoothLeScanner.startScan(filters, scanSettings, BnBLEHostCommunicator.this);
            mHandler.postDelayed(new Runnable() {
                @Override
                public void run() {
                    stopScan();
                }
            }, SCAN_INTERVAL);
        }
    }

    private void stopScan() {
        Log.d(TAG, "stopScan mIsScanning = " + mIsScanning);
        if (mIsScanning) {
            mIsScanning = false;
            mBluetoothLeScanner.stopScan(BnBLEHostCommunicator.this);
            mHandler.postDelayed(new Runnable() {
                @Override
                public void run() {
                    startScan();
                }
            }, SCAN_INTERVAL);

        }
    }

}


