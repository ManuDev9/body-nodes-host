#!/bin/sh

# Create the executable by linking shared library
g++ -I/home/pi/workspace/body-nodes-host/raspberry/cpplib -L/home/pi/workspace/body-nodes-host/raspberry/cpplib -Wall -o osc_translator -g osc_translator.cpp -lBodynodes -lpthread -llo

# Make shared library available at runtime:
# export LD_LIBRARY_PATH=/home/pi/workspace/body-nodes-host/raspberry/cpplib:$LD_LIBRARY_PATH 
# LD_LIBRARY_PATH=/home/pi/workspace/body-nodes-host/raspberry/cpplib:$LD_LIBRARY_PATH ./osc_translator
