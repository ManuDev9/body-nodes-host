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

#include "messages_mgr.h"

Connections mConnections;
char mBodyparts[MAX_BODYNODES_NUMBER][MAX_BODYPART_LENGTH];
bool mEnabled[MAX_BODYNODES_NUMBER];

// WS -> Data from Wifi to Serial
char mMessagesWS_Type[MAX_BODYNODES_NUMBER][MAX_TYPE_LENGTH];
char mMessagesWS_Value[MAX_BODYNODES_NUMBER][MAX_VALUE_LENGTH];
bool mMessagesWS_Changed[MAX_BODYNODES_NUMBER];

/*
 * Initialize and ensure mBodynodes_messages and mBodynodes are empty
 */
void initMessages(){
  for(unsigned int index = 0; index < MAX_BODYNODES_NUMBER; ++index){
    mBodyparts[index][0] = '\0';
    mEnabled[index] = false;
    mMessagesWS_Type[index][0] = '\0';
    mMessagesWS_Value[index][0] = '\0';
    mMessagesWS_Changed[index] = false;
  }
}

/*
 * Given a bodypart string, the bodypart index will be returned
 */
int get_index_bodypart(IPAddressPort connection, const char *bodypart){
  if(bodypart == nullptr) {
    return -1;
  }
  unsigned int index = 0;
  for( ;index < MAX_BODYNODES_NUMBER && mEnabled[index]; ++index){
    if(strstr(mBodyparts[index], bodypart)!=NULL){
      if(mConnections.conn[index].ip != connection.ip){
          mConnections.conn[index] = connection;
          mConnections.conn_status[index] = CS_WAIT_INIT_ACK;
      }
      return index;
    }
  }
  // If not found create new one
  strcpy(mBodyparts[index], bodypart);
  mConnections.conn[index] = connection;
  mConnections.last_action[index] = Action();
  mConnections.conn_status[index] = CS_WAIT_INIT_ACK;
  mConnections.num_connections = index+1;
  mEnabled[index] = true;
  return index;
}

void store_message(int index_bodypart, const char *mtype, const char *mvalue){
  if( index_bodypart < 0 || MAX_BODYNODES_NUMBER <= index_bodypart ){
    DEBUG_PRINT("Invalid index_bodypart in store_message");
    return;
  }
  strcpy(mMessagesWS_Type[index_bodypart], mtype);
  strcpy(mMessagesWS_Value[index_bodypart], mvalue);
  mMessagesWS_Changed[index_bodypart] = true;
}

void serial_send_messages(){
  String fullMessage ="[";
  bool is_first = true;
  for(unsigned int index = 0;index < MAX_BODYNODES_NUMBER && mEnabled[index]; ++index){
    if(mMessagesWS_Changed[index] == true) {
      if(!is_first){
        fullMessage +=",";        
      }
      is_first = false;
      fullMessage +="{\"bodypart\":\"";
      fullMessage +=mBodyparts[index];
      fullMessage +="\",\"type\":\"";
      fullMessage +=mMessagesWS_Type[index];
      fullMessage +="\",\"value\":\"";
      fullMessage += mMessagesWS_Value[index];
      fullMessage += "\"}";
      mMessagesWS_Changed[index] = false;
    }
  }
  fullMessage += "]";
  if(!is_first){
    Serial.println(fullMessage);
  }
}

void parseMessage(IPAddressPort connection, String message){
  DynamicJsonDocument messagesJson(JSON_ARRAY_SIZE(3) + MAX_BUFF_LENGTH);

  // Deserialize the JSON document
  DeserializationError error = deserializeJson(messagesJson, message);
  // Test if parsing succeeds.
  if (error) {
    return;
  }
  JsonArray jsonArray = messagesJson.as<JsonArray>();
  for(JsonVariant elem : jsonArray) {
    JsonObject messageObj = elem.as<JsonObject>();
    const char* mtype = messageObj["type"];
    const char* mvalue = messageObj["value"];
    const char* mbodypart = messageObj["bodypart"];
    const int index_bp = get_index_bodypart(connection, mbodypart);
    store_message(index_bp, mtype, mvalue);
  }
}

unsigned int manageAck(IPAddressPort connection){
  unsigned int index = 0;
  for( ;index < MAX_BODYNODES_NUMBER && mEnabled[index]; ++index){
    if(mConnections.conn[index].ip == connection.ip){
      break;
    }
  }
  if(index == MAX_BODYNODES_NUMBER){
    return CS_NOTHING;
  }
  if(!mEnabled[index]){
    // This is an ACK coming from a not registered node
    return CS_WAIT_INIT_ACK;
  }

  bool sendAck = true;
  for( ;index < MAX_BODYNODES_NUMBER && mEnabled[index]; ++index){
    if(mConnections.conn[index].ip == connection.ip){
      if(mConnections.conn_status[index] == CS_WAIT_ACTION_ACK){
        mConnections.conn_status[index] = CS_NOTHING;
        sendAck = false;
      }
    }
  }
  if(sendAck){
    return CS_WAIT_INIT_ACK;
  } else {
    return CS_NOTHING;
  }
}

void setActionToNodes(Action action){
  unsigned int index = 0;
  for( ;index < MAX_BODYNODES_NUMBER && mEnabled[index]; ++index){
    if(mConnections.conn[index].port != 0){
      if(action.bodypart[0] == '\0'){ // An empty bodypart action is basically a broadcast
        mConnections.last_action[index] = action;
        mConnections.conn_status[index] = CS_WAIT_ACTION_ACK;
      } else if(strstr(mBodyparts[index], action.bodypart)!=NULL){
        mConnections.last_action[index] = action;
        mConnections.conn_status[index] = CS_WAIT_ACTION_ACK;
        return;
      }
    }
  }
}

Connections &getConnections() {
  return mConnections;
}
