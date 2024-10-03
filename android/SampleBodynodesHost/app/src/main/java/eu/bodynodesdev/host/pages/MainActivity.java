package eu.bodynodesdev.host.pages;

import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.Handler;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import androidx.activity.EdgeToEdge;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

import eu.bodynodesdev.common.BnConstants;
import eu.bodynodesdev.host.BnBLEHostCommunicator;
import eu.bodynodesdev.host.BnHostCommunicator;
import eu.bodynodesdev.host.R;

public class MainActivity extends AppCompatActivity {

    private final static String TAG = "MainActivity";


    private Button mStartBLEButton;
    private Button mStartBluetoothButton;
    private Button mStartWifiButton;
    private Button mStopButton;
    private EditText mMessagesInfoEditText;

    BnHostCommunicator mHostCommunicator;

    // Communicator Types
    private static int HOST_COMMUNICATOR_BLE = 0;
    private static int HOST_COMMUNICATOR_BLUETOOTH = 1;
    private static int HOST_COMMUNICATOR_WIFI = 2;

    private static final int REQUEST_BLE_PERMISSIONS = 1;

    private final Handler mHandler = new Handler();
    private boolean mIsRunning = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main);
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });

        mHostCommunicator = null;

        getViewReferences();
        setOnClicks();
        startTimer();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        mIsRunning = false;
    }

    private void getViewReferences() {
        mStartBLEButton = findViewById(R.id.main_page_start_ble_button);
        mStartBluetoothButton = findViewById(R.id.main_page_start_bluetooth_button);
        mStartWifiButton = findViewById(R.id.main_page_start_wifi_button);
        mStopButton = findViewById(R.id.main_page_stop_button);
        mMessagesInfoEditText = findViewById(R.id.main_page_messages_info);

        mStartBLEButton.setVisibility(View.VISIBLE);
        mStartBluetoothButton.setVisibility(View.GONE);
        mStartWifiButton.setVisibility(View.GONE);
        mStopButton.setVisibility(View.GONE);
    }

    private void setOnClicks() {
        mStartBLEButton.setOnClickListener(view -> startCommunicator(HOST_COMMUNICATOR_BLE));
        mStartBluetoothButton.setOnClickListener(view -> startCommunicator(HOST_COMMUNICATOR_BLUETOOTH));
        mStartWifiButton.setOnClickListener(view -> startCommunicator(HOST_COMMUNICATOR_WIFI));
        mStopButton.setOnClickListener(view -> stopCommunicator());
    }


    private void startTimer() {
        mIsRunning = true;
        mHandler.postDelayed(new Runnable() {
            @Override
            public void run() {
                if (mIsRunning) {
                    // Call your function here
                    updateMessagesInfo();

                    // Schedule the next execution
                    mHandler.postDelayed(this, BnConstants.SENSOR_READ_INTERVAL_MS); // 1000 ms = 1 second
                }
            }
        }, 1000); // Start after 1 second
    }

    private void updateMessagesInfo(){
        if(mHostCommunicator != null) {
            mMessagesInfoEditText.setText(mHostCommunicator.getMessages());
        } else {
            mMessagesInfoEditText.setText("No Host has been started");
        }
    }

    private boolean checkPermissions() {
        return ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_SCAN) == PackageManager.PERMISSION_GRANTED &&
                ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED &&
                ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    private void  startBLECommunicator(){
        Log.d(TAG, "Start BLE communicator");
        mHostCommunicator = new BnBLEHostCommunicator(this);

        // todo the other host communicators
        mStartBLEButton.setVisibility(View.GONE);
        mStartBluetoothButton.setVisibility(View.GONE);
        mStartWifiButton.setVisibility(View.GONE);
        mStopButton.setVisibility(View.VISIBLE);
        mHostCommunicator.start();
    }



    private void startCommunicator(int type) {
        if(mHostCommunicator !=  null) {
            mHostCommunicator.stop();
            mHostCommunicator = null;
        }
        if(type == HOST_COMMUNICATOR_BLE) {
            if (checkPermissions()) {
                // Start your Bluetooth scanning process
                startBLECommunicator();
            } else {
                requestPermissions();
            }
        }
    }

    public void stopCommunicator(){
        if(mHostCommunicator !=null){
            mHostCommunicator.stop();
        }
        mStartBLEButton.setVisibility(View.VISIBLE);
        mStartBluetoothButton.setVisibility(View.GONE);
        mStartWifiButton.setVisibility(View.GONE);
        mStopButton.setVisibility(View.GONE);
    }




    private void requestPermissions() {
        ActivityCompat.requestPermissions(this,
                new String[]{
                        Manifest.permission.BLUETOOTH_SCAN,
                        Manifest.permission.BLUETOOTH_CONNECT,
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
}