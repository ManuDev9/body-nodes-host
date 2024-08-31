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
import threading
import json
import time
import bluetooth
import uuid

# sudo apt-get update
# sudo apt-get install libbluetooth-dev
# sudo apt-get install python3-bluez
# pip install pybluez
# bluetoothctl show
#              power on
#              power off
#              discoverable on
#              pairable on
#              pair
# rfkill list bluetooth
# Name: Pixel A - Address: 13:95:2G:61:6P:C6
#              pair 13:95:2G:61:6P:A6
#              connect 13:95:2G:61:6P:C6
#              info 13:95:2G:61:6P:C6
#        UUID: Serial Port               (00001101-0000-1000-8000-00805f9b34fb)
#
# It is best to first run the app, and then pair it to propertly discover the UUID Serial Port
# otherwise it might be seen. NOTE: This happens ONlY the first time the Host pair to the Node


bodynodes_bt = {
  "buffer_size" : 1024,
  "connection_keep_alive_rec_interval_ms" : 60000,
  "connection_ack_interval_ms" : 1000,

  # This is the common UUID of the service to look for

  "nodes_UUID" : "00001101-0000-1000-8000-00805f9b34fb",

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

# This is class that helps in the conversion of data
class BodynodesData:
  def __init__(self):
    self.reorient_axis = { "new_w" : 0, "new_x" : 1, "new_y" : 2, "new_z" : 3  }
    self.reorient_sign = { "w" : 1, "x" : 1, "y" : 1, "z" : 1  }

  # Change the orientation of received data to align to the main application
  # new_axis is an array of 4 integer that can be 0 ('w'), 1 ('x'), 2 ('y'), or 3 ('z').
  # Example [ 0, 1, 2, 3]
  # signs is an array of 4 integers that can be 1 or -1. Example [1, 1, 1, 1]
  # Note: by default the orientation is set as [ 0, 1, 2, 3 ] and [1, 1, 1, 1] 
  def configOrientationAbs( self, new_axis, signs ):
    self.reorient_axis["new_w"] = new_axis[0]
    self.reorient_axis["new_x"] = new_axis[1]
    self.reorient_axis["new_y"] = new_axis[2]
    self.reorient_axis["new_z"] = new_axis[3]
    self.reorient_sign["w"] = signs[0]
    self.reorient_sign["x"] = signs[1]
    self.reorient_sign["y"] = signs[2]
    self.reorient_sign["z"] = signs[3]

  def changeOrientationAbs( self, values ):
    oW = values[ self.reorient_axis["new_w"] ] * self.reorient_sign["w"]
    oX = values[ self.reorient_axis["new_x"] ] * self.reorient_sign["x"]
    oY = values[ self.reorient_axis["new_y"] ] * self.reorient_sign["y"]
    oZ = values[ self.reorient_axis["new_z"] ] * self.reorient_sign["z"]
    return [ oW, oX, oY, oZ ]

class BnBluetoothHostCommunicator:

  # Initializes the object, no input parameters are required
  def __init__(self):
    # Thread for data connection
    self.bthc_dataConnectionThread = threading.Thread(target=self.run_data_connection_background)
    # Boolean to stop the thread
    self.bthc_toStop = True;
    # Json object containing the messages for each player+bodypart+sensortype combination (key)
    self.bthc_messagesMap = {}
    # Map the connections (bt_address) to the player+bodypart combination (key)
    self.bthc_connectionsMap = {}
    # Map temporary connections data to an arbitrary string representation of a connection (key)
    self.bthc_tempConnectionsDataMap = {}
    # Dictionary of bluetooth address / connector objects that can receive and send data
    self.bthc_connectors = {}
    # List of actions to send
    self.bthc_actionsToSend = []
    self.bthc_bodynodesListeners = []

# Public functions

  # Starts the communicator
  def start(self, identifiers):
    # You are supposed to discover the bt_addresses yourself
    # Do also a pairing, connect, and if you want, trust
    # make use of bluetoothctl
    print("BnBluetoothHostCommunicator - Starting")

    for bt_addr in identifiers:
      print(f"Trying to connect to {bt_addr}")
 
      service_matches = bluetooth.find_service(uuid=bodynodes_bt["nodes_UUID"], address=bt_addr)
      if len(service_matches) == 0:
          print("Couldn't find the specified UUID service.")
          continue

      for svc in service_matches:
        print(f"Found service: {svc['name']} at {svc['host']}")

        # Connect to the service
        port = svc['port']
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        try:
            sock.connect((bt_addr, port))
            print(f"Connected to {bt_addr}")

            sock.setblocking(0)
            self.bthc_connectors[bt_addr] = sock

        except bluetooth.BluetoothError as e:
            print(f"Connection failed: {e}")


    self.bthc_toStop = False
    self.bthc_dataConnectionThread.start()

  # Stops the communicator
  def stop(self):
    print("BnBluetoothHostCommunicator - Stopping")
    self.bthc_toStop = True
    for bt_addr in self.bthc_connectors.keys():
      self.bthc_connectors[bt_addr].close()
    self.bthc_bodynodesListeners = []

  # Update function, not in use
  def update(self):
    print("Update function called [NOT IN USE]")

  def run_data_connection_background(self):
    while not self.bthc_toStop:
      self.checkAllOk()
      time.sleep(0.01)

  # Returns the message associated to the requested player+bodypart+sensortype combination
  def getMessageValue(self, player, bodypart, sensortype):
    if player+"_"+bodypart+"_"+sensortype in self.bthc_messagesMap:
      return self.bthc_messagesMap[player+"_"+bodypart+"_"+sensortype]
    return None

  # Adds an action to the list of actions to be sent
  def addAction(self, action):
    self.bthc_actionsToSend.append(action);
    
  # Sends all actions in the list
  def sendAllActions(self):
    for action in self.bthc_actionsToSend:
      player_bodypart = action["player"] + "_" + action["bodypart"]
      if player_bodypart not in self.bthc_connectionsMap or self.bthc_connectionsMap[player_bodypart] == None:
        print("Player+Bodypart connection not existing\n")
        continue
      action_str = json.dumps(action)
      self.bthc_connectors[self.bthc_connectionsMap[player_bodypart]].send(action_str.encode("utf-8"))

  # Checks if everything is ok. Returns true if it is indeed ok, false otherwise
  def checkAllOk(self):
    self.__receiveBytes()
    for tmp_connection_str in self.bthc_tempConnectionsDataMap.keys():

      #print("Connection to check "+tmp_connection_str+"\n", )
      if self.bthc_tempConnectionsDataMap[tmp_connection_str]["received_bytes"] != None:
        #print("Connection to check "+tmp_connection_str+"\n", )
        received_bytes_str = self.bthc_tempConnectionsDataMap[tmp_connection_str]["received_bytes"].decode("utf-8")
        # print("Data in the received bytes "+received_bytes_str+"\n" )
        # print("Status connection "+self.bthc_tempConnectionsDataMap[tmp_connection_str]["STATUS"] )

      if self.bthc_tempConnectionsDataMap[tmp_connection_str]["STATUS"] == "IS_WAITING_ACK":
        #print("Connetion is waiting ACKN")
        if self.__checkForACKN(self.bthc_tempConnectionsDataMap[tmp_connection_str]):
          self.__sendACKH(self.bthc_tempConnectionsDataMap[tmp_connection_str])
          self.bthc_tempConnectionsDataMap[tmp_connection_str]["STATUS"]  = "CONNECTED"
      else:
        if current_milli_time() - self.bthc_tempConnectionsDataMap[tmp_connection_str]["last_rec_time"] > bodynodes_bt["connection_keep_alive_rec_interval_ms"]:
          self.bthc_tempConnectionsDataMap[tmp_connection_str]["STATUS"]  = "DISCONNECTED"
        if self.__checkForACKN(self.bthc_tempConnectionsDataMap[tmp_connection_str]):
          print("Received ACKN")
        else:
          self.__checkForMessages(self.bthc_tempConnectionsDataMap[tmp_connection_str])
      self.bthc_tempConnectionsDataMap[tmp_connection_str]["received_bytes"] = None
      self.bthc_tempConnectionsDataMap[tmp_connection_str]["num_received_bytes"] = 0
    return not self.bthc_toStop

  def addListener(self, listener):
    if listener == None:
      print("Given listener is empty")
      return False
    if not isinstance(listener, BodynodeListener):
      print("Given listener does not extend BodynodeListener")
      return False
    self.bthc_bodynodesListeners.append(listener)
    return True    
    
  def removeListener(self, listener):
    self.bthc_bodynodesListeners.remove(listener)
  
  def removeAllListeners(self):
    self.bthc_bodynodesListeners = []

# Private functions

  # Receive bytes from the socket
  def __receiveBytes(self):
    for bt_addr in self.bthc_connectors.keys():
      message_bytes = None
      sock = self.bthc_connectors[bt_addr]
      try:
        message_bytes = sock.recv(bodynodes_bt["buffer_size"])
      except bluetooth.BluetoothError as e:
        #print(f"Error reading from socket: {e}")
        break

      if not message_bytes:
        break

      #print(bt_addr)
      #print(message_bytes)
      connection_str = bt_addr+""
      if connection_str not in self.bthc_tempConnectionsDataMap:
        new_connectionData = {}
        new_connectionData["STATUS"] = "IS_WAITING_ACK"
        new_connectionData["bt_address"] = bt_addr
        self.bthc_tempConnectionsDataMap[connection_str] = new_connectionData
   
      connectionData = self.bthc_tempConnectionsDataMap[connection_str]
      connectionData["num_received_bytes"] = len(message_bytes)
      connectionData["received_bytes"] = message_bytes

  # Sends ACKH to a connection
  def __sendACKH(self, connectionData):
    print( "Sending ACK to = " +connectionData["bt_address"] )
    self.bthc_connectors[connectionData["bt_address"]].send("ACKH".encode("utf-8"))

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

    tmp_connection_str = connectionData["bt_address"]
    self.bthc_tempConnectionsDataMap[tmp_connection_str]["last_rec_time"] = current_milli_time()
    self.__parseMessages(connectionData["bt_address"], jsonMessages)
    
  # Puts the json messages in the messages map and associated them with the connection
  def __parseMessages(self, bt_address, jsonMessages):
    for message in jsonMessages:	
      if ("player" not in message) or ("bodypart" not in message) or ("sensortype" not in message) or ("value" not in message):
        printf("Json message received is incomplete\n");
        continue
      player = message["player"]
      bodypart = message["bodypart"]
      sensortype = message["sensortype"]
      self.bthc_connectionsMap[player+"_"+bodypart] = bt_address;
      self.bthc_messagesMap[player+"_"+bodypart+"_"+sensortype] = message["value"];
    
      for listener in self.bthc_bodynodesListeners:
        if listener.isOfInterest(player, bodypart, sensortype ):
          listener.onMessageReceived(player, bodypart, sensortype, message["value"])


if __name__=="__main__":
  communicator = BnBluetoothHostCommunicator()
  communicator.start(["24:95:2F:64:68:A6"])
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
