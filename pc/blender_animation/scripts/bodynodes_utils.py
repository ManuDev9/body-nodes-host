#
# MIT License
# 
# Copyright (c) 2021-2024 Manuel Bottini
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

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
