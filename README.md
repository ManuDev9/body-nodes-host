# body-nodes-host
BodyNodes repository for the host side

For now we have the following hosts:
- Blender Wifi
  - It is a UI capable of working collecting movement data from sensor and help you modify it and apply it to the characters
    - Let you create recordings using Bodynodes sensors and save them as animation data in files
    - Let you load from files or bake the animation data in the armature to use and modify
    - Let you extract your animation own data in files so that you can pass them easily 
  - Works with 11 body parts. Unfortunately on Windows the mobile hotspot has a maximum of 8 wifi connected devices at the same time, so you need multiples take sessions 
  - Introductions and animation examples video can be found at these links:
    - Blender UI Introduction - 1: https://www.youtube.com/watch?v=stgBOEd9ngc
    - Introduzione UI di Blender - 1: https://www.youtube.com/watch?v=vazKZa--szA
    - Blender animation #1: https://www.youtube.com/watch?v=MwjpmM8pkQM
    - Blender animation #2: https://www.youtube.com/watch?v=hXeTYtePf1c
  - Files in this repo:
    - FullSuitScript_11.blend : main project file containing the model and armature with our UI. Go in Scripting mode and run the script to make the UI appear
    - fullsuit11_recording.py : python script for the "Bodynodes recording" tab with all recording functionalities
    - fullsuit11_animation.py : python script for the "Bodynodes animation" tab with all animation functionalities
    - For more info about the functionalities watch this video: https://www.youtube.com/watch?v=LVsrDDIUEkY&t=5s
    - armature_config_XXX.json : bodynodes configuration files containing the bodypart-bones relations
    - example_animation.json : example of bodynodes animation data file
  - Cool functions we implemented to help using bodynodes animation data:
    - Walk algorithm: https://www.youtube.com/watch?v=99TttiHgcV4&t=11s
    - Steady feet algortihm: https://www.youtube.com/watch?v=o5ng-tRwjA0
