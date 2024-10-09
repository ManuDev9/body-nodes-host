#
# MIT License
# 
# Copyright (c) 2024 Manuel Bottini
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import sys
import json
import threading
import time
import uuid
import struct

import asyncio
from bleak import BleakScanner
from bleak import BleakClient

# Don't use this script directly on the GIT Bash on Windows, the python script won't be able to use the input() command
# sudo apt-get update
# python3 -m pip install bleak

sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../body-nodes-common/python/")

import bnconstants
import bncommon

def current_milli_time():
    return round(time.time() * 1000)

# Extend this class to create your own listeners
class BodynodeListener:
    def onMessageReceived(self, player, bodypart, sensortype, value):
        print("onMessageReceive: player="+player + " bodypart="+bodypart + " sensortype="+sensortype + " value="+str(value))
    def isOfInterest(self, player, bodypart, sensortype):
        return True

class BodynodeListenerTest(BodynodeListener):
    def __init__(self):
        print("This is a test class")

class BnBLEHostCommunicator:

    # Initializes the object, no input parameters are required
    def __init__(self):
        # Thread for data connection
        self.blec_dataConnectionThread = None
        # Boolean to stop the thread
        self.blec_toStop = True
        # Json object containing the messages for each player+bodypart+sensortype combination (key)
        self.blec_messagesMap = {}
        # Map the BLE client address to the player+bodypart combination
        self.blec_BLEAddress_PlayerBodypartMap = {}
        # Map the player+bodypart combination to the BLE client
        self.blec_PlayerBodypart_BLEdevicesMap = {}
        # List of actions to send
        self.blec_actionsToSend = []
        self.blec_bodynodesListeners = []
        self.blec_identifiers = None

# Public functions

    # Starts the communicator
    def start(self, identifiers):
        # You are supposed to discover the bt_addresses yourself
        # Do also a pairing, connect, and if you want, trust
        # make use of bluetoothctl
        print("BnBLEHostCommunicator - Starting")

        self.blec_toStop = True

        self.blec_identifiers = identifiers
        self.blec_BLEAddress_PlayerBodypartMap = {}
        self.blec_PlayerBodypart_BLEdevicesMap = {}
        self.blec_actionsToSend = []
        self.blec_bodynodesListeners = []
        self.blec_dataConnectionThread = threading.Thread(target=self.run_data_connection_background)

        self.blec_toStop = False
        self.blec_dataConnectionThread.start()

    # Stops the communicator
    def stop(self):
        print("BnBLEHostCommunicator - Stopping")

        self.blec_toStop = True
        self.blec_dataConnectionThread.join()

        self.blec_BLEAddress_PlayerBodypartMap = {}
        self.blec_PlayerBodypart_BLEdevicesMap = {}
        self.blec_actionsToSend = []
        self.blec_bodynodesListeners = []
        self.blec_identifiers = None
        
    # Indicates if the host is running and listening
    def isRunning(self):
        return not self.blec_toStop

    # Update function, not in use
    def update(self):
        print("update function called [NOT IN USE]")

    def run_data_connection_background(self):
        asyncio.run(self.run_data_connection_background_tasks() )

    async def run_data_connection_background_tasks(self):

        print("")
        print("Discovering devices")
        devices = await BleakScanner.discover()
        
        list_subscribe = []

        print("")
        print(devices)
        for device in devices:
            if device.name == None:
                continue
            if device.name == self.blec_identifiers[0]:
                print("Connecting to " + device.address)
                client =  BleakClient(device.address)
                await client.connect()
                services = client.services
                for service in services:
                    print(f"Service: {service.uuid}")
                    if service.uuid == bnconstants.BLE_BODYNODES_SERVICE_UUID.lower():
                        for characteristic in service.characteristics:
                            print(f" - Characteristic: {characteristic.uuid}")
                            if ( characteristic.uuid.lower() == bnconstants.BLE_BODYNODES_CHARA_PLAYER_UUID.lower() or
                                    characteristic.uuid.lower() == bnconstants.BLE_BODYNODES_CHARA_BODYPART_UUID.lower() ):

                                print("Reading chara")
                                value = await client.read_gatt_char(characteristic.uuid)
                                self.__check_chara(client, characteristic.uuid, value)
                                
                            if( characteristic.uuid.lower() == bnconstants.BLE_BODYNODES_CHARA_ORIENTATION_ABS_VALUE_UUID.lower() or
                                    characteristic.uuid.lower() == bnconstants.BLE_BODYNODES_CHARA_ACCELERATION_REL_VALUE_UUID.lower() or
                                    characteristic.uuid.lower() == bnconstants.BLE_BODYNODES_CHARA_GLOVE_VALUE_UUID.lower() or
                                    characteristic.uuid.lower() == bnconstants.BLE_BODYNODES_CHARA_SHOE_UUID.lower() ):

                                print("Subscribing to chara")
                                list_subscribe.append({ "client": client , "characteristic_uuid" : characteristic.uuid })
                                
        
        await self.__ble_subscribe_all( list_subscribe ) 

        for plbo in self.blec_PlayerBodypart_BLEdevicesMap.keys():
            client = self.blec_PlayerBodypart_BLEdevicesMap[plbo]
            print("Disconnecting from " + client.address)
            await client.disconnect()
        
        print("Closing the data connection thread")
            
    # Returns the message associated to the requested player+bodypart+sensortype combination
    def getMessageValue(self, player, bodypart, sensortype):
        if player+"|"+bodypart+"|"+sensortype in self.blec_messagesMap:
            return self.blec_messagesMap[player+"|"+bodypart+"|"+sensortype]
        return None

    # Adds an action to the list of actions to be sent
    def addAction(self, action):
        self.blec_actionsToSend.append(action);
        
    # Sends all actions in the list
    def sendAllActions(self):
        print("sendAllActions function called [NOT IMPLEMENTED]")
        return

    # Checks if everything is ok. Returns true if it is indeed ok, false otherwise
    def checkAllOk(self):
        return not self.blec_toStop

    def addListener(self, listener):
        if listener == None:
            print("Given listener is empty")
            return False
        if not isinstance(listener, BodynodeListener):
            print("Given listener does not extend BodynodeListener")
            return False
        self.blec_bodynodesListeners.append(listener)
        return True        
        
    def removeListener(self, listener):
        self.blec_bodynodesListeners.remove(listener)
    
    def removeAllListeners(self):
        self.blec_bodynodesListeners = []

# Private functions

    async def __ble_subscribe_chara(self, client, uuid):
        await client.start_notify(uuid, lambda sender, value: self.__device_notification(sender, client.address, uuid, value)  ) 

        while not self.blec_toStop:
            await asyncio.sleep(0.005)
        
        print( "Closing this subscription " +client.address + " "+ uuid )
        await client.stop_notify(uuid)

    async def __ble_subscribe_all(self, list_subscribe):
        tasks = []
        for subscr in list_subscribe:
            tasks.append(self.__ble_subscribe_chara(subscr["client"], subscr["characteristic_uuid"]))
        return await asyncio.gather(*tasks)

    def __device_notification(self, sender, ble_address, characteristic_uuid, value):
        #print(f"Notification from {ble_address} {characteristic_uuid}")

        jsonMessage = self.__createJsonMessageFromBLEChara(characteristic_uuid, value);

        player = self.blec_BLEAddress_PlayerBodypartMap[ble_address]["player"]
        bodypart = self.blec_BLEAddress_PlayerBodypartMap[ble_address]["bodypart"]
        if player == "":
            print("Missing player")
            return
        if bodypart == "":
            print("Missing bodypart")
            return

        sensortype = jsonMessage[bnconstants.MESSAGE_SENSORTYPE_TAG]
        self.blec_messagesMap[player +"|"+ bodypart+"|"+sensortype] = str(jsonMessage[bnconstants.MESSAGE_VALUE_TAG])
        for listener in self.blec_bodynodesListeners:
            if listener.isOfInterest(player, bodypart, sensortype ):
                listener.onMessageReceived(player, bodypart, sensortype, jsonMessage[bnconstants.MESSAGE_VALUE_TAG])

    
    def __check_chara(self, client, uuid, value):
        
        player = None
        bodypart = None
        
        if uuid == bnconstants.BLE_BODYNODES_CHARA_PLAYER_UUID.lower() :
            player = value.decode('utf-8')

        if uuid == bnconstants.BLE_BODYNODES_CHARA_BODYPART_UUID.lower() :
            bodypart = value.decode('utf-8')

        if client.address not in self.blec_BLEAddress_PlayerBodypartMap:
            self.blec_BLEAddress_PlayerBodypartMap[client.address] = { "player": "", "bodypart" : "" }

        if player != None:
            self.blec_BLEAddress_PlayerBodypartMap[client.address]["player"] = player

        if bodypart != None:
            self.blec_BLEAddress_PlayerBodypartMap[client.address]["bodypart"] = bodypart

        player = self.blec_BLEAddress_PlayerBodypartMap[client.address]["player"]
        bodypart = self.blec_BLEAddress_PlayerBodypartMap[client.address]["bodypart"]
        
        if player != "" and bodypart != "":
            self.blec_PlayerBodypart_BLEdevicesMap[player+"|"+bodypart] = client

    def __createJsonMessageFromBLEChara(self, characteristic_uuid, value):
        jsonMessage = {}
        if characteristic_uuid == bnconstants.BLE_BODYNODES_CHARA_ORIENTATION_ABS_VALUE_UUID.lower():
            jsonMessage[bnconstants.MESSAGE_SENSORTYPE_TAG] = bnconstants.SENSORTYPE_ORIENTATION_ABS_TAG
            # '>f' means big-endian float
            jsonMessage[bnconstants.MESSAGE_VALUE_TAG] = [
                struct.unpack('>f', value[0:4])[0],
                struct.unpack('>f', value[4:8])[0],
                struct.unpack('>f', value[8:12])[0],
                struct.unpack('>f', value[12:16])[0]
            ]

        elif characteristic_uuid == bnconstants.BLE_BODYNODES_CHARA_ACCELERATION_REL_VALUE_UUID.lower():
            jsonMessage[bnconstants.MESSAGE_SENSORTYPE_TAG] = bnconstants.SENSORTYPE_ACCELERATION_REL_TAG
            # '>f' means big-endian float
            jsonMessage[bnconstants.MESSAGE_VALUE_TAG] = [
                struct.unpack('>f', value[0:4])[0],
                struct.unpack('>f', value[4:8])[0],
                struct.unpack('>f', value[8:12])[0]
            ]

        elif characteristic_uuid == bnconstants.BLE_BODYNODES_CHARA_GLOVE_VALUE_UUID.lower():
            jsonMessage[bnconstants.MESSAGE_SENSORTYPE_TAG] = bnconstants.SENSORTYPE_GLOVE_TAG
            jsonMessage[bnconstants.MESSAGE_VALUE_TAG] = [
                int.from_bytes(value[0]),
                int.from_bytes(value[1]),
                int.from_bytes(value[2]),
                int.from_bytes(value[3]),
                int.from_bytes(value[4]),

                int.from_bytes(value[5]),
                int.from_bytes(value[6]),
                int.from_bytes(value[7]),
                int.from_bytes(value[8])

            ]
        elif characteristic_uuid == bnconstants.BLE_BODYNODES_CHARA_SHOE_UUID.lower():
            jsonMessage[bnconstants.MESSAGE_SENSORTYPE_TAG] = bnconstants.SENSORTYPE_SHOE_TAG
            jsonMessage[bnconstants.MESSAGE_VALUE_TAG] = [
                int.from_bytes(value[0])
            ]
        
        return jsonMessage
        


if __name__=="__main__":
    communicator = BnBLEHostCommunicator()
    communicator.start([bnconstants.BLE_BODYNODES_NAME])
    listener = BodynodeListenerTest()
    command = "n"
    while command != "e":
        command = input("Type a command [r/l/u to read message, h/p/b/s/w to send action, e to exit]: ")
        print(command)
        if command == "r":
            outvalue = communicator.getMessageValue("1", "katana", "orientation_abs")
            print(outvalue)

        elif command == 'l':
            communicator.addListener(listener)
            
        elif command == 'u':
            communicator.removeListener(listener)
            
    
    communicator.stop()
    exit()
