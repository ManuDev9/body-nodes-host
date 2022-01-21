
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

#include <iostream>
#include <sstream>
#include <unistd.h>
#include <algorithm>

#include <lo/lo.h>
#include <lo/lo_lowlevel.h>

class OscTranslator : public BodynodeListener {
  public:
    OscTranslator() {
      ot_addr = lo_address_new_from_url ("osc://192.168.0.167:8000");
      lo_address_set_ttl(ot_addr, 1);
    }

    void onMessageReceived(std::string player, std::string bodypart, std::string sensortype, std::string value) {
      // std::cout << "onMessageReceived: player=" << player << " bodypart=" << bodypart << " sensortype=" << sensortype << " value=" << value << std::endl;
      if( sensortype.compare(MESSAGE_SENSORTYPE_ORIENTATION_ABS_TAG) == 0) {
        lo_message msg = lo_message_new();

        lo_message_add_string(msg, player.c_str());
        lo_message_add_string(msg, bodypart.c_str());
        lo_message_add_string(msg, sensortype.c_str());
        
        std::vector<float> values_f = parse_vector(value);
        lo_message_add_float(msg, values_f[0]);
        lo_message_add_float(msg, values_f[1]);
        lo_message_add_float(msg, values_f[2]);
        lo_message_add_float(msg, values_f[3]);
        lo_send_message(ot_addr, ot_oa_path, msg);
        lo_message_free(msg);
      } else if( sensortype.compare(MESSAGE_SENSORTYPE_ACCELERATION_REL_TAG) == 0 ) {
        lo_message msg = lo_message_new();

        lo_message_add_string(msg, player.c_str());
        lo_message_add_string(msg, bodypart.c_str());
        lo_message_add_string(msg, sensortype.c_str());

        std::vector<float> values_f = parse_vector(value);
        lo_message_add_float(msg, values_f[0]);
        lo_message_add_float(msg, values_f[1]);
        lo_message_add_float(msg, values_f[2]);
        lo_send_message(ot_addr, ot_ar_path, msg);
        lo_message_free(msg);
      }
    }

    bool isOfInterest(std::string player, std::string bodypart, std::string sensortype) {
      return true;
    }

  private:

    std::vector<float> parse_vector(std::string value_str){
      std::vector<float> values_f;
      value_str[0] = ' ';
      value_str[value_str.size()-1] = ' ';
      std::stringstream value_stream (value_str);
      uint8_t count = 0;
      for(std::string single_val_str; std::getline(value_stream, single_val_str, ','); ) {
        float single_val_f = std::stof(single_val_str);
        values_f.push_back(single_val_f);
        count++;
      }
      return values_f;
    }

    lo_address ot_addr = nullptr;
    const char *ot_oa_path = "/obBn";
    const char *ot_ar_path = "/obBn";
};

int main(){
  WifiHostCommunicator communicator;
  communicator.start();
  OscTranslator translator;
  communicator.addListener(&translator);
  
  char c_command = 'n';
  while(c_command != 'e') {
    std::cout << "[Type e to exit the program]: " << std::endl; // Type a character and press enter
    std::cin >> c_command; // Get user input from the keyboard
  }
  communicator.stop();

}
