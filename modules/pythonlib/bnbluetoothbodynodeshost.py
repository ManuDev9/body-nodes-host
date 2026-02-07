#
# MIT License
#
# Copyright (c) 2024-2026 Manuel Bottini
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
Module implementation of the Bluetooth Bodynode Host.
"""

import sys
import threading
import json
import time
import socket
import subprocess
import re

from bncommon import BnConstants

# Note: based on "sdptool"
# $ sdptool browse --tree 24:95:2F:64:68:A6 | grep -B 10 -A 10 "0x1101" | grep Channel
#       Channel/Port (Integer) : 0x11


# sudo apt update
# sudo apt install -y software-properties-common
# sudo add-apt-repository ppa:deadsnakes/ppa
# sudo apt update
# sudo apt install -y python3.7 python3.7-venv python3.7-dev
# sudo apt remove -y python3.10 python3.10-venv python3.10-dev

# sudo apt-get update
# sudo apt-get install libbluetooth-dev
# sudo apt-get install python3-bluez

# python3.7 -m venv venv
# source venv/bin/activate
# pip install pybluez
# bluetoothctl show
#              power on
#              power off
#              discoverable on
#              pairable on
#              pair
#              devices
#
# rfkill list bluetooth
# Name: Pixel A - Address: 13:95:2G:61:6P:C6
#                 pair 13:95:2G:61:6P:A6
#                 connect 13:95:2G:61:6P:C6
#                 info 13:95:2G:61:6P:C6
# UUID: Serial Port              (00001101-0000-1000-8000-00805f9b34fb)
#
# It is best to first run the app, and then pair it to propertly discover the UUID Serial Port
# otherwise it might be seen. NOTE: This happens ONlY the first time the Host pair to the Node


bodynodes_bt = {
    "buffer_size": 1024,
    "connection_keep_alive_rec_interval_ms": 60000,
    "connection_ack_interval_ms": 1000,
    # This is the common UUID of the service to look for
    "nodes_UUID128": "00001101-0000-1000-8000-00805f9b34fb",
    "nodes_UUID16": "0x1101",
}


def current_milli_time():
    """Utility function that returns the current time in milliseconds"""
    return round(time.time() * 1000)


def get_bt_port(bt_addr, target_uuid16="0x1101"):
    """Utility function that returns the bluetooth port from"""
    try:
        result = subprocess.run(
            ["sdptool", "browse", "--tree", bt_addr],
            capture_output=True,
            text=True,
            check=True,
        )

        records = result.stdout.split(
            "Attribute Identifier : 0x0 - ServiceRecordHandle"
        )
        found_ports = []

        for record in records:
            if target_uuid16 in record:
                match = re.search(
                    r"Channel/Port \(Integer\) : (0x[0-9a-fA-F]+)", record
                )
                if match:
                    found_ports.append(match.group(1))

        print(found_ports)
        if found_ports:
            hex_val = found_ports[-1]
            return int(hex_val, 16)

    except subprocess.CalledProcessError as e:
        print(f"Error running sdptool: {e}")

    return None


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


class BnBluetoothHostCommunicator:
    """Bodynodes Bluetooth Host ommunicator implementation"""

    def __init__(self):
        # Thread for data connection
        self.bthc_data_connection_thread = threading.Thread(
            target=self.run_data_connection_background
        )
        # Boolean to stop the thread
        self.bthc_to_stop = True

        self.bthc_maps = {
            # Json object containing the messages for each player+bodypart+sensortype combination (key)
            "messages": {},
            # Map the connections (bt_address) to the player+bodypart combination (key)
            "connections": {},
            # Map temporary connections data to an arbitrary string representation of a connection (key)
            "tempConnectionsData": {},
        }

        # Dictionary of bluetooth address / connector objects that can receive and send data
        self.bthc_connectors = {}
        # List of actions to send
        self.bthc_actions_to_send = []
        self.bthc_bodynodes_listeners = []

    # Public functions

    def start(self, identifiers):
        """Starts the communicator"""

        # You are supposed to discover the bt_addresses yourself
        # Do also a pairing, connect, and if you want, trust
        # make use of bluetoothctl
        print("BnBluetoothHostCommunicator - Starting")

        self.bthc_maps = {
            "messages": {},
            "connections": {},
            "tempConnectionsData": {},
        }
        self.bthc_connectors = {}
        self.bthc_actions_to_send = []
        self.bthc_bodynodes_listeners = []

        for bt_addr in identifiers:
            print(f"Trying to connect to {bt_addr}")

            # Connect to the service
            port = get_bt_port(bt_addr, bodynodes_bt["nodes_UUID16"])
            if port is None:
                print(f"Cannot find port in {bt_addr}")
                continue

            sock = socket.socket(
                socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
            )
            try:
                sock.connect((bt_addr, port))
                print(f"Connected to {bt_addr}")

                sock.setblocking(False)
                self.bthc_connectors[bt_addr] = sock

            except socket.error as e:
                print(f"Connection failed to {bt_addr}: {e}")
                sock.close()

        self.bthc_to_stop = False
        self.bthc_data_connection_thread.start()

    def stop(self):
        """Stops the communicator"""

        print("BnBluetoothHostCommunicator - Stopping")
        self.bthc_to_stop = True
        for _, conn in self.bthc_connectors.items():
            conn.close()

        self.bthc_maps = {
            "messages": {},
            "connections": {},
            "tempConnectionsData": {},
        }
        self.bthc_connectors = {}
        self.bthc_actions_to_send = []
        self.bthc_bodynodes_listeners = []

    def is_running(self):
        """Returns true if the communicator is running, false otherwise"""

        return not self.bthc_to_stop

    def update(self):
        """Update function, not in use"""

        print("Update function called [NOT IN USE]")

    def run_data_connection_background(self):
        """Data connection runner function"""

        while not self.bthc_to_stop:
            self.check_all_ok()
            time.sleep(0.01)

    def get_message_value(self, player, bodypart, sensortype):
        """Returns the message associated to the requested player+bodypart+sensortype combination"""

        pbs_key = f"{player}|{bodypart}|{sensortype}"
        if pbs_key in self.bthc_maps["messages"]:
            return self.bthc_maps["messages"][pbs_key]
        return None

    def add_action(self, action):
        """Adds an action to the list of actions to be sent"""

        self.bthc_actions_to_send.append(action)

    def send_all_actions(self):
        """Sends all actions in the list"""

        for action in self.bthc_actions_to_send:
            player_bodypart = action["player"] + "_" + action["bodypart"]
            if (
                player_bodypart not in self.bthc_maps["connections"]
                or self.bthc_maps["connections"][player_bodypart] is None
            ):
                print("Player+Bodypart connection not existing\n")
                continue
            action_str = json.dumps(action)
            self.bthc_connectors[self.bthc_maps["connections"][player_bodypart]].send(
                action_str.encode("utf-8")
            )

        self.bthc_actions_to_send = []

    def check_all_ok(self):
        """Checks if everything is ok. Returns true if it is indeed ok, false otherwise"""

        self.__receive_bytes()
        for _, tmp_connection in self.bthc_maps["tempConnectionsData"].items():

            # print("Connection to check "+tmp_connection_str+"\n", )
            # if tmp_connection["received_bytes"] is not None:
            # print("Connection to check "+tmp_connection_str+"\n", )
            # received_bytes_str = tmp_connection["received_bytes"].decode("utf-8")
            # print("Data in the received bytes "+received_bytes_str+"\n" )
            # print("Status connection "+tmp_connection["STATUS"] )

            if tmp_connection["STATUS"] == "IS_WAITING_ACK":
                # print("Connetion is waiting ACKN")
                if self.__check_for_ackn(tmp_connection):
                    self.__send_ackh(tmp_connection)
                    tmp_connection["STATUS"] = "CONNECTED"
            else:
                if (
                    current_milli_time() - tmp_connection["last_rec_time"]
                    > bodynodes_bt["connection_keep_alive_rec_interval_ms"]
                ):
                    tmp_connection["STATUS"] = "DISCONNECTED"
                if self.__check_for_ackn(tmp_connection):
                    print("Received ACKN")
                    self.__send_ackh(tmp_connection)
                else:
                    self.__check_for_messages(tmp_connection)
            tmp_connection["received_bytes"] = None
            tmp_connection["num_received_bytes"] = 0
        return not self.bthc_to_stop

    def add_listener(self, listener):
        """Add a listener to the communicator"""

        if listener is None:
            print("Given listener is empty")
            return False
        if not isinstance(listener, BodynodeListener):
            print("Given listener does not extend BodynodeListener")
            return False
        self.bthc_bodynodes_listeners.append(listener)
        return True

    def remove_listener(self, listener):
        """Remove a listener in the communicator"""

        self.bthc_bodynodes_listeners.remove(listener)

    def remove_all_listeners(self):
        """Remove all listeners in the communicator"""

        self.bthc_bodynodes_listeners = []

    # Private functions

    def __receive_bytes(self):
        """Receive bytes from the socket"""

        for bt_addr, sock in self.bthc_connectors.items():
            message_bytes = None
            try:
                message_bytes = sock.recv(bodynodes_bt["buffer_size"])
            except socket.error:
                # print(f"Error reading from socket: {e}")
                break

            if not message_bytes:
                break

            # print(bt_addr)
            # print(message_bytes)
            connection_str = bt_addr + ""
            if connection_str not in self.bthc_maps["tempConnectionsData"]:
                new_connection_data = {}
                new_connection_data["STATUS"] = "IS_WAITING_ACK"
                new_connection_data["bt_address"] = bt_addr
                self.bthc_maps["tempConnectionsData"][
                    connection_str
                ] = new_connection_data

            connection_data = self.bthc_maps["tempConnectionsData"][connection_str]
            connection_data["num_received_bytes"] = len(message_bytes)
            connection_data["received_bytes"] = message_bytes

    def __send_ackh(self, connection_data):
        """Sends ACKH to a connection"""

        # print("Sending ACKH to = " + connection_data["bt_address"])
        # print(self.bthc_connectors[connection_data["bt_address"]])
        try:
            self.bthc_connectors[connection_data["bt_address"]].send(
                "ACKH".encode("utf-8")
            )
        except socket.error as exc:
            print(exc)
            print("Cannot send ACKH")

    def __check_for_ackn(self, connection_data):
        """Checks if there is an ACK in the connection data. Returns true if there is, false otherwise"""

        if connection_data["num_received_bytes"] < 4:
            # print( "Check for ACKN - not enough bytes = " +str(connection_data["num_received_bytes"]) )
            return False

        for index in range(0, connection_data["num_received_bytes"] - 2):
            # ACKN
            if (
                connection_data["received_bytes"][index] == 65
                and connection_data["received_bytes"][index + 1] == 67
                and connection_data["received_bytes"][index + 2] == 75
                and connection_data["received_bytes"][index + 3] == 78
            ):
                connection_data["last_rec_time"] = current_milli_time()
                return True
        return False

    def __check_for_messages(self, connection_data):
        """Checks if there are messages in the connection data and puts them in jsons"""

        if connection_data["num_received_bytes"] == 0:
            return

        message_str = connection_data["received_bytes"].decode("utf-8")

        index_st = 0
        json_messages = []
        # print( "Original message_str = " + str(message_str) )
        while index_st != -1:
            index_st = message_str.find("{")
            message_str = message_str[index_st:]
            index_end = message_str.find("}")
            remaining_message_str = message_str[index_end + 1 :]
            message_str = message_str[: index_end + 1]
            if message_str == "":
                break

            json_message = None
            try:
                # It loads arrays too
                json_message = json.loads(message_str)
                json_messages.append(json_message)
            except json.decoder.JSONDecodeError as err:
                print(message_str)
                print("Not a valid json: ", err)
            message_str = remaining_message_str

        tmp_connection_str = connection_data["bt_address"]
        self.bthc_maps["tempConnectionsData"][tmp_connection_str][
            "last_rec_time"
        ] = current_milli_time()
        self.__parse_messages(connection_data["bt_address"], json_messages)

    def __parse_messages(self, bt_address, json_messages):
        """Puts the json messages in the messages map and associated them with the connection"""

        for message in json_messages:
            if (
                ("player" not in message)
                or ("bodypart" not in message)
                or ("sensortype" not in message)
                or ("value" not in message)
            ):
                print("Json message received is incomplete\n")
                continue
            player = message["player"]
            bodypart = message["bodypart"]
            sensortype = message["sensortype"]
            self.bthc_maps["connections"][player + "_" + bodypart] = bt_address
            self.bthc_maps["messages"][player + "_" + bodypart + "_" + sensortype] = (
                message["value"]
            )

            for listener in self.bthc_bodynodes_listeners:
                if listener.is_of_interest(player, bodypart, sensortype):
                    listener.on_message_received(
                        player, bodypart, sensortype, message["value"]
                    )


def main():
    """Main function running a default communicator"""

    communicator = BnBluetoothHostCommunicator()
    communicator.start(["24:95:2F:64:68:A6"])
    listener = BodynodeListenerTest()
    command = "n"
    while command != "e":
        command = input(
            "Type a command [r/l/u to read message, h/p/b/s/w to send action, e to exit]: "
        )
        if command == "r":
            outvalue = communicator.get_message_value(
                "mario",
                BnConstants.BODYPART_KATANA_TAG,
                BnConstants.SENSORTYPE_ORIENTATION_ABS_TAG,
            )
            print(outvalue)

        elif command == "l":
            communicator.add_listener(listener)

        elif command == "u":
            communicator.remove_listener(listener)

        elif command == "h":
            action = {
                BnConstants.ACTION_TYPE_TAG: BnConstants.ACTION_TYPE_HAPTIC_TAG,
                BnConstants.ACTION_PLAYER_TAG: "mario",
                BnConstants.ACTION_BODYPART_TAG: BnConstants.BODYPART_KATANA_TAG,
                BnConstants.ACTION_HAPTIC_DURATION_MS_TAG: 250,
                BnConstants.ACTION_HAPTIC_STRENGTH_TAG: 200,
            }
            communicator.add_action(action)

        elif command == "p":
            action = {
                BnConstants.ACTION_TYPE_TAG: BnConstants.ACTION_TYPE_SETPLAYER_TAG,
                BnConstants.ACTION_PLAYER_TAG: "mario",
                BnConstants.ACTION_BODYPART_TAG: BnConstants.BODYPART_KATANA_TAG,
                BnConstants.ACTION_SETPLAYER_NEWPLAYER_TAG: "luigi",
            }
            communicator.add_action(action)

        elif command == "b":
            action = {
                BnConstants.ACTION_TYPE_TAG: BnConstants.ACTION_TYPE_SETBODYPART_TAG,
                BnConstants.ACTION_PLAYER_TAG: "mario",
                BnConstants.ACTION_BODYPART_TAG: BnConstants.BODYPART_KATANA_TAG,
                BnConstants.ACTION_SETBODYPART_NEWBODYPART_TAG: BnConstants.BODYPART_UPPERARM_LEFT_TAG,
            }
            communicator.add_action(action)

        elif command == "s":
            action = {
                BnConstants.ACTION_TYPE_TAG: BnConstants.ACTION_TYPE_ENABLESENSOR_TAG,
                BnConstants.ACTION_PLAYER_TAG: "mario",
                BnConstants.ACTION_BODYPART_TAG: BnConstants.BODYPART_KATANA_TAG,
                BnConstants.ACTION_ENABLESENSOR_SENSORTYPE_TAG: BnConstants.SENSORTYPE_ORIENTATION_ABS_TAG,
                BnConstants.ACTION_ENABLESENSOR_ENABLE_TAG: False,
            }
            communicator.add_action(action)

        communicator.send_all_actions()

    communicator.stop()


if __name__ == "__main__":
    main()
    sys.exit()
