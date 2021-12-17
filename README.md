# body-nodes-host
BodyNodes repository for the host side

We have the following hosts:
- PC Blender:
  - It is a UI capable of working collecting movement data from wifi sensor and help you modify it and apply it to the characters
    - Let you create recordings using Bodynodes sensors and save them as animation data in files
    - Let you load from files or bake the animation data in the armature to use and modify
    - Let you extract your animation own data in files so that you can pass them easily
	- Let you load and save .fbx animations that can be used in other frameworks (Unity for example)
  - Blender Serial:
    - Works with 11 body parts. It has to be used with the esp-12e/access_point which connects serially with the PC and wifi with the snodes
  - Blender Wifi:
    - Works with 11 body parts. On Windows the mobile hotspot has a maximum of 8 wifi connected devices at the same time. In order to get data from all 11 nodes you need Wifi Super Nodes, which are wifi nodes that can collect info from other wifi nodes. Otherwise you need to take multiple sessions of the same movements with the different bodypart nodes

Introductions and animation examples video can be found at these links:
  - Blender UI Introduction - 1: https://www.youtube.com/watch?v=stgBOEd9ngc
  - Introduzione UI di Blender - 1: https://www.youtube.com/watch?v=vazKZa--szA
  - Blender animation #1: https://www.youtube.com/watch?v=MwjpmM8pkQM
  - Blender animation #2: https://www.youtube.com/watch?v=hXeTYtePf1c
Main files in each project:
  - .ino : Arduino project files containing the code to run the Host on the Arduino-compatible board
  - .blend : Blender project files containing the model and armature with our UI. Go in Scripting mode and run the script to make the UI appear
  - fullsuit11_recording.py : python script for the "Bodynodes recording" tab with all recording functionalities with Wifi SNodes
  - fullsuit11_recording_serial.py : python script for the "Bodynodes recording" tab with all recording functionalities with serial Access Point
  - fullsuit11_animation.py : python script for the "Bodynodes animation" tab with all animation functionalities
  - For more info about the functionalities watch this video: https://www.youtube.com/watch?v=LVsrDDIUEkY&t=5s
  - armature_config_XXX.json : bodynodes configuration files containing the bodypart-bones relations
  - example_animation.json : example of bodynodes animation data file
Cool functions we implemented to help using bodynodes animation data:
  - Walk algorithm: https://www.youtube.com/watch?v=99TttiHgcV4&t=11s
  - Steady feet algortihm: https://www.youtube.com/watch?v=o5ng-tRwjA0
Other videos:
  - How to wear the Bodynodes: https://www.youtube.com/watch?v=LUTw81M7dCs
  - One Shot Recordings with Wifi SNodes: https://www.youtube.com/watch?v=ZCPGYsXJy1M
  - First Animation on Blender: https://www.youtube.com/watch?v=JCAFX81Wjso
  - Unity Boxe Animations: https://www.youtube.com/watch?v=EFiGo6Ao5FU
  

