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
uint16_t port_sn = SERVER_PORT_AP_SN;
uint16_t port_n = SERVER_PORT_AP_N;
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
WiFiUDP mUdpConnectionSN;
WiFiUDP mUdpConnectionN;

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
  mUdpConnectionSN.begin(port_sn);
  mUdpConnectionN.begin(port_n);
  setStatusConnectionHMI_ON();
}

void sendACK(IPAddressPort connection){
  byte buf_udp [4] = {'A','C','K', '\0'};
  if(connection.port == port_sn){
    mUdpConnectionSN.beginPacket(connection.ip, port_sn);
    mUdpConnectionSN.write(buf_udp, 4);
    mUdpConnectionSN.endPacket(); 
  } else if(connection.port == port_n){
    mUdpConnectionN.beginPacket(connection.ip, port_n);
    mUdpConnectionN.write(buf_udp, 4);
    mUdpConnectionN.endPacket(); 
  }
}

IPAddressPort get_snodes_udp_packets(String &incomingMessage) {
  int noBytes = mUdpConnectionSN.parsePacket();
  String received_command = "";
  IPAddressPort connection;
  connection.port = 0;
  if ( noBytes > 0 ) {
     // read the packet into the buffer
    int len = mUdpConnectionSN.read(packetBuffer, MAX_BUFF_LENGTH);
    unsigned int i = 0;
    for(; i < len; ++i) {
      messagesBuffer[i] = packetBuffer[i];
    }
    messagesBuffer[i] = '\0';
    incomingMessage = messagesBuffer;
    connection.ip = mUdpConnectionSN.remoteIP();
    connection.port = mUdpConnectionSN.remotePort();
  }
  return connection;
}

IPAddressPort get_nodes_udp_packets(String &incomingMessage) {
  int noBytes = mUdpConnectionN.parsePacket();
  String received_command = "";
  IPAddressPort connection;
  connection.port = 0;
  if ( noBytes > 0 ) {
    // read the packet into the buffer
    int len = mUdpConnectionN.read(packetBuffer, MAX_BUFF_LENGTH);
    unsigned int i = 0;
    for(; i < len; ++i) {
      messagesBuffer[i] = packetBuffer[i];
    }
    messagesBuffer[i] = '\0';
    incomingMessage = messagesBuffer;
    connection.ip = mUdpConnectionN.remoteIP();
    connection.port = mUdpConnectionN.remotePort();
  }
  return connection;
}

void sendActionToNode(IPAddressPort connection, String actionMessage){
  int buf_size = actionMessage.length()+1;
  byte buf_udp [buf_size];

  actionMessage.getBytes(buf_udp, buf_size);
  if(connection.port == port_sn){
    mUdpConnectionSN.beginPacket(connection.ip, port_sn);
    mUdpConnectionSN.write(buf_udp, buf_size);
    mUdpConnectionSN.endPacket(); 
  } else if(connection.port == port_n){
    mUdpConnectionN.beginPacket(connection.ip, port_n);
    mUdpConnectionN.write(buf_udp, buf_size);
    mUdpConnectionN.endPacket(); 
  }
}

void sendActions(Connections &connections){
  for(unsigned int index = 0; index < connections.num_connections; ++index){
    if( connections.conn_status[index] == CS_WAIT_ACTION_ACK ){
      sendActionToNode(connections.conn[index], connections.last_action[index].message);
    }
  }
}
