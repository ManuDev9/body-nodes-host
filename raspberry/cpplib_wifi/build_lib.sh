#!/bin/sh


# Convert library code to Object file
g++ -c -o BnWifiHostCommunicator.o -g BnWifiHostCommunicator.cpp

# Create shared .SO library
gcc -shared -o libBodynodes.so BnWifiHostCommunicator.o
