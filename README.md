# body-nodes-host
BodyNodes repository for the host side

For now we have the following hosts:
- Blender
  - Let you create animations using Bodynodes sensors
  - It is a UI capable of working collecting movement data from sensor and help you modify it and apply it to the characters
  - Works with 11 body parts. Unfortunately on Windows the mobile hotspot has a maximum of 8 wifi connected devices at the same time, so you need multiples take sessions 
  - Introductions and animation examples video can be found at these links:
    - Blender UI Introduction - 1: https://www.youtube.com/watch?v=stgBOEd9ngc
	- Introduzione UI di Blender - 1: https://www.youtube.com/watch?v=vazKZa--szA
	- Blender animation #1: https://www.youtube.com/watch?v=MwjpmM8pkQM
	- Blender animation #2: https://www.youtube.com/watch?v=hXeTYtePf1c
  - Files in this repo:
    - FullSuitScript_11.blend : main project file containing the model and armature with our UI. Go in Scripting mode and run the script to make the UI appear
    - fullsuitscript_11.py : python script creating the UI.
    - Functionalities:
        - Select player
        - Start/Stop of the server
		- Start/Stop reconding session
		- Up to 3 different reconding sessions possible at the same time
		- Chaning animation for calibration issues
		- Apply walk character movement automatically (move in the XY-plane)
		- Enable/Disable tracking
		- Load/Save/Reset puppet position
        - Change axis of each bodypart
		- Close UI (stops animation and server)