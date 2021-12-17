/**
MIT License

Copyright (c) 2021 Manuel Bottini

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

#include "BodynodesHostInterface.h"
#include "commons.h"

#include <thread>
#include <map>
#include <list>

#ifndef __WIFI_HOST_COMMUNICATOR
#define __WIFI_HOST_COMMUNICATOR

class WifiHostCommunicator : public BodynodesHostInterface {

public:
  void start();
  void stop();
  void update();
  bool getMessageVaue(std::string player, std::string bodypart, std::string sensortype, float outvalue[]);
  void addAction(nlohmann::json &action);
  void sendAllActions();
  bool checkAllOk();

private:

  void receiveBytes();
  void sendACK(IPConnectionData &connectionData);
  bool checkForACK(IPConnectionData &connectionData);
  void checkForMessages(IPConnectionData &connectionData);
  void parseJSON(sockaddr_in &connection, nlohmann::json &jsonMessages);
  
  std::thread                             whc_messagesListenerThread;
  bool                                    whc_toStop;
  nlohmann::json                          whc_messagesMap;
  std::map<std::string, sockaddr_in>      whc_connectionsMap;
  std::map<std::string, IPConnectionData> whc_tempConnectionsDataMap;
  UDPConnector                            whc_connector;
  std::list<nlohmann::json>               whc_actionsToSend;
};

#endif // __WIFI_HOST_COMMUNICATOR
