
import bpy
from mathutils import *

bodynodes_objs_init = {
	"forearm_left": Quaternion((0.5000, 0.5000, 0.5000, 0.5000)),
	"forearm_right": Quaternion((0.5000, 0.5000, -0.5000, -0.5000)),
	"head": Quaternion((1.0000, 0.0000, 0.0000, 0.0000)),
	"Hip": Quaternion((1.0000, 0.0000, 0.0000, 0.0000)),
	"lowerbody": Quaternion((1.0000, 0.0000, 0.0000, 0.0000)),
	"lowerleg_left": Quaternion((-0.0000, 1.0000, 0.0000, -0.0000)),
	"lowerleg_right": Quaternion((-0.0000, 1.0000, 0.0000, -0.0000)),
	"upperarm_left": Quaternion((0.5000, 0.5000, 0.5000, 0.5000)),
	"upperarm_right": Quaternion((0.5000, 0.5000, -0.5000, -0.5000)),
	"upperbody": Quaternion((1.0000, 0.0000, 0.0000, 0.0000)),
	"upperleg_left": Quaternion((-0.0000, 1.0000, 0.0000, -0.0000)),
	"upperleg_right": Quaternion((-0.0000, 1.0000, 0.0000, -0.0000))
}