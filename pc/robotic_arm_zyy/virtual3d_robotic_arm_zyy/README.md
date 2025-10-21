This is a Host-based project to play in a virtual 3d environment with your robotic arm

The Host can also be a Raspberry PI

It recreates a virtual Robotic Arm ZYY scenerio that can control a real robotic arm.

We can use the sliders to change angles and understand the correct offset angles of your robotic arm.
You can then take inspiration for the real robotic arm project

Note, you need a real robotic arm serially connected to the laptop.

You have a set of sliders:
- The top ones let you move your point of view
- The bottom ones on the left will change the offset for each angle affecting the arm.
  Offsets are subtracted to the values and then applied in the plot.
- The bottom ones on the right will set the fake values of the sensors

The values of the fake sensors are sent directly to the real robotic arm, showing you where 0, 90, 180 are for each angle.
Change the offset values to move the virtual arm so that it matches the real one.
If the virtual arm is moving in the opposite direction compared to the real arm, please change the signs in the code.

You can take the offset values and sign, to create a model for the real_robotic_arm_zyy project.

In our program we are using Adeept.py to abstract the interaction with the Robotic Arm
Feel free to change the code and adapt it to your case.
