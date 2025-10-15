This is a Host-based project to play in a virtual 3d environment with two bodynodes.

The Host can also be a Raspberry PI

"bnvirtual3d_robotic_arm_zyy"
It recreates a virtual Robotic Arm ZYY scenerio that we want to control with two bodynodes.

A Robotic Arm ZYY is a 3 Motors Robotic Arm:
- Motor 1 controls the Z rotation of Arm1, Arm2, Arm3
- Motor 2 controls the local Y rotation of Arm2, Arm3
- Motor 3 controls the local Y rotation of Arm3

Angle1 is therefore a global Z angle
Angle2 is a local Y angle
Angle3 is a local Y angle

At Angle1, Angle2, Angle3 all to 0, the Arms are all pointing upwards.

     .
     |
     |
     |
     _

Example2:
Angle1 = 0
Angle2 = 90
Angle3 = 0

      _ _.
     |
     _

Example3
Angle1 = 0
Angle2 = 90
Angle3 = 90

      _ 
     | |
     _ .


The two Bodynodes instead are inserted on the person arm, the initial position is the L position

So the arm will be like this


    |
    |___.

When the person moves his arm, the imaginary space point "." moves.
This is the point that the Robotic Arm will try to follow

There are limitations on the Robotic Arm. It cannot move everywhere.
The system will try to follow the point in the allowed space and also
try his best for points it cannotr reach

We have the project in the following languages:
- python

The required packages are indicated in requirements.txt
$ pip install -r requirements.txt 

To run the scripts:
$ python3 bnvirtual3d_robotic_arm_zyy.py


