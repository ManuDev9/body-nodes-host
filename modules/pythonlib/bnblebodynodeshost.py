#
# MIT License
#
# Copyright (c) 2024-2025 Manuel Bottini
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

"""
Module implementation of the BLE Bodynode Host.
"""

import threading
import time
import sys
import struct

import asyncio
from bleak import BleakScanner
from bleak import BleakClient

# Don't use this script directly on the GIT Bash on Windows, the python script won't be able to use the input() command
# sudo apt-get update
# python3 -m pip install bleak

# sudo apt update && sudo apt install --reinstall bluez
# systemctl status bluetooth
# sudo systemctl daemon-reload
# sudo systemctl unmask bluetooth
# sudo systemctl start bluetooth
# sudo systemctl enable bluetooth


from bncommon import BnConstants


def current_milli_time():
    """Utility function that returns the current time in milliseconds"""
    return round(time.time() * 1000)


class BodynodeListener:
    """Listener class to receive bodynodes data"""

    def on_message_received(self, player, bodypart, sensortype, value):
        """Callback with player, bodypart, sensortype, and value info"""
        print(
            f"on_message_received: player={player} bodypart={bodypart} sensortype={sensortype} value={value}"
        )

    def is_of_interest(self, player, bodypart, sensortype):
        """By overriding this function you can set which set of player / bodypart / sensortype the listerner returns data of"""
        print(
            f"is_of_interest: returning True for player={player} bodypart={bodypart} sensortype={sensortype}"
        )
        return True


class BodynodeListenerTest(BodynodeListener):
    """Implementation example of a BodynodeListener"""

    def __init__(self):
        print("This is a test class")


class BnBLEHostCommunicator:
    """Bodynodes BLE Host ommunicator implementation"""

    def __init__(self):
        # Thread for data connection
        self.blec_data_connection_thread = None
        # Boolean to stop the thread
        self.blec_to_stop = True

        self.blec_maps = {
            # Json object containing the messages for each player+bodypart+sensortype combination (key)
            "messages": {},
            # Map the BLE client address to the player+bodypart combination
            "BLEAddress_PlayerBodypart": {},
            # Map the player+bodypart combination to the BLE client
            "PlayerBodypart_BLEdevices": {},
        }
        # List of actions to send
        self.blec_actions_to_send = []
        self.blec_bodynodes_listeners = []
        self.blec_identifiers = None

    # Public functions

    def start(self, identifiers):
        """Starts the communicator"""

        # You are supposed to discover the bt_addresses yourself
        # Do also a pairing, connect, and if you want, trust
        # make use of bluetoothctl
        print("BnBLEHostCommunicator - Starting")

        self.blec_to_stop = True
        self.blec_identifiers = identifiers
        self.blec_maps = {
            "messages": {},
            "BLEAddress_PlayerBodypart": {},
            "PlayerBodypart_BLEdevices": {},
        }
        self.blec_actions_to_send = []
        self.blec_data_connection_thread = threading.Thread(
            target=self.run_data_connection_background
        )

        self.blec_to_stop = False
        self.blec_data_connection_thread.start()

    def stop(self):
        """Stops the communicator"""

        print("BnBLEHostCommunicator - Stopping")

        self.blec_to_stop = True
        if self.blec_data_connection_thread.is_alive():
            self.blec_data_connection_thread.join()

        self.blec_maps = {
            "messages": {},
            "BLEAddress_PlayerBodypart": {},
            "PlayerBodypart_BLEdevices": {},
        }

        self.blec_actions_to_send = []
        self.blec_bodynodes_listeners = []
        self.blec_identifiers = None

    def is_running(self):
        """Returns true if the communicator is running, false otherwise"""

        return not self.blec_to_stop

    def update(self):
        """Update function, not in use"""

        print("update function called [NOT IN USE]")

    def run_data_connection_background(self):
        """Data connection runner function"""

        asyncio.run(self.run_data_connection_background_tasks())

    async def run_data_connection_background_tasks(self):
        """Data connection task function"""

        print("\nDiscovering devices")
        try:
            devices = await BleakScanner.discover()
        except OSError:
            print("")
            print(
                "It was not possible to discover BLE devices, make sure you have the Bluetooth ON in your PC/Laptop"
            )
            self.blec_to_stop = True
            return

        list_subscribe = []

        print("")
        print(devices)
        for device in devices:
            if device.name is None:
                continue
            if device.name != self.blec_identifiers[0]:
                continue

            print("Connecting to " + device.address)
            client = BleakClient(
                device.address, disconnected_callback=self.__handle_disconnect
            )
            await client.connect()
            services = client.services
            for service in services:
                print(f"Service: {service.uuid}")
                if service.uuid != BnConstants.BLE_SERVICE_UUID.lower():
                    continue

                for characteristic in service.characteristics:
                    print(f" - Characteristic: {characteristic.uuid}")
                    if (
                        characteristic.uuid.lower()
                        == BnConstants.BLE_CHARA_PLAYER_UUID.lower()
                        or characteristic.uuid.lower()
                        == BnConstants.BLE_CHARA_BODYPART_UUID.lower()
                    ):

                        print("Reading chara")
                        value = await client.read_gatt_char(characteristic.uuid)
                        self.__check_chara(client, characteristic.uuid, value)

                    if (
                        characteristic.uuid.lower()
                        == BnConstants.BLE_CHARA_ORIENTATION_ABS_VALUE_UUID.lower()
                        or characteristic.uuid.lower()
                        == BnConstants.BLE_CHARA_ACCELERATION_REL_VALUE_UUID.lower()
                        or characteristic.uuid.lower()
                        == BnConstants.BLE_CHARA_GLOVE_VALUE_UUID.lower()
                        or characteristic.uuid.lower()
                        == BnConstants.BLE_CHARA_SHOE_UUID.lower()
                        or characteristic.uuid.lower()
                        == BnConstants.BLE_CHARA_ANGULARVELOCITY_REL_VALUE_UUID.lower()
                    ):

                        print("Subscribing to chara")
                        list_subscribe.append(
                            {
                                "client": client,
                                "characteristic_uuid": characteristic.uuid,
                            }
                        )

        await self.__ble_subscribe_all(list_subscribe)

        for _, client in self.blec_maps["PlayerBodypart_BLEdevices"].items():
            if client.is_connected:
                print("Disconnecting from " + client.address)
                await client.disconnect()

        print("Closing the data connection thread")

    def get_message_value(self, player, bodypart, sensortype):
        """Returns the message associated to the requested player+bodypart+sensortype combination"""

        pbs_key = f"{player}|{bodypart}|{sensortype}"
        if pbs_key in self.blec_maps["messages"]:
            return self.blec_maps["messages"][pbs_key]
        return None

    def add_action(self, action):
        """Adds an action to the list of actions to be sent"""

        self.blec_actions_to_send.append(action)

    def send_all_actions(self):
        """Sends all actions in the list"""

        print("send_all_actions function called [NOT IMPLEMENTED]")

    def check_all_ok(self):
        """Checks if everything is ok. Returns true if it is indeed ok, false otherwise"""

        return not self.blec_to_stop

    def add_listener(self, listener):
        """Add a listener to the communicator"""

        if listener is None:
            print("Given listener is empty")
            return False
        if not isinstance(listener, BodynodeListener):
            print("Given listener does not extend BodynodeListener")
            return False
        self.blec_bodynodes_listeners.append(listener)
        return True

    def remove_listener(self, listener):
        """Remove a listener in the communicator"""

        self.blec_bodynodes_listeners.remove(listener)

    def remove_all_listeners(self):
        """Remove all listeners in the communicator"""

        self.blec_bodynodes_listeners = []

    # Private functions

    def __handle_disconnect(self, client):
        print(f"Device {client.address} has fully disconnected, no bluetooth.")

    async def __ble_subscribe_chara(self, client, uuid):
        """Subscribe to a BLE characteristic"""

        await client.start_notify(
            uuid,
            lambda sender, value: self.__receive_notification(
                sender, client.address, uuid, value
            ),
        )

        while not self.blec_to_stop:
            await asyncio.sleep(0.005)

        if client.is_connected:
            print("Closing this subscription " + client.address + " " + uuid)
            await client.stop_notify(uuid)

    async def __ble_subscribe_all(self, list_subscribe):
        """Subscribe to a list of BLE characteristics"""

        tasks = []
        for subscr in list_subscribe:
            tasks.append(
                self.__ble_subscribe_chara(
                    subscr["client"], subscr["characteristic_uuid"]
                )
            )
        return await asyncio.gather(*tasks)

    def __receive_notification(self, sender, ble_address, characteristic_uuid, value):
        """Receive a notification with a value"""

        # print(f"Notification from {ble_address} {characteristic_uuid}")

        json_message = self.__create_json_message_from_ble_chara(
            characteristic_uuid, value
        )

        # print(sender) # example: 0000cca3-0000-1000-8000-00805f9b34fb (Handle: 168): Vendor specific
        player = self.blec_maps["BLEAddress_PlayerBodypart"][ble_address]["player"]
        bodypart = self.blec_maps["BLEAddress_PlayerBodypart"][ble_address]["bodypart"]
        if player == "":
            print(f"{sender}:Missing player")
            return
        if bodypart == "":
            print(f"{sender}:Missing bodypart")
            return

        sensortype = json_message[BnConstants.MESSAGE_SENSORTYPE_TAG]
        self.blec_maps["messages"][player + "|" + bodypart + "|" + sensortype] = str(
            json_message[BnConstants.MESSAGE_VALUE_TAG]
        )
        for listener in self.blec_bodynodes_listeners:
            if listener.is_of_interest(player, bodypart, sensortype):
                listener.on_message_received(
                    player,
                    bodypart,
                    sensortype,
                    json_message[BnConstants.MESSAGE_VALUE_TAG],
                )

    def __check_chara(self, client, uuid, value):
        """Check characteristic validity and set in map"""

        player = None
        bodypart = None

        if uuid == BnConstants.BLE_CHARA_PLAYER_UUID.lower():
            player = value.decode("utf-8")

        if uuid == BnConstants.BLE_CHARA_BODYPART_UUID.lower():
            bodypart = value.decode("utf-8")

        if client.address not in self.blec_maps["BLEAddress_PlayerBodypart"]:
            self.blec_maps["BLEAddress_PlayerBodypart"][client.address] = {
                "player": "",
                "bodypart": "",
            }

        if player is not None:
            self.blec_maps["BLEAddress_PlayerBodypart"][client.address][
                "player"
            ] = player

        if bodypart is not None:
            self.blec_maps["BLEAddress_PlayerBodypart"][client.address][
                "bodypart"
            ] = bodypart

        player = self.blec_maps["BLEAddress_PlayerBodypart"][client.address]["player"]
        bodypart = self.blec_maps["BLEAddress_PlayerBodypart"][client.address][
            "bodypart"
        ]

        if player != "" and bodypart != "":
            self.blec_maps["PlayerBodypart_BLEdevices"][
                player + "|" + bodypart
            ] = client

    def __create_json_message_from_ble_chara(self, characteristic_uuid, value):
        """Create a JSON from a characteristic"""

        json_message = {}
        try:

            if (
                characteristic_uuid
                == BnConstants.BLE_CHARA_ORIENTATION_ABS_VALUE_UUID.lower()
            ):
                json_message[BnConstants.MESSAGE_SENSORTYPE_TAG] = (
                    BnConstants.SENSORTYPE_ORIENTATION_ABS_TAG
                )
                # '>f' means big-endian float
                json_message[BnConstants.MESSAGE_VALUE_TAG] = [
                    struct.unpack(">f", value[0:4])[0],
                    struct.unpack(">f", value[4:8])[0],
                    struct.unpack(">f", value[8:12])[0],
                    struct.unpack(">f", value[12:16])[0],
                ]

            elif (
                characteristic_uuid
                == BnConstants.BLE_CHARA_ACCELERATION_REL_VALUE_UUID.lower()
            ):
                json_message[BnConstants.MESSAGE_SENSORTYPE_TAG] = (
                    BnConstants.SENSORTYPE_ACCELERATION_REL_TAG
                )
                # '>f' means big-endian float
                json_message[BnConstants.MESSAGE_VALUE_TAG] = [
                    struct.unpack(">f", value[0:4])[0],
                    struct.unpack(">f", value[4:8])[0],
                    struct.unpack(">f", value[8:12])[0],
                ]

            elif characteristic_uuid == BnConstants.BLE_CHARA_GLOVE_VALUE_UUID.lower():
                json_message[BnConstants.MESSAGE_SENSORTYPE_TAG] = (
                    BnConstants.SENSORTYPE_GLOVE_TAG
                )
                json_message[BnConstants.MESSAGE_VALUE_TAG] = [
                    value[0],
                    value[1],
                    value[2],
                    value[3],
                    value[4],
                    value[5],
                    value[6],
                    value[7],
                    value[8],
                ]
            elif characteristic_uuid == BnConstants.BLE_CHARA_SHOE_UUID.lower():
                json_message[BnConstants.MESSAGE_SENSORTYPE_TAG] = (
                    BnConstants.SENSORTYPE_SHOE_TAG
                )
                json_message[BnConstants.MESSAGE_VALUE_TAG] = [value[0]]
            elif (
                characteristic_uuid
                == BnConstants.BLE_CHARA_ANGULARVELOCITY_REL_VALUE_UUID.lower()
            ):
                json_message[BnConstants.MESSAGE_SENSORTYPE_TAG] = (
                    BnConstants.SENSORTYPE_ANGULARVELOCITY_REL_TAG
                )
                # '>f' means big-endian float
                json_message[BnConstants.MESSAGE_VALUE_TAG] = [
                    struct.unpack(">f", value[0:4])[0],
                    struct.unpack(">f", value[4:8])[0],
                    struct.unpack(">f", value[8:12])[0],
                ]
        except TypeError as err:
            print(err)
            json_message = {}

        return json_message


def main():
    """Main function running a default communicator"""

    communicator = BnBLEHostCommunicator()
    # communicator.start([BnConstants.BLE_NAME])
    communicator.start(["Pixel 7"])
    listener = BodynodeListenerTest()
    command = "n"
    while command != "e":
        command = input(
            "Type a command [r/l/u to read message, actions not supported, e to exit]: "
        )
        print(command)
        if command == "r":
            outvalue = communicator.get_message_value(
                "1",
                BnConstants.BODYPART_KATANA_TAG,
                BnConstants.SENSORTYPE_ORIENTATION_ABS_TAG,
            )
            print(outvalue)

        elif command == "l":
            communicator.add_listener(listener)

        elif command == "u":
            communicator.remove_listener(listener)

    communicator.stop()


if __name__ == "__main__":
    main()
    sys.exit()
