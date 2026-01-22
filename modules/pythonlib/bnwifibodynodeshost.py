#
# MIT License
#
# Copyright (c) 2019-2025 Manuel Bottini
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
Module implementation of the WiFi Bodynode Host.
"""

import socket
import threading
import json
import time
import sys

from bncommon import BnConstants

# TO REMOVE
bodynodes_server = {
    "port": 12345,
    "buffer_size": 1024,
    "connection_keep_alive_rec_interval_ms": 60000,
    "connection_ack_interval_ms": 1000,
    "multicast_group": "239.192.1.99",
    "multicast_port": 12346,
    "multicast_ttl": 2,
}


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


class BnWifiHostCommunicator:
    """Bodynodes Wifi Host ommunicator implementation"""

    def __init__(self):
        # Connection threads
        self.whc_connection_threads = {
            "data": None,
            "multicast": None,
        }
        # Boolean to stop the thread
        self.whc_to_stop = True

        self.whc_maps = {
            # Json object containing the messages for each player+bodypart+sensortype combination (key)
            "messages": None,
            # Map the connections (ip_address) to the player+bodypart combination (key)
            "connections": None,
            # Map temporary connections data to an arbitrary string representation of a connection (key)
            "tempconnections_data": None,
        }
        # Connector object that can receive and send data
        self.whc_connectors = {
            "data": None,
            "multicast": None,
        }
        # Connector object that can advertise itself in the network
        # List of actions to send
        self.whc_actions_tosend = None
        self.whc_bodynodes_listeners = []
        self.whc_identifier = None

    # Public functions
    def start(self, communication_parameters):
        """Starts the communicator"""
        print("BnWifiHostCommunicator - Starting")

        self.whc_maps = {
            "messages": {},
            "connections": {},
            "tempconnections_data": {},
        }
        self.whc_connectors = {
            "data": None,
            "multicast": None,
        }
        self.whc_connection_threads = {
            "data": None,
            "multicast": None,
        }
        self.whc_actions_tosend = []
        self.whc_identifier = None

        try:
            self.whc_connectors["data"] = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM | socket.SOCK_NONBLOCK
            )
            self.whc_connectors["multicast"] = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM | socket.SOCK_NONBLOCK,
                socket.IPPROTO_UDP,
            )
        except NameError:
            self.whc_connectors["data"] = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM
            )
            self.whc_connectors["multicast"] = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
            )

        self.whc_connectors["data"].setblocking(False)
        self.whc_connectors["multicast"].setblocking(False)

        self.whc_connection_threads["data"] = threading.Thread(
            target=self.run_data_connection_background
        )
        self.whc_connection_threads["multicast"] = threading.Thread(
            target=self.run_multicast_connection_background
        )

        if communication_parameters is None or len(communication_parameters) != 1:
            print('Please provide a Multicast Identifier, example ["BN"]')
            return

        self.whc_identifier = communication_parameters[0]
        try:
            self.whc_connectors["data"].bind(("", bodynodes_server["port"]))
        except OSError:
            print(
                "Cannot start the data socket. Is the IP address correct? Or is there any ip connection?"
            )

        try:
            print("Interfaces = ")
            all_ifaces = socket.gethostbyname_ex(socket.gethostname())[2]
            print(all_ifaces)

            group = socket.inet_aton(bodynodes_server["multicast_group"])
            # iface = inet_aton(self.whc_host_ip) # Connect the multicast packets on this interface.
            self.whc_connectors["multicast"].setsockopt(
                socket.IPPROTO_IP,
                socket.IP_MULTICAST_TTL,
                bodynodes_server["multicast_ttl"],
            )
            for iface in all_ifaces:
                print("Using interface = " + str(iface))
                self.whc_connectors["multicast"].setsockopt(
                    socket.IPPROTO_IP,
                    socket.IP_ADD_MEMBERSHIP,
                    group + socket.inet_aton(iface),
                )
        except OSError as er:
            print("Cannot start multicast socket. No network connections available?")
            print(er)

        self.whc_to_stop = False
        self.whc_connection_threads["data"].start()
        self.whc_connection_threads["multicast"].start()

    def stop(self):
        """Stops the communicator"""

        print("BnWifiHostCommunicator - Stopping")
        self.whc_to_stop = True
        self.whc_connectors["data"].close()
        self.whc_connectors["multicast"].close()
        self.whc_connection_threads["data"].join()
        self.whc_connection_threads["multicast"].join()
        print("BnWifiHostCommunicator - Stopped!")
        self.whc_bodynodes_listeners = []
        self.whc_connection_threads = {
            "data": None,
            "multicast": None,
        }
        self.whc_connectors = {
            "data": None,
            "multicast": None,
        }
        self.whc_maps = {
            "messages": None,
            "connections": None,
            "tempconnections_data": None,
        }

    def is_running(self):
        """Returns true if the communicator is running, false otherwise"""

        return not self.whc_to_stop

    def update(self):
        """Update function, not in use"""

        print("Update function called [NOT IN USE]")

    def run_data_connection_background(self):
        """Data connection runner function"""

        while not self.whc_to_stop:
            self.check_all_ok()
            time.sleep(0.01)

    def run_multicast_connection_background(self):
        """Multicast connection runner function"""

        while not self.whc_to_stop:
            self.__send_multicast_message()
            time.sleep(5)

    def get_message_value(self, player, bodypart, sensortype):
        """Returns the message associated to the requested player+bodypart+sensortype combination"""

        pbs_key = f"{player}|{bodypart}|{sensortype}"
        if pbs_key in self.whc_maps["messages"]:
            return self.whc_maps["messages"][pbs_key]
        return None

    def add_action(self, action):
        """Adds an action to the list of actions to be sent"""

        self.whc_actions_tosend.append(action)

    def send_all_actions(self):
        """Sends all actions in the list"""

        for action in self.whc_actions_tosend:
            player_bodypart = f"{action[BnConstants.ACTION_PLAYER_TAG]}|{action[BnConstants.ACTION_BODYPART_TAG]}"
            if (
                player_bodypart not in self.whc_maps["connections"]
                or self.whc_maps["connections"][player_bodypart] is None
            ):
                print("Player+Bodypart connection not existing\n")
                continue

            action_str = json.dumps(action)
            self.whc_connectors["data"].sendto(
                str.encode(action_str),
                (self.whc_maps["connections"][player_bodypart], 12345),
            )

        self.whc_actions_tosend = []

    def check_all_ok(self):
        """Checks if everything is ok. Returns true if it is indeed ok, false otherwise"""

        self.__receive_bytes()
        for tempconnections_data in self.whc_maps["tempconnections_data"]:

            # print("Connection to check "+tmp_connection_str+"\n", )
            # if (
            #    tempconnections_data[
            #        "received_bytes"
            #    ]
            #    is not None
            # ):
            # print("Connection to check "+tmp_connection_str+"\n", )
            # received_bytes_str = self.whc_maps["tempconnections_data"][
            #    tmp_connection_str
            # ]["received_bytes"].decode("utf-8")
            # print("Data in the received bytes "+received_bytes_str+"\n" )
            # print("Status connection "
            #   +tempconnections_data["STATUS"] )
            if tempconnections_data["STATUS"] == "IS_WAITING_ACK":
                # print("Connetion is waiting ACKN")
                if self.__check_for_ackn(tempconnections_data):
                    self.__send_ackh(tempconnections_data)
                    tempconnections_data["STATUS"] = "CONNECTED"
            else:
                if (
                    current_milli_time() - tempconnections_data["last_rec_time"]
                    > bodynodes_server["connection_keep_alive_rec_interval_ms"]
                ):
                    tempconnections_data["STATUS"] = "DISCONNECTED"
                if self.__check_for_ackn(tempconnections_data):
                    print("Received ACKN")
                    self.__send_ackh(tempconnections_data)
                else:
                    self.__check_for_messages(tempconnections_data)
            tempconnections_data["received_bytes"] = None
            tempconnections_data["num_received_bytes"] = 0
        return not self.whc_to_stop

    def add_listener(self, listener):
        """Add a listener to the communicator"""

        if listener is None:
            print("Given listener is empty")
            return False
        if not isinstance(listener, BodynodeListener):
            print("Given listener does not extend BodynodeListener")
            return False
        self.whc_bodynodes_listeners.append(listener)
        return True

    def remove_listener(self, listener):
        """Remove a listener in the communicator"""

        self.whc_bodynodes_listeners.remove(listener)

    def remove_all_listeners(self):
        """Remove all listeners in the communicator"""

        self.whc_bodynodes_listeners = []

    # Private functions

    def __receive_bytes(self):
        """Receive bytes from the socket"""

        try:
            bytes_address_pair = self.whc_connectors["data"].recvfrom(
                bodynodes_server["buffer_size"]
            )
        except BlockingIOError:
            return
        except OSError:
            return

        if not bytes_address_pair:
            return

        message_bytes = bytes_address_pair[0]
        ip_address = bytes_address_pair[1][0]
        # print(ip_address)
        # print(message_bytes)
        connection_str = str(ip_address)
        if connection_str not in self.whc_maps["tempconnections_data"]:
            new_connection_data = {}
            new_connection_data["STATUS"] = "IS_WAITING_ACK"
            new_connection_data["ip_address"] = ip_address
            self.whc_maps["tempconnections_data"][connection_str] = new_connection_data

        self.whc_maps["tempconnections_data"][connection_str]["num_received_bytes"] = (
            len(message_bytes)
        )
        self.whc_maps["tempconnections_data"][connection_str][
            "received_bytes"
        ] = message_bytes

    def __send_ackh(self, connection_data):
        """Sends ACKH to a connection"""

        # print( "Sending ACKH to = " +connection_data["ip_address"] )
        self.whc_connectors["data"].sendto(
            str.encode("ACKH"), (connection_data["ip_address"], 12345)
        )

    def __send_multicast_message(self):
        """Sends a message in the multicast channel"""

        # print("self.multicast_socket = "+str(self.multicast_socket))
        # print("Sending a BN multicast: "+str(self.whc_identifier))
        self.whc_connectors["multicast"].sendto(
            self.whc_identifier.encode("utf-8"),
            (bodynodes_server["multicast_group"], bodynodes_server["multicast_port"]),
        )

    def __check_for_ackn(self, connection_data):
        """Checks if there is an ACK in the connection data. Returns true if there is, false otherwise"""

        if connection_data["num_received_bytes"] < 4:
            # print( "Check for ACKN - not enough bytes = "
            #   + str(connection_data["num_received_bytes"]) )
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

        tmp_connection_str = connection_data["ip_address"]
        self.whc_maps["tempconnections_data"][tmp_connection_str][
            "last_rec_time"
        ] = current_milli_time()
        self.__parse_messages(tmp_connection_str, json_messages)

    #
    def __parse_messages(self, ip_address, json_messages):
        """Puts the json messages in the messages map and associated them with the connection"""

        for message in json_messages:
            if (
                (BnConstants.MESSAGE_PLAYER_TAG not in message)
                or (BnConstants.MESSAGE_BODYPART_TAG not in message)
                or (BnConstants.MESSAGE_SENSORTYPE_TAG not in message)
                or (BnConstants.MESSAGE_VALUE_TAG not in message)
            ):
                print("Json message received is incomplete")
                continue
            player = message[BnConstants.MESSAGE_PLAYER_TAG]
            bodypart = message[BnConstants.MESSAGE_BODYPART_TAG]
            sensortype = message[BnConstants.MESSAGE_SENSORTYPE_TAG]

            pb_key = f"{player}|{bodypart}"
            pbs_key = f"{player}|{bodypart}|{sensortype}"

            self.whc_maps["connections"][pb_key] = ip_address
            self.whc_maps["messages"][pbs_key] = message[BnConstants.MESSAGE_VALUE_TAG]

            for listener in self.whc_bodynodes_listeners:
                if listener.isOfInterest(player, bodypart, sensortype):
                    listener.onMessageReceived(
                        player,
                        bodypart,
                        sensortype,
                        message[BnConstants.MESSAGE_VALUE_TAG],
                    )


def main():
    """Main function running a default communicator"""

    communicator = BnWifiHostCommunicator()
    communicator.start(["BN"])
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

        elif command == "w":
            action = {
                BnConstants.ACTION_TYPE_TAG: BnConstants.ACTION_TYPE_SETWIFI_TAG,
                BnConstants.ACTION_PLAYER_TAG: "mario",
                BnConstants.ACTION_BODYPART_TAG: BnConstants.BODYPART_KATANA_TAG,
                BnConstants.MEMORY_WIFI_SSID_TAG: "upperbody",
                BnConstants.MEMORY_WIFI_PASSWORD_TAG: "bodynodes1",
            }

            communicator.add_action(action)

        communicator.send_all_actions()

    communicator.stop()


if __name__ == "__main__":
    main()
    sys.exit()
