# MIT License
# 
# Copyright (c) 2019-2021 Manuel Bottini
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
  "host" : "192.168.0.167", # Raspberry PI local address, check it with "ifconfig" and change it
  "port" : 12345,
  "buffer_size" : 1024,
  "connection_keep_alive_rec_interval_ms" : 60000,
  "connection_ack_interval_ms" : 1000
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

class WifiHostCommunicator:
	
  # Initializes the object, no input parameters are required
  def __init__(self):
    # Thread to listen for messages
    self.whc_messagesListenerThread = threading.Thread(target=self.run_background)
    # Boolean to stop the thread
    self.whc_toStop = True;
    # Json object containing the messages for each player+bodypart+sensortype combination (key)
    self.whc_messagesMap = {}
    # Map the connections (ip_address) to the player+bodypart combination (key)
    self.whc_connectionsMap = {}
    # Map temporary connections data to an arbitrary string representation of a connection (key)
    self.whc_tempConnectionsDataMap = {}
    # Connector object that can receive and send data
    self.whc_connector = socket(AF_INET, SOCK_DGRAM | SOCK_NONBLOCK)
    # List of actions to send
    self.whc_actionsToSend = []
    self.whc_bodynodesListeners = []

# Public functions

  # Starts the communicator
  def start(self):
    print("WifiHostCommunicator - Starting")
    try:
      self.whc_connector.bind((bodynodes_server["host"], bodynodes_server["port"]))
    except:
      print("Cannot start socket. Is the IP address correct? Or is there any ip connection?")
    self.whc_messagesListenerThread.start()
    
  # Stops the communicator
  def stop(self):
    print("WifiHostCommunicator - Stopping")
    self.whc_toStop = True
    self.whc_connector.close()
    self.whc_bodynodesListeners = []

  # Update function, not in use
  def update(self):
    print("Update function called [NOT IN USE]")
  
  def run_background(self):
    self.whc_toStop = False
    while not self.whc_toStop:
      self.checkAllOk()

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

  # Checks if everything is ok. Returns true if it is indeed ok, false otherwise
  def checkAllOk(self):
    self.__receiveBytes()
    for tmp_connection_str in self.whc_tempConnectionsDataMap.keys():

      #print("Connection to check "+tmp_connection_str+"\n", )
      if self.whc_tempConnectionsDataMap[tmp_connection_str]["received_bytes"] != None:
        #print("Connection to check "+tmp_connection_str+"\n", )
        received_bytes_str = self.whc_tempConnectionsDataMap[tmp_connection_str]["received_bytes"].decode("utf-8")
        #print("Data in the received bytes "+received_bytes_str+"\n" )
        #print("Status connection "+self.whc_tempConnectionsDataMap[tmp_connection_str]["STATUS"] )
        
      if self.whc_tempConnectionsDataMap[tmp_connection_str]["STATUS"] == "IS_WAITING_ACK":
        #print("Connetion is waiting ACK")
        if self.__checkForACK(self.whc_tempConnectionsDataMap[tmp_connection_str]):
          self.__sendACK(self.whc_tempConnectionsDataMap[tmp_connection_str])
          self.whc_tempConnectionsDataMap[tmp_connection_str]["STATUS"]  = "CONNECTED"
      else:
        if current_milli_time() - self.whc_tempConnectionsDataMap[tmp_connection_str]["last_rec_time"] > bodynodes_server["connection_keep_alive_rec_interval_ms"]:
          self.whc_tempConnectionsDataMap[tmp_connection_str]["STATUS"]  = "DISCONNECTED"
        if self.__checkForACK(self.whc_tempConnectionsDataMap[tmp_connection_str]):
          self.__sendACK(self.whc_tempConnectionsDataMap[tmp_connection_str])
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
    #print(ip_address)
    connection_str = ip_address+""
    if connection_str not in self.whc_tempConnectionsDataMap:
      new_connectionData = {}
      new_connectionData["STATUS"] = "IS_WAITING_ACK"
      new_connectionData["ip_address"] = ip_address
      self.whc_tempConnectionsDataMap[connection_str] = new_connectionData
 
    connectionData = self.whc_tempConnectionsDataMap[connection_str]
    connectionData["num_received_bytes"] = len(message_bytes)
    connectionData["received_bytes"] = message_bytes

  # Sends ACK to a connection
  def __sendACK(self, connectionData):
    #print( "Sending ACK to = " +connectionData["ip_address"] )
    self.whc_connector.sendto(str.encode("ACK"), ( connectionData["ip_address"], bodynodes_server["port"] ))

  # Checks if there is an ACK in the connection data. Returns true if there is, false otherwise
  def __checkForACK(self, connectionData):
    if connectionData["num_received_bytes"] < 3:
      return False

    for index in range(0, connectionData["num_received_bytes"] - 2 ):
      # ACK
      if connectionData["received_bytes"][index] == 65 and connectionData["received_bytes"][index+1] == 67 and connectionData["received_bytes"][index+2] == 75 :
        connectionData["last_rec_time"] = current_milli_time()        
        return True
    return False

  # Checks if there are messages in the connection data and puts them in jsons
  def __checkForMessages(self, connectionData):
    if connectionData["num_received_bytes"] == 0:
      return

    message_str = connectionData["received_bytes"].decode("utf-8")
    jsonMessages = None
    try:
      jsonMessages = json.loads(message_str)
    except json.decoder.JSONDecodeError as err:
      print("Not a valid json: ", err)
      
    if jsonMessages == None:
      return

    tmp_connection_str = connectionData["ip_address"]
    self.whc_tempConnectionsDataMap[tmp_connection_str]["last_rec_time"] = current_milli_time()
    if not isinstance(jsonMessages, list):
      jsonMessages = [jsonMessages]

    self.__parseJSON(connectionData["ip_address"], jsonMessages)
    
  # Puts the json messages in the messages map and associated them with the connection
  def __parseJSON(self, ip_address, jsonMessages):
    for message in jsonMessages:	
      if ("player" not in message) or ("bodypart" not in message) or ("sensortype" not in message) or ("value" not in message):
        printf("Json message received is incomplete\n");
        continue
    player = message["player"]
    bodypart = message["bodypart"]
    sensortype = message["sensortype"]
    self.whc_connectionsMap[player+"_"+bodypart] = ip_address;
    self.whc_messagesMap[player+"_"+bodypart+"_"+sensortype] = message["value"];
    
    for listener in self.whc_bodynodesListeners:
      if listener.isOfInterest(player, bodypart, sensortype ):
        listener.onMessageReceived(player, bodypart, sensortype, message["value"])


if __name__=="__main__":
  communicator = WifiHostCommunicator()
  communicator.start()
  listener = BodynodeListenerTest()
  command = "n"
  while command != "e":
    command = input("Type a command [r/l/u ro read message, h/p/b/s/w to send action, e to exit]: ")
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
        "password" : "bodynodes1",
        "server_ip" : "192.168.137.1"
      }
      
      communicator.addAction(action)

    communicator.sendAllActions();
  
  communicator.stop()
  exit()
