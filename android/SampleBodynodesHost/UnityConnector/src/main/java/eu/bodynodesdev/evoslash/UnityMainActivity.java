/**
 * MIT License
 *
 * Copyright (c) 2019-2023 Manuel Bottini
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

package eu.bodynodesdev.evoslash;

import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.util.Log;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import eu.bodynodesdev.host.BnBLEHostCommunicator;


public class UnityMainActivity extends UnityPlayerActivity {

    private static final int REQUEST_BLE_PERMISSIONS = 1;

    private final static String TAG = "UnityMainActivity";
    private BnBLEHostCommunicator mBLEHostCommunicator;

    private static UnityMainActivity mActivity;

    public void startBLECommunicator() {
        Log.d(TAG,"startBLE");
        if(mBLEHostCommunicator !=  null) {
            mBLEHostCommunicator.stop();
            mBLEHostCommunicator = null;
        }
        mBLEHostCommunicator = new BnBLEHostCommunicator(this);
        mBLEHostCommunicator.start();
    }

    public void startBLE() {
        if (checkPermissions()) {
            // Start your Bluetooth scanning process
            startBLECommunicator();
        } else {
            requestPermissions();
        }
    }

    public void stopBLE(){
        if(mBLEHostCommunicator !=null){
            mBLEHostCommunicator.stop();
        }
    }

    private void requestPermissions() {
        ActivityCompat.requestPermissions(this,
                new String[]{
                        Manifest.permission.BLUETOOTH,
                        Manifest.permission.BLUETOOTH_ADMIN,
                        Manifest.permission.BLUETOOTH_SCAN,
                        Manifest.permission.BLUETOOTH_CONNECT,
                        Manifest.permission.ACCESS_COARSE_LOCATION,
                        Manifest.permission.ACCESS_FINE_LOCATION
                },
                REQUEST_BLE_PERMISSIONS);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_BLE_PERMISSIONS) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                // Permissions granted
                startBLECommunicator();
            } else {
                // Permissions denied
                Toast.makeText(this, "Permissions denied. Cannot perform Bluetooth scan.", Toast.LENGTH_SHORT).show();
            }
        }
    }

    private boolean checkPermissions() {
        return ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH) == PackageManager.PERMISSION_GRANTED &&
                ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_ADMIN) == PackageManager.PERMISSION_GRANTED &&
                ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_SCAN) == PackageManager.PERMISSION_GRANTED &&
                ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED &&
                ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED &&
                ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    /*
    public void sendHapticAction(String bodypart, int duration_ms, int strength ){
        Log.d(TAG,"- sendHapticAction bodypart = " + bodypart + " , duration_ms = " + duration_ms + " , strength = " + strength);
        sInstance.sendHapticAction(bodypart, (short)duration_ms, (byte)strength);
    }
    */

    public String getMessage(String player, String bodypart, String sensortype ) {
        //Log.d(TAG,"-getMessage player = " + player + " , bodypart = " +bodypart + " , sensortype = " + sensortype );
        return mBLEHostCommunicator.getMessage(player, bodypart, sensortype);
    }

    public String getMessages() {
        return mBLEHostCommunicator.getMessages();
    }

    public static UnityMainActivity currentActivity()
    {
        Log.i("UnityMainActivity", "currentActivity");
        if(mActivity != null){
            Log.i("UnityMainActivity", "mActivity is good");
        } else {
            Log.i("UnityMainActivity", "mActivity is null");
        }
        return mActivity;
    }

    @Override
    protected void onCreate(Bundle bundle) {
        super.onCreate(bundle);
        Log.i("UnityMainActivity", "onCreate");
        mActivity = this;
    }

    @Override
    protected void onDestroy() {
        Log.i("UnityMainActivity", "onDestroy");
        super.onDestroy();
        mActivity = null;
    }
}
