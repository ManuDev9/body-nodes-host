# body-nodes-host
BodyNodes repository for the host side

For now we have the following hosts:
- Blender - It is capable of working with all 11 bodynodes all active at the same time. Unfortunately on Windows the Mobile Hotspot has a maximum of 8 wifi connected devices at the same time. The Blender project contains the example of this video: https://www.youtube.com/watch?v=MwjpmM8pkQM . Contains:
  - FullSuitScript_11.blend : main project file containing the model and armature with our UI. Go in Scripting mode and run the script to make the UI appear
  - fullsuitscript_11.py : python script creating the UI, able to start/stop the server, and change axis of each bodypart