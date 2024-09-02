#
# MIT License
# 
# Copyright (c) 2019-2024 Manuel Bottini
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

from socket import *
import os
import sys
import threading
import json
import time

bodynodes_server = {
    "port" : 12345,
    "buffer_size" : 1024,
    "connection_keep_alive_rec_interval_ms" : 60000,
    "connection_ack_interval_ms" : 1000,
    "multicast_group" : "239.192.1.99",
    "multicast_port" : 12346,
    "multicast_ttl" : 2,
}

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

class BnWifiHostCommunicator:
    # Initializes the object, no input parameters are required
    def __init__(self):
        # Thread for data connection
        self.whc_dataConnectionThread = None
        # Thread to multicast ACKH
        self.whc_multicastConnectionThread = None
        # Boolean to stop the thread
        self.whc_toStop = True;
        # Json object containing the messages for each player+bodypart+sensortype combination (key)
        self.whc_messagesMap = None
        # Map the connections (ip_address) to the player+bodypart combination (key)
        self.whc_connectionsMap = None
        # Map temporary connections data to an arbitrary string representation of a connection (key)
        self.whc_tempConnectionsDataMap = None
        # Connector object that can receive and send data
        self.whc_connector = None
        # Connector object that can advertise itself in the network
        self.whc_multicast_connector = None
        # List of actions to send
        self.whc_actionsToSend = None
        self.whc_bodynodesListeners = None
        self.whc_identifier = None

# Public functions

    # Starts the communicator
    def start(self, communicationParameters):
        print("BnWifiHostCommunicator - Starting")

        self.whc_messagesMap = {}
        self.whc_connectionsMap = {}
        self.whc_tempConnectionsDataMap = {}
        self.whc_connector = None
        self.whc_multicast_connector = None
        self.whc_actionsToSend = []
        self.whc_bodynodesListeners = []
        self.whc_identifier = None
        
        try:
                self.whc_connector = socket(AF_INET, SOCK_DGRAM | SOCK_NONBLOCK)
                self.whc_multicast_connector = socket(AF_INET, SOCK_DGRAM | SOCK_NONBLOCK, IPPROTO_UDP)
        except NameError:
                self.whc_connector = socket(AF_INET, SOCK_DGRAM )
                self.whc_multicast_connector = socket(AF_INET, SOCK_DGRAM , IPPROTO_UDP)
        self.whc_connector.setblocking(False) 
        self.whc_multicast_connector.setblocking(False)

        self.whc_dataConnectionThread = threading.Thread(target=self.run_data_connection_background)
        self.whc_multicastConnectionThread = threading.Thread(target=self.run_multicast_connection_background)

        if communicationParameters == None or len(communicationParameters) != 1:
            print("Please provide a Multicast Identifier, example [\"BN\"]")
            return 
     
        self.whc_identifier = communicationParameters[0]

        try:
            self.whc_connector.bind(('', bodynodes_server["port"]))
        except:
            print("Cannot start socket. Is the IP address correct? Or is there any ip connection?")

        try:
            print("Interfaces = ")
            all_ifaces = gethostbyname_ex(gethostname())[2]
            print(all_ifaces)
            
            group = inet_aton(bodynodes_server["multicast_group"])
            #iface = inet_aton(self.whc_host_ip) # Connect the multicast packets on this interface.
            self.whc_multicast_connector.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, bodynodes_server["multicast_ttl"])
            for iface in all_ifaces:
                print("Using interface = " + str(iface))
                self.whc_multicast_connector.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, group+inet_aton(iface))
        except Exception as er:
            print("Cannot start multicast socket. No network connections available?")
            print(er)
        
        self.whc_toStop = False
        self.whc_dataConnectionThread.start()
        self.whc_multicastConnectionThread.start()
        
    # Stops the communicator
    def stop(self):
        print("BnWifiHostCommunicator - Stopping")
        self.whc_toStop = True
        self.whc_connector.close()
        self.whc_multicast_connector.close()
        self.whc_dataConnectionThread.join()
        self.whc_multicastConnectionThread.join()
        print("BnWifiHostCommunicator - Stopped!")
        self.whc_bodynodesListeners = []

        self.whc_dataConnectionThread = None
        self.whc_multicastConnectionThread = None
        self.whc_connector = None
        self.whc_multicast_connector = None

    # Indicates if the host is running and listening
    def isRunning(self):
        return not self.whc_toStop

    # Update function, not in use
    def update(self):
        print("Update function called [NOT IN USE]")

    def run_data_connection_background(self):
        while not self.whc_toStop:
            self.checkAllOk()
            time.sleep(0.01)

    def run_multicast_connection_background(self):
        while not self.whc_toStop:
            self.__sendMulticastBN()
            time.sleep(5)

    # Returns the message associated to the requested player+bodypart+sensortype combination
    def getMessageValue(self, player, bodypart, sensortype):
        if player+"_"+bodypart+"_"+sensortype in self.whc_messagesMap:
            return self.whc_messagesMap[player+"_"+bodypart+"_"+sensortype]
        return None

    # Adds an action to the list of actions to be sent
    def addAction(self, action):
        self.whc_actionsToSend.append(action);
        
    # Sends all actions in the list
    def sendAllActions(self):
        for action in self.whc_actionsToSend:
            player_bodypart = action["player"] + "_" + action["bodypart"]
            if player_bodypart not in self.whc_connectionsMap or self.whc_connectionsMap[player_bodypart] == None:
                print("Player+Bodypart connection not existing\n")
                continue
            action_str = json.dumps(action)
            self.whc_connector.sendto(str.encode(action_str), (self.whc_connectionsMap[player_bodypart], 12345))

        self.whc_actionsToSend = []

    # Checks if everything is ok. Returns true if it is indeed ok, false otherwise
    def checkAllOk(self):
        self.__receiveBytes()
        for tmp_connection_str in self.whc_tempConnectionsDataMap.keys():

            #print("Connection to check "+tmp_connection_str+"\n", )
            if self.whc_tempConnectionsDataMap[tmp_connection_str]["received_bytes"] != None:
                #print("Connection to check "+tmp_connection_str+"\n", )
                received_bytes_str = self.whc_tempConnectionsDataMap[tmp_connection_str]["received_bytes"].decode("utf-8")
                # print("Data in the received bytes "+received_bytes_str+"\n" )
                # print("Status connection "+self.whc_tempConnectionsDataMap[tmp_connection_str]["STATUS"] )

            if self.whc_tempConnectionsDataMap[tmp_connection_str]["STATUS"] == "IS_WAITING_ACK":
                #print("Connetion is waiting ACKN")
                if self.__checkForACKN(self.whc_tempConnectionsDataMap[tmp_connection_str]):
                    self.__sendACKH(self.whc_tempConnectionsDataMap[tmp_connection_str])
                    self.whc_tempConnectionsDataMap[tmp_connection_str]["STATUS"]    = "CONNECTED"
            else:
                if current_milli_time() - self.whc_tempConnectionsDataMap[tmp_connection_str]["last_rec_time"] > bodynodes_server["connection_keep_alive_rec_interval_ms"]:
                    self.whc_tempConnectionsDataMap[tmp_connection_str]["STATUS"]    = "DISCONNECTED"
                if self.__checkForACKN(self.whc_tempConnectionsDataMap[tmp_connection_str]):
                    print("Received ACKN")
                    self.__sendACKH(self.whc_tempConnectionsDataMap[tmp_connection_str])
                else:
                    self.__checkForMessages(self.whc_tempConnectionsDataMap[tmp_connection_str])
            self.whc_tempConnectionsDataMap[tmp_connection_str]["received_bytes"] = None
            self.whc_tempConnectionsDataMap[tmp_connection_str]["num_received_bytes"] = 0
        return not self.whc_toStop

    def addListener(self, listener):
        if listener == None:
            print("Given listener is empty")
            return False
        if not isinstance(listener, BodynodeListener):
            print("Given listener does not extend BodynodeListener")
            return False
        self.whc_bodynodesListeners.append(listener)
        return True        
        
    def removeListener(self, listener):
        self.whc_bodynodesListeners.remove(listener)
    
    def removeAllListeners(self):
        self.whc_bodynodesListeners = []

# Private functions

    # Receive bytes from the socket
    def __receiveBytes(self):
        try:
            bytesAddressPair = self.whc_connector.recvfrom(bodynodes_server["buffer_size"])
        except BlockingIOError:
            return
        except OSError:
            return

        if not bytesAddressPair:
            return

        message_bytes = bytesAddressPair[0]
        ip_address = bytesAddressPair[1][0]
        # print(ip_address)
        # print(message_bytes)
        connection_str = ip_address+""
        if connection_str not in self.whc_tempConnectionsDataMap:
            new_connectionData = {}
            new_connectionData["STATUS"] = "IS_WAITING_ACK"
            new_connectionData["ip_address"] = ip_address
            self.whc_tempConnectionsDataMap[connection_str] = new_connectionData
 
        connectionData = self.whc_tempConnectionsDataMap[connection_str]
        connectionData["num_received_bytes"] = len(message_bytes)
        connectionData["received_bytes"] = message_bytes

    # Sends ACKH to a connection
    def __sendACKH(self, connectionData):
        # print( "Sending ACKH to = " +connectionData["ip_address"] )
        self.whc_connector.sendto(str.encode("ACKH"), (connectionData["ip_address"], 12345))

    # Sends ACKH to a connection
    def __sendMulticastBN(self):
        #print("self.multicast_socket = "+str(self.multicast_socket))
        #print("Sending a BN multicast: "+str(self.whc_identifier))
        self.whc_multicast_connector.sendto(self.whc_identifier.encode('utf-8'), (bodynodes_server["multicast_group"], bodynodes_server["multicast_port"]))

    # Checks if there is an ACK in the connection data. Returns true if there is, false otherwise
    def __checkForACKN(self, connectionData):
        if connectionData["num_received_bytes"] < 4:
            #print( "Check for ACKN - not enough bytes = " +str(connectionData["num_received_bytes"]) )
            return False

        for index in range(0, connectionData["num_received_bytes"] - 2 ):
            # ACKN
            if connectionData["received_bytes"][index] == 65 and connectionData["received_bytes"][index+1] == 67 and connectionData["received_bytes"][index+2] == 75 and connectionData["received_bytes"][index+3] == 78:
                connectionData["last_rec_time"] = current_milli_time()                
                return True
        return False

    # Checks if there are messages in the connection data and puts them in jsons
    def __checkForMessages(self, connectionData):
        if connectionData["num_received_bytes"] == 0:
            return

        message_str = connectionData["received_bytes"].decode("utf-8")

        index_st = 0
        jsonMessages = []
        #print( "Original message_str = " + str(message_str) )
        while index_st != -1:
            index_st = message_str.find("{")
            message_str = message_str[index_st:] 
            index_end = message_str.find("}")
            remaining_message_str = message_str[index_end+1:]
            message_str = message_str[:index_end+1]
            if message_str == "":
                break;

            jsonMessage = None
            try:
                # It loads arrays too
                jsonMessage = json.loads(message_str)
                jsonMessages.append(jsonMessage)
            except json.decoder.JSONDecodeError as err:
                print(message_str)
                print("Not a valid json: ", err)
            message_str = remaining_message_str

        tmp_connection_str = connectionData["ip_address"]
        self.whc_tempConnectionsDataMap[tmp_connection_str]["last_rec_time"] = current_milli_time()
        self.__parseMessages(connectionData["ip_address"], jsonMessages)
        
    # Puts the json messages in the messages map and associated them with the connection
    def __parseMessages(self, ip_address, jsonMessages):
        for message in jsonMessages:	
            if ("player" not in message) or ("bodypart" not in message) or ("sensortype" not in message) or ("value" not in message):
                printf("Json message received is incomplete\n");
                continue
            player = message["player"]
            bodypart = message["bodypart"]
            sensortype = message["sensortype"]
            self.whc_connectionsMap[player+"_"+bodypart] = ip_address
            self.whc_messagesMap[player+"_"+bodypart+"_"+sensortype] = message["value"]
        
            for listener in self.whc_bodynodesListeners:
                if listener.isOfInterest(player, bodypart, sensortype ):
                    listener.onMessageReceived(player, bodypart, sensortype, message["value"])


if __name__=="__main__":
    communicator = BnWifiHostCommunicator()
    communicator.start(["BN"])
    listener = BodynodeListenerTest()
    command = "n"
    while command != "e":
        command = input("Type a command [r/l/u to read message, h/p/b/s/w to send action, e to exit]: ")
        if command == "r":
            outvalue = communicator.getMessageValue("mario", "katana", "orientation_abs")
            print(outvalue)

        elif command == 'l':
            communicator.addListener(listener)
            
        elif command == 'u':
            communicator.removeListener(listener)
            
        elif command == 'h':
            action = {
                "type" : "haptic",
                "player" : "mario",
                "bodypart" : "katana",
                "duration_ms" : 250,
                "strength" : 200
            }
            communicator.addAction(action)

        elif command == 'p':
            action = {
                "type" : "set_player",
                "player" : "mario",
                "bodypart" : "katana",
                "new_player" : "luigi"
            }
            communicator.addAction(action)

        elif command == 'b':
            action = {
                "type" : "set_bodypart",
                "player" : "mario",
                "bodypart" : "katana",
                "new_bodypart" : "upperarm_left"
            }
            communicator.addAction(action)

        elif command == 's':
            action = {
                "type" : "enable_sensor",
                "player" : "mario",
                "bodypart" : "katana",
                "sensortype" : "orientation_abs",
                "enable" : False
            }
            communicator.addAction(action)

        elif command == 'w':
            action = {
                "type" : "set_wifi",
                "player" : "mario",
                "bodypart" : "katana",
                "ssid" : "upperbody",
                "password" : "bodynodes1"
            }
            
            communicator.addAction(action)

        communicator.sendAllActions();
    
    communicator.stop()
    exit()
