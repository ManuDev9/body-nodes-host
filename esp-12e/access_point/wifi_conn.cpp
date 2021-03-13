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

#include "wifi_conn.h"

extern "C" {
  #include "user_interface.h"
}
char ssid[] = WIFI_SSID;
char password[] = WIFI_PASS;
uint16_t port = SERVER_PORT_AP;     // port number of the server
byte packetBuffer[MAX_BUFF_LENGTH]; 
char messagesBuffer[MAX_BUFF_LENGTH]; 

/*
 * Example of messages coming from nodes:
 * [
 *  {
 *    "bodypart": "head",
 *    "type": "orientation",
 *    "value": "<w_value>|<x_value>|<y_value>|<z_value>"
 *  }
 * ]
 * 
 * It is an array of object
 * Every object should be read separately and analyzed
 */

StatusConnLED mStatusConnLED;
WiFiUDP mUdpConnection;

void setStatusConnectionHMI_ON(){
  digitalWrite(STATUS_WIFI_CONNECTION_HMI_LED_P, HIGH);
  mStatusConnLED.on = true;
  mStatusConnLED.lastToggle = millis();
}

void setStatusConnectionHMI_OFF(){
  digitalWrite(STATUS_WIFI_CONNECTION_HMI_LED_P, LOW);
  mStatusConnLED.on = false;
  mStatusConnLED.lastToggle = millis();
}

void setStatusConnectionHMI_BLINK(){
  if(millis() - mStatusConnLED.lastToggle > 300){
    mStatusConnLED.lastToggle = millis();
    mStatusConnLED.on = !mStatusConnLED.on;
    if(mStatusConnLED.on){
      digitalWrite(STATUS_WIFI_CONNECTION_HMI_LED_P, HIGH);
    } else {
      digitalWrite(STATUS_WIFI_CONNECTION_HMI_LED_P, LOW);
    }
  }
}

void initServer(){
  pinMode(STATUS_WIFI_CONNECTION_HMI_LED_P  , OUTPUT);
  setStatusConnectionHMI_OFF();
  WiFi.mode(WIFI_AP);
  WiFi.softAP(ssid, password);
  mUdpConnection.begin(port);
  setStatusConnectionHMI_ON();
}

void sendACK(IPAddress remote_ip, uint16_t remote_port){
  byte buf_udp [4] = {'A','C','K', '\0'};
  mUdpConnection.beginPacket(remote_ip, remote_port);
  mUdpConnection.write(buf_udp, 4);
  mUdpConnection.endPacket();
}

Connection get_nodes_udp_packets(JsonArray &jsonArray) {
  int noBytes = mUdpConnection.parsePacket();
  String received_command = "";
  Connection connection;
  if ( noBytes > 0 ) {
    int len = mUdpConnection.read(packetBuffer, MAX_BUFF_LENGTH); // read the packet into the buffer
    unsigned int i = 0;
    for(; i < len; ++i) {
      messagesBuffer[i] = packetBuffer[i];
    }
    messagesBuffer[i] = '\0';
    if(strstr(messagesBuffer, "ACK")  != NULL){
      sendACK(mUdpConnection.remoteIP(), mUdpConnection.remotePort());
    } else {
      DynamicJsonDocument messagesJson(JSON_ARRAY_SIZE(3) + MAX_BUFF_LENGTH);
  
      // Deserialize the JSON document
      DeserializationError error = deserializeJson(messagesJson, messagesBuffer);
      // Test if parsing succeeds.
      if (error) {
        return connection;
      }
      jsonArray = messagesJson.as<JsonArray>();
      connection.remote_ip = mUdpConnection.remoteIP();
      connection.remote_port = mUdpConnection.remotePort();
    }
  }
  return connection;
}

void sendActionToNode(Connection connection, String actionMessage){
  int buf_size = actionMessage.length()+1;
  byte buf_udp [buf_size];

  actionMessage.getBytes(buf_udp, buf_size);
  mUdpConnection.beginPacket(connection.remote_ip, connection.remote_port);
  mUdpConnection.write(buf_udp, buf_size);
  mUdpConnection.endPacket(); 
}

void sendActionToAllNodes(Connections connections, String actionMessage){
  for(unsigned int index = 0; index < connections.num_connections; ++index){
    sendActionToNode(connections.bodypart[index], actionMessage);
  }
}
