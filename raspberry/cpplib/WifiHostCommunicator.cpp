
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
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

#include "WifiHostCommunicator.h"

#include <stdio.h>
#include <sys/time.h>
#include <iostream>
#include <unistd.h>
#include <sys/types.h> 

void startFun(WifiHostCommunicator *comm) {
  comm->run_background();
}

void WifiHostCommunicator::start() {
  whc_toStop = false;
  // create a UDP socket
  if ((whc_connector.socket_id =socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1) {
    printf("Couldn't start socket\n");
	whc_toStop = true;
  }
  
  // zero out the structure
  memset((char *) &whc_connector.ip_address, 0, sizeof(whc_connector.ip_address));
  
  whc_connector.ip_address.sin_family = AF_INET;
  whc_connector.ip_address.sin_port = htons(BODYNODES_PORT);
  whc_connector.ip_address.sin_addr.s_addr = htonl(INADDR_ANY);

  // set a receive time-out for the socket 
  struct timeval read_timeout;
  read_timeout.tv_sec = 0;
  read_timeout.tv_usec = 10000;
  setsockopt(whc_connector.socket_id, SOL_SOCKET, SO_RCVTIMEO, &read_timeout, sizeof read_timeout);
  
  // bind socket to port
  if( bind(whc_connector.socket_id , (sockaddr*)&whc_connector.ip_address, sizeof(whc_connector.ip_address) ) == -1) {
    printf("Couldn't bind socket to port\n");
	whc_toStop = true;
  }
  if(!whc_toStop) {
    whc_messagesListenerThread = std::thread(&startFun, this);
  }
}

void WifiHostCommunicator::stop() {
  whc_toStop = true;
  close(whc_connector.socket_id);
  whc_messagesListenerThread.join();
  removeAllListeners();
}

void WifiHostCommunicator::update() {
  printf("WifiHostCommunicator::update()\n");
}

bool WifiHostCommunicator::getMessageValue(
  std::string player,
  std::string bodypart,
  std::string sensortype,
  float outvalue[]) {

  if(!whc_messagesMap.contains(player+"_"+bodypart+"_"+sensortype)){
    return false;
  }

  nlohmann::json value_json = whc_messagesMap[player+"_"+bodypart+"_"+sensortype];
  uint8_t counter = 0;
  for (auto& elem : value_json.items()) {
    outvalue[counter] = elem.value();
    counter++;
  }
  return true;  
}

void WifiHostCommunicator::addAction(nlohmann::json &action) {
  whc_actionsToSend.push_back(action);
}

void WifiHostCommunicator::sendAllActions() {
  for (auto const& action : whc_actionsToSend) {
    std::cout << "action: " << action << '\n';
    std::string player_bodypart = action[ACTION_PLAYER_TAG];
    player_bodypart.append("_");
    player_bodypart.append(action[ACTION_BODYPART_TAG]);
	if(whc_connectionsMap.count(player_bodypart) == 0){
      printf("Player+Bodypart connection not existing\n");
      continue;
	}
    sockaddr_in remote_socket = whc_connectionsMap[player_bodypart];
    std::string action_str = action.dump();     
	int slen = sizeof(remote_socket);
    if (sendto(whc_connector.socket_id, action_str.c_str() , action_str.size() , 0, (struct sockaddr*) &remote_socket, slen) == -1) {
      printf("Couldn't send ACK\n");
    }

  }
  whc_actionsToSend.clear();
}

bool WifiHostCommunicator::checkAllOk() {
  receiveBytes();
  
  std::map<std::string, IPConnectionData>::iterator iter = whc_tempConnectionsDataMap.begin();
    // Iterate over the map using Iterator till end.
  while (iter != whc_tempConnectionsDataMap.end()) {
    // Accessing VALUE from element pointed by iter.
    IPConnectionData *connectionData = &iter->second;
    //printf("Connection to check %s\n", iter->first.c_str());
    //printf("Data in the received bytes %s\n", connectionData->received_bytes );
    
    if(connectionData->isWaitingACK()) {
	  //printf("connectionData->isWaitingACK()\n");
      if(checkForACK(*connectionData)) {
	    sendACK(*connectionData);
        connectionData->setConnected();
      }
    } else {
      if( time(0) - connectionData->last_rec_time > CONNECTION_KEEP_ALIVE_REC_INTERVAL_MS ) {
        connectionData->setDisconnected();
      }
      if(checkForACK(*connectionData)) {
	    sendACK(*connectionData);
      } else {
        checkForMessages(*connectionData);
	  }
    }
    connectionData->cleanBytes();
    // Increment the Iterator to point to next entry
    iter++;
  }
  return !whc_toStop;
}

void WifiHostCommunicator::run_background() {
  while(checkAllOk());
}

bool WifiHostCommunicator::addListener(BodynodeListener *listener) {
  if(listener!=nullptr) {
    whc_bodynodesListeners.push_back(listener);
    return true;
  }
  return false;
}

void WifiHostCommunicator::removeListener(BodynodeListener *listener) {
  if(listener!=nullptr) {
    whc_bodynodesListeners.remove(listener);
  }
}

void WifiHostCommunicator::removeAllListeners() {
  whc_bodynodesListeners.clear();
}

void WifiHostCommunicator::receiveBytes() {
  sockaddr_in remote_socket;
  unsigned int socket_len = sizeof(remote_socket);
  int num_bytes = 0;
  char tmp_buf[MAX_BUFFER_LENGTH];
  //try to receive some data, this is a blocking call
  if ((num_bytes = recvfrom(whc_connector.socket_id, tmp_buf, MAX_BUFFER_LENGTH, 0, (sockaddr *) &remote_socket, &socket_len)) == -1) {
    //printf("Not received anything\n");
    return;
  }
  if(num_bytes > 0) {
    //print details of the client/peer and the data received
    std::string connection_str = inet_ntoa(remote_socket.sin_addr);
    //printf("Received packet from %s:%d\n", connection_str.c_str(), ntohs(remote_socket.sin_port));
    //printf("Data: %s\n" , tmp_buf);
    if(whc_tempConnectionsDataMap.count(connection_str) == 0){
	  IPConnectionData new_connectionData;
	  new_connectionData.setWaitingACK();
	  new_connectionData.ip_address = remote_socket;
	  whc_tempConnectionsDataMap[connection_str] = new_connectionData;
	}
    IPConnectionData &connectionData = whc_tempConnectionsDataMap[connection_str];
    connectionData.num_received_bytes = num_bytes;
    memcpy(connectionData.received_bytes, tmp_buf, num_bytes);
  }
}

void WifiHostCommunicator::sendACK(IPConnectionData &connectionData) {
  char tmp_buf[4] = {'A', 'C', 'K', '\0'};
  int slen = sizeof(connectionData.ip_address);
  if (sendto(whc_connector.socket_id, tmp_buf, 4, 0, (struct sockaddr*) &connectionData.ip_address, slen) == -1) {
    printf("Couldn't send ACK\n");
  }
}

bool WifiHostCommunicator::checkForACK(IPConnectionData &connectionData) {
  for(uint16_t index = 0; index< connectionData.num_received_bytes-2;++index){
    if(connectionData.received_bytes[index] == 'A' && connectionData.received_bytes[index+1] == 'C' && connectionData.received_bytes[index+2] == 'K') {
      connectionData.last_rec_time = time(0);
      return true;
    }
  }
  return false;
}

void WifiHostCommunicator::checkForMessages(IPConnectionData &connectionData) {
  if(connectionData.num_received_bytes > 0 ) {
    //std::cout << "checkForMessages - connetionData.received_bytes =" << connectionData.received_bytes << '\n';
    nlohmann::json jsonMessages = nlohmann::json::parse(connectionData.received_bytes);
    parseJSON(connectionData.ip_address, jsonMessages);
    connectionData.last_rec_time = time(0);
  }
}

void WifiHostCommunicator::parseJSON(sockaddr_in &connection, nlohmann::json &jsonMessages) {
  //printf("WifiHostCommunicator::parseJSON\n");
  for (auto& elem : jsonMessages.items()) {
    //std::cout << "key: " << message.key() << ", value:" << message.value() << '\n';
    nlohmann::json message = elem.value();
    //std::cout << "message: " << message << '\n';
    if(!message.contains(MESSAGE_PLAYER_TAG) ||
      !message.contains(MESSAGE_BODYPART_TAG) ||
      !message.contains(MESSAGE_SENSORTYPE_TAG) || 
      !message.contains(MESSAGE_VALUE_TAG)) {
		  
      printf("Json message received is incomplete\n");
      continue;
    }
    std::string player = message[MESSAGE_PLAYER_TAG];
    std::string bodypart = message[MESSAGE_BODYPART_TAG];
    std::string sensortype = message[MESSAGE_SENSORTYPE_TAG];    
    whc_connectionsMap[player+"_"+bodypart] = connection;

    whc_messagesMap[player+"_"+bodypart+"_"+sensortype] = message[MESSAGE_VALUE_TAG];    
    for( std::list<BodynodeListener*>::iterator it_listener = whc_bodynodesListeners.begin(); 
        it_listener != whc_bodynodesListeners.end(); it_listener ++) {

      if( (*it_listener)->isOfInterest(player, bodypart, sensortype) ){
	std::string value = message[MESSAGE_VALUE_TAG].dump();
        (*it_listener)->onMessageReceived(player, bodypart, sensortype, value);
      }
      
    }
    
    //std::cout << "whc_messagesMap = "<< whc_messagesMap[player+"_"+bodypart+"_"+sensortype] << '\n';
  }
}

