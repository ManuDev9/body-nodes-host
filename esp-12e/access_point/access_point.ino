/**
* MIT License
* 
* Copyright (c) 2021 Manuel Bottini
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

#include "basics.h"
#include "wifi_conn.h"
#include "messages_mgr.h"

unsigned long lastSendMessage;

// { "action":"haptic", "duration_ms": 500, "strength" : 250 }
Action getActionFromString(String incomingString){
  Action action;
  action.type = ACTION_NOPE_INT;
  action.duration_ms = 0;
  action.strength = 0;
  
  int indexOpen = incomingString.indexOf("{");
  int indexClose = incomingString.indexOf("}");
  if(indexOpen < 0){
    //No starting point
    return action;
  }
  if(indexOpen > indexClose){
    //we got a starting point after the closing point
    indexClose = incomingString.indexOf("}", indexOpen);
  }
  if(indexClose<0){
    //JSON has not been closed, let's keep what we have and not read from it
    return action;
  }
  incomingString = incomingString.substring(indexOpen, indexClose+1);
  DynamicJsonDocument actionJson(JSON_OBJECT_SIZE(3) +MAX_BUFF_LENGTH);

  // Deserialize the JSON document
  DeserializationError error = deserializeJson(actionJson, incomingString);
  // Test if parsing succeeds.
  if (error) {
    DEBUG_PRINTLN("No possible to parse the json, error =");
    DEBUG_PRINTLN(error.c_str());
    return action;
  }
  deserializeJson(actionJson, incomingString);
  //DEBUG_PRINTLN("actionJson =");
  //serializeJson(actionJson, Serial);
  //DEBUG_PRINTLN("");
  if(actionJson.containsKey(ACTION_ACTION_TAG)){
    const char* actionName = actionJson[ACTION_ACTION_TAG];
    if(strstr(actionName, ACTION_HAPTIC_TAG)!=NULL){
      if(actionJson.containsKey(ACTION_DURATIONMS_TAG) &&
          actionJson.containsKey(ACTION_STRENGTH_TAG)){
        action.type = ACTION_HAPTIC_INT;
        action.duration_ms = actionJson[ACTION_DURATIONMS_TAG];
        action.strength = actionJson[ACTION_STRENGTH_TAG];
        if(actionJson.containsKey(ACTION_BODYPART_TAG)){
          strcpy(action.bodypart, actionJson[ACTION_BODYPART_TAG]);
        } else {
          action.bodypart[0] = '\0';
        }
        action.message = incomingString;
      }
    }
  }
  return action;
}

void setup() {  
  //Initialize serial and wait for port to open:
  Serial.begin(921600);
  initServer();
  initMessages();
  lastSendMessage = 0;
}

void loop() {
  String incomingMessage;

  // Wifi SNodes
  IPAddressPort connection_rec = get_snodes_udp_packets(incomingMessage);
  if(strstr(incomingMessage.c_str(), "ACK")  != NULL){
    if(manageAck(connection_rec) == CS_WAIT_INIT_ACK){
      sendACK(connection_rec);
    }
  } else {
    parseMessage(connection_rec, incomingMessage);
  }

  // Wifi Nodes
  incomingMessage = "";
  connection_rec = get_nodes_udp_packets(incomingMessage);
  if(strstr(incomingMessage.c_str(), "ACK")  != NULL){
    if(manageAck(connection_rec) == CS_WAIT_INIT_ACK){
      sendACK(connection_rec);
    }
  } else {
    parseMessage(connection_rec, incomingMessage);
  }

  if(Serial.available( ) > 0) {
    String incomingString = Serial.readString();
    Action action = getActionFromString(incomingString);
    if(action.message.length() > 0){
      setActionToNodes(action);
    }
  }

  // Messages will be sent every 30 milliseconds
  if(millis() - lastSendMessage > MESSAGES_SEND_PERIOD_MS){
    lastSendMessage = millis();
    serial_send_messages();
    sendActions(getConnections());
  }
}
