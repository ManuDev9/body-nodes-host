/**
 * MIT License
 *
 * Copyright (c) 2021-2024 Manuel Bottini
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

#include "BnConstants.h"

#include <sys/socket.h>
#include <arpa/inet.h>	//inet_addr

#ifndef __BODYNODES_COMMONS_H
#define __BODYNODES_COMMONS_H

#define MAX_BUFFER_LENGTH             512	//Max length of buffer
#define BODYNODES_PORT                12345
#define BODYNODES_MULTICAST_PORT      12346
#define BODYNODES_MULTICAST_ADDRESS   "239.192.1.99"

#define CONNECTION_ACK_INTERVAL_MS 1000
#define CONNECTION_KEEP_ALIVE_SEND_INTERVAL_MS 30000
#define CONNECTION_KEEP_ALIVE_REC_INTERVAL_MS 60000


struct UDPConnector {
  sockaddr_in ip_address;
  sockaddr_in multicast_ip_address;
  int socket_id;
};

class IPConnectionData {
public:
  void setDisconnected() { conn_status = CONNECTION_STATUS_NOT_CONNECTED; }
  void setWaitingACK() { conn_status = CONNECTION_STATUS_WAITING_ACK; }
  void setConnected() { conn_status = CONNECTION_STATUS_CONNECTED; }
  bool isDisconnected() { return conn_status == CONNECTION_STATUS_NOT_CONNECTED; }
  bool isWaitingACK() { return conn_status == CONNECTION_STATUS_WAITING_ACK; }
  void cleanBytes() {
    memset(received_bytes, 0, MAX_BUFFER_LENGTH); 
    num_received_bytes = 0;
  }

  uint8_t conn_status = CONNECTION_STATUS_NOT_CONNECTED;
  sockaddr_in ip_address;
  
  char received_bytes[MAX_BUFFER_LENGTH];
  uint16_t num_received_bytes = 0;

  unsigned long last_sent_time = 0; // Not in use for Hosts
  unsigned long last_rec_time = 0;
};

#endif // __BODYNODES_COMMONS_H
