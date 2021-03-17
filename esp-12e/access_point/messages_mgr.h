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

#ifndef __ACCESS_POINT_MESSAGESMGR_H__
#define __ACCESS_POINT_MESSAGESMGR_H__

// Serial is always connected

void initMessages();
int get_index_bodypart(IPAddressPort connection, const char *bodypart);
void store_message(int index_bodypart, const char *mtype, const char *mvalue);
String getAllMessages();
void serial_send_messages();
void parseMessage(IPAddressPort connection, String message);
unsigned int manageAck(IPAddressPort connection);
void setActionToNodes(Action action);
Connections &getConnections();

#endif //__ACCESS_POINT_MESSAGESMGR_H__
