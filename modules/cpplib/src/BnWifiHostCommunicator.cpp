/**
 * MIT License
 *
 * Copyright (c) 2021-2025 Manuel Bottini
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

#include "BnWifiHostCommunicator.h"

#include <stdio.h>
#include <sys/time.h>
#include <iostream>
#include <unistd.h>
#include <sys/types.h> 
#include <chrono>


void startFunData(BnWifiHostCommunicator *comm) {
  comm->run_connection_background();
}

void startFunMulticast(BnWifiHostCommunicator *comm) {
  comm->run_multicast_background();
}

void BnWifiHostCommunicator::start(std::list<std::string> connectionParameters) {
  whc_toStop = false;
  if( connectionParameters.size() != 1 ) {
    // Only one identifier is taken
    printf("Please provide valid connection parameters, for example [ \"BN\" ]\n");
    return;
  }
  whc_identifier = connectionParameters.front();
  
  // create a UDP socket for data
  if ((whc_connector.socket_id =socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1) {
    printf("Couldn't data start socket\n");
    return;
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
  if( setsockopt(whc_connector.socket_id, SOL_SOCKET, SO_RCVTIMEO, &read_timeout, sizeof read_timeout) == -1 ) {
    printf("Couldn't set option to data socket\n");
    whc_toStop = true;
    return;
  }
  
  // bind data socket to port
  if( bind(whc_connector.socket_id , (sockaddr*)&whc_connector.ip_address, sizeof(whc_connector.ip_address) ) == -1) {
    printf("Couldn't bind data socket to port\n");
    whc_toStop = true;
    return;
  }

  // create a UDP socket for multicast
  if ((whc_multicast_connector.socket_id = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1) {
    printf("Couldn't start multicast socket\n");
    whc_toStop = true;
    return;
  }
  
  // zero out the structure
  memset((char *) &whc_multicast_connector.ip_address, 0, sizeof(whc_multicast_connector.ip_address));
  
  whc_multicast_connector.ip_address.sin_family = AF_INET;
  whc_multicast_connector.ip_address.sin_port = htons(BODYNODES_MULTICAST_PORT);
  whc_multicast_connector.ip_address.sin_addr.s_addr = htonl(INADDR_ANY);

  whc_multicast_connector.multicast_ip_address.sin_family = AF_INET;
  whc_multicast_connector.multicast_ip_address.sin_port = htons(BODYNODES_MULTICAST_PORT);
  whc_multicast_connector.multicast_ip_address.sin_addr.s_addr = inet_addr(BODYNODES_MULTICAST_ADDRESS);

  struct ip_mreq mc_req;
  mc_req.imr_multiaddr.s_addr = whc_multicast_connector.multicast_ip_address.sin_addr.s_addr;
  mc_req.imr_interface.s_addr = htonl(INADDR_ANY);

  // set multicast option to socket
  if( setsockopt(whc_multicast_connector.socket_id, IPPROTO_IP, IP_ADD_MEMBERSHIP, (char*)&mc_req, sizeof(mc_req)) == -1 ) {
    printf("Couldn't set option to multicast socket\n");
    whc_toStop = true;
    return;
  }
  
  // bind multicast socket to port
  if( bind(whc_multicast_connector.socket_id , (sockaddr*)&whc_multicast_connector.ip_address, sizeof(whc_multicast_connector.ip_address) ) == -1) {
    printf("Couldn't bind multicast socket to port\n");
    whc_toStop = true;
    return;
  }

  if(!whc_toStop) {
    whc_dataConnectionThread = std::thread(&startFunData, this);
    whc_multicastConnectionThread = std::thread(&startFunMulticast, this);
  }
}

void BnWifiHostCommunicator::stop() {
  whc_toStop = true;
  close(whc_connector.socket_id);
  close(whc_multicast_connector.socket_id);
  whc_dataConnectionThread.join();
  whc_multicastConnectionThread.join();
  removeAllListeners();
}

void BnWifiHostCommunicator::update() {
  printf("BnWifiHostCommunicator::update()\n");
}

bool BnWifiHostCommunicator::getMessageValue(
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

void BnWifiHostCommunicator::addAction(nlohmann::json &action) {
  whc_actionsToSend.push_back(action);
}

void BnWifiHostCommunicator::sendAllActions() {
  for (auto const& action : whc_actionsToSend) {
    std::cout << "action: " << action << '\n';
    std::string player_bodypart = action[BN_ACTION_PLAYER_TAG];
    player_bodypart.append("_");
    player_bodypart.append(action[BN_ACTION_BODYPART_TAG]);
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

bool BnWifiHostCommunicator::checkAllOk() {
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
      if(checkForACKN(*connectionData)) {
        sendACKH(*connectionData);
        connectionData->setConnected();
      }
    } else {
      if( time(0) - connectionData->last_rec_time > CONNECTION_KEEP_ALIVE_REC_INTERVAL_MS ) {
        connectionData->setDisconnected();
      }
      if(checkForACKN(*connectionData)) {
        sendACKH(*connectionData);
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

void BnWifiHostCommunicator::run_connection_background() {
  while(checkAllOk()) {
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
  }
}

void BnWifiHostCommunicator::run_multicast_background() {
  while(!whc_toStop) {
    //printf("Sending a multicast BN\n");
    sendMulticastBN();
    std::this_thread::sleep_for(std::chrono::milliseconds(5000));
  }
}

bool BnWifiHostCommunicator::addListener(BodynodeListener *listener) {
  if(listener!=nullptr) {
    whc_bodynodesListeners.push_back(listener);
    return true;
  }
  return false;
}

void BnWifiHostCommunicator::removeListener(BodynodeListener *listener) {
  if(listener!=nullptr) {
    whc_bodynodesListeners.remove(listener);
  }
}

void BnWifiHostCommunicator::removeAllListeners() {
  whc_bodynodesListeners.clear();
}

void BnWifiHostCommunicator::receiveBytes() {
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

void BnWifiHostCommunicator::sendACKH(IPConnectionData &connectionData) {
  char tmp_buf[5] = {'A', 'C', 'K', 'H', '\0'};
  int slen = sizeof(connectionData.ip_address);
  if (sendto(whc_connector.socket_id, tmp_buf, 5, 0, (struct sockaddr*) &connectionData.ip_address, slen) == -1) {
    printf("Couldn't send ACKH\n");
  }
}

void BnWifiHostCommunicator::sendMulticastBN() {
  uint8_t const length_id = whc_identifier.size()+1;
  char tmp_buf[length_id];
  std::strcpy(tmp_buf, whc_identifier.c_str());
  tmp_buf[length_id-1] = '\0';

  //printf("Sending BN Multicast: %s\n", tmp_buf);
  int slen = sizeof(whc_multicast_connector.multicast_ip_address);
  if (sendto(whc_connector.socket_id, tmp_buf, sizeof(tmp_buf), 0, (struct sockaddr*) &whc_multicast_connector.multicast_ip_address, slen) == -1) {
    printf("Couldn't send BN Multicast\n");
  }
}

bool BnWifiHostCommunicator::checkForACKN(IPConnectionData &connectionData) {
  for(uint16_t index = 0; index< connectionData.num_received_bytes-3;++index){
    if(connectionData.received_bytes[index] == 'A' && connectionData.received_bytes[index+1] == 'C' && connectionData.received_bytes[index+2] == 'K' && connectionData.received_bytes[index+3] == 'N') {
      connectionData.last_rec_time = time(0);
      return true;
    }
  }
  return false;
}

void BnWifiHostCommunicator::checkForMessages(IPConnectionData &connectionData) {
  if(connectionData.num_received_bytes > 0 ) {
    //std::cout << "checkForMessages - connetionData.received_bytes =" << connectionData.received_bytes << '\n';
    nlohmann::json jsonMessages = nlohmann::json::parse(connectionData.received_bytes);
    parseMessage(connectionData.ip_address, jsonMessages);
    connectionData.last_rec_time = time(0);
  }
}

void BnWifiHostCommunicator::parseMessage(sockaddr_in &connection, nlohmann::json &jsonMessages) {
  //printf("BnWifiHostCommunicator::parseMessage\n");
  for (auto& elem : jsonMessages.items()) {
    //std::cout << "key: " << message.key() << ", value:" << message.value() << '\n';
    nlohmann::json message = elem.value();
    //std::cout << "message: " << message << '\n';
    if(!message.contains(BN_MESSAGE_PLAYER_TAG) ||
      !message.contains(BN_MESSAGE_BODYPART_TAG) ||
      !message.contains(BN_MESSAGE_SENSORTYPE_TAG) || 
      !message.contains(BN_MESSAGE_VALUE_TAG)) {
		  
      printf("Json message received is incomplete\n");
      continue;
    }
    std::string player = message[BN_MESSAGE_PLAYER_TAG];
    std::string bodypart = message[BN_MESSAGE_BODYPART_TAG];
    std::string sensortype = message[BN_MESSAGE_SENSORTYPE_TAG];    
    whc_connectionsMap[player+"_"+bodypart] = connection;

    whc_messagesMap[player+"_"+bodypart+"_"+sensortype] = message[BN_MESSAGE_VALUE_TAG];    
    for( std::list<BodynodeListener*>::iterator it_listener = whc_bodynodesListeners.begin(); 
        it_listener != whc_bodynodesListeners.end(); it_listener ++) {

      if( (*it_listener)->isOfInterest(player, bodypart, sensortype) ){
	std::string value = message[BN_MESSAGE_VALUE_TAG].dump();
        (*it_listener)->onMessageReceived(player, bodypart, sensortype, value);
      }
      
    }
    
    //std::cout << "whc_messagesMap = "<< whc_messagesMap[player+"_"+bodypart+"_"+sensortype] << '\n';
  }
}

