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
#include <iostream>
#include <unistd.h>

class BodynodeListenerTest : public BodynodeListener {
  public:
    void onMessageReceived(std::string player, std::string bodypart, std::string sensortype, std::string value) {
      std::cout << "onMessageReceived: player=" << player << " bodypart=" << bodypart << " sensortype=" << sensortype << " value=" << value << std::endl;
    }
    bool isOfInterest(std::string player, std::string bodypart, std::string sensortype) {
      return true;
    }
};


int main(){
  BnWifiHostCommunicator communicator;
  communicator.start({ "BN" });
  BodynodeListenerTest listener;
  
  char c_command = 'n';
  while(c_command != 'e') {
    std::cout << "Type a command [r/l/u ro read message, h/p/b/s/w to send action, e to exit]: " << std::endl; // Type a character and press enter
    std::cin >> c_command; // Get user input from the keyboard
    if(c_command == 'r') {
      std::string player = "mario";
      std::string bodypart = "katana";
      std::string sensortype = "orientation_abs";
      float outvalue[4] = {0, 0, 0, 0};
      communicator.getMessageValue(player, bodypart, sensortype, outvalue);
      std::cout << "outvalue = [ " << outvalue[0] << ", " << outvalue[1] << ", " << outvalue[2] << ", " << outvalue[3] << " ]"<< std::endl;
    } else if(c_command == 'l') {
      std::cout << "Adding the listener" << std::endl;
      communicator.addListener(&listener);
    } else if(c_command == 'u') {
      std::cout << "Remove the listener" << std::endl;
      communicator.removeListener(&listener);
    } else if (c_command == 'h') {
      nlohmann::json action;
      action[ACTION_TYPE_TAG] = ACTION_TYPE_HAPTIC_TAG;
      action[ACTION_PLAYER_TAG] = "mario";
      action[ACTION_BODYPART_TAG] = "katana";
      action[ACTION_HAPTIC_DURATION_MS_TAG] = 250;
      action[ACTION_HAPTIC_STRENGTH_TAG] = 200;
      
      communicator.addAction(action);
    } else if (c_command == 'p') {
      nlohmann::json action;
      action[ACTION_TYPE_TAG] = ACTION_TYPE_SETPLAYER_TAG;
      action[ACTION_PLAYER_TAG] = "mario";
      action[ACTION_BODYPART_TAG] = "katana";
      action[ACTION_SETPLAYER_NEWPLAYER_TAG] = "luigi";
      
      communicator.addAction(action);
    } else if (c_command == 'b') {
      nlohmann::json action;
      action[ACTION_TYPE_TAG] = ACTION_TYPE_SETBODYPART_TAG;
      action[ACTION_PLAYER_TAG] = "mario";
      action[ACTION_BODYPART_TAG] = "katana";
      action[ACTION_SETBODYPART_NEWBODYPART_TAG] = "upperarm_left";
      
      communicator.addAction(action);
    } else if (c_command == 's') {
      nlohmann::json action;
      action[ACTION_TYPE_TAG] = ACTION_TYPE_ENABLESENSOR_TAG;
      action[ACTION_PLAYER_TAG] = "mario";
      action[ACTION_BODYPART_TAG] = "katana";
      action[ACTION_ENABLESENSOR_SENSORTYPE_TAG] = MESSAGE_SENSORTYPE_ORIENTATION_ABS_TAG;
      action[ACTION_ENABLESENSOR_ENABLE_TAG] = false;
      
      communicator.addAction(action);
    } else if (c_command == 'w') {
      nlohmann::json action;
      action[ACTION_TYPE_TAG] = ACTION_TYPE_SETWIFI_TAG;
      action[ACTION_PLAYER_TAG] = "mario";
      action[ACTION_BODYPART_TAG] = "katana";
      
      action[ACTION_SETWIFI_SSID_TAG] = "upperbody";
      action[ACTION_SETWIFI_PASSWORD_TAG] = "bodynodes1";
      
      communicator.addAction(action);
    }
    communicator.sendAllActions();
  }
  communicator.stop();

}
