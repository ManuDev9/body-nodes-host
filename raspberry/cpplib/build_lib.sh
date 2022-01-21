#!/bin/sh


# Convert library code to Object file
g++ -c -o bodynodes.o -g WifiHostCommunicator.cpp

# Create shared .SO library
gcc -shared -o libBodynodes.so bodynodes.o
