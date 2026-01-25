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

#include "BodynodesHostInterface.h"
#include "BnDatatypes.h"
#include <thread>
#include <map>
#include <list>


#ifndef __BN_WIFI_HOST_COMMUNICATOR
#define __BN_WIFI_HOST_COMMUNICATOR

class BnWifiHostCommunicator : public BodynodesHostInterface {

public:
  void start(std::list<std::string> connectionParameters);
  void stop();
  void update();
  bool getMessageValue(std::string player, std::string bodypart, std::string sensortype, float outvalue[]);
  void addAction(nlohmann::json &action);
  void sendAllActions();
  bool checkAllOk();
  void run_connection_background();
  void run_multicast_background();
  bool addListener(BodynodeListener *listener);
  void removeListener(BodynodeListener *listener);
  void removeAllListeners();

private:

  void receiveBytes();
  void sendACKH(IPConnectionData &connectionData);
  void sendMulticastBN();
  bool checkForACKN(IPConnectionData &connectionData);
  void checkForMessages(IPConnectionData &connectionData);
  void parseMessage(sockaddr_in &connection, nlohmann::json &jsonMessages);
  
  std::thread                             whc_dataConnectionThread;
  std::thread                             whc_multicastConnectionThread;
  bool                                    whc_toStop;
  nlohmann::json                          whc_messagesMap;
  std::map<std::string, sockaddr_in>      whc_connectionsMap;
  std::map<std::string, IPConnectionData> whc_tempConnectionsDataMap;
  UDPConnector                            whc_connector;
  UDPConnector                            whc_multicast_connector;
  std::list<nlohmann::json>               whc_actionsToSend;
  std::list<BodynodeListener*>            whc_bodynodesListeners;
  std::string                             whc_identifier;
};

#endif // __BN_WIFI_HOST_COMMUNICATOR
