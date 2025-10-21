This is a Host-based project to control a Robotic Arm ZYY with two Bodynodes.

The Host can also be a Raspberry PI

A Robotic Arm ZYY is a 3 Motors Robotic Arm:
- Motor 1 controls the Z rotation of Arm1, Arm2, Arm3
- Motor 2 controls the local Y rotation of Arm2, Arm3
- Motor 3 controls the local Y rotation of Arm3

Angle1 is therefore a global Z angle
Angle2 is a local Y angle
Angle3 is a local Y angle

Make use of the virtual3d_sensors to make sure your bodynodes sensors send data to a host
Make use of the virtual3d_robotic_arm_zyy to understand how fake sensor values affect your real robotic arm,
and change the configuration so it moves as expected

When the person moves his arm, the imaginary space point "." moves.
This is the point that the Robotic Arm will try to follow

There are limitations on the Robotic Arm. It cannot move everywhere.
The system will try to follow the point in the allowed space and also
try his best for points it cannotr reach

We have the project in the following languages:
- python3

In our program we are using Adeept.py to abstract the interaction with the Robotic Arm
Feel free to change the code and adapt it to your case.

