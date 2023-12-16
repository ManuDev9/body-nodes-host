
import bpy
import mathutils

bodynodes_objs_init = {
	"forearm_left": mathutils.Quaternion((0.5000, 0.5000, 0.5000, 0.5000)),
	"forearm_right": mathutils.Quaternion((0.5000, 0.5000, -0.5000, -0.5000)),
	"head": mathutils.Quaternion((1.0000, 0.0000, 0.0000, 0.0000)),
	"Hip": mathutils.Quaternion((1.0000, 0.0000, 0.0000, 0.0000)),
	"lowerbody": mathutils.Quaternion((1.0000, 0.0000, 0.0000, 0.0000)),
	"lowerleg_left": mathutils.Quaternion((-0.0000, 1.0000, 0.0000, -0.0000)),
	"lowerleg_right": mathutils.Quaternion((-0.0000, 1.0000, 0.0000, -0.0000)),
	"upperarm_left": mathutils.Quaternion((0.5000, 0.5000, 0.5000, 0.5000)),
	"upperarm_right": mathutils.Quaternion((0.5000, 0.5000, -0.5000, -0.5000)),
	"upperbody": mathutils.Quaternion((1.0000, 0.0000, 0.0000, 0.0000)),
	"upperleg_left": mathutils.Quaternion((-0.0000, 1.0000, 0.0000, -0.0000)),
	"upperleg_right": mathutils.Quaternion((-0.0000, 1.0000, 0.0000, -0.0000))
}

bodynode_bones_init = [
	"lowerarm_left",
	"lowerarm_right",
	"head",
	"Hip",
	"lowerbody",
	"lowerleg_left",
	"lowerleg_right",
	"upperarm_left",
	"upperarm_right",
	"upperbody",
	"upperleg_left",
	"upperleg_right",
	"hand_left",
	"hand_right"
]

bodynode_fingers_init = [ "mignolo", "anulare", "medio", "indice", "pollice" ]

def get_bone_global_rotation_quaternion(player_selected, bone):
	if bone not in bpy.data.objects[player_selected].pose.bones:
		print(bone+" bone has not been found")
		return None
	return (bpy.data.objects[player_selected].matrix_world @ bpy.data.objects[player_selected].pose.bones[bone].matrix).to_quaternion()


def get_bone_local_rotation_quaternion(player_selected, bone):
	if bone not in bpy.data.objects[player_selected].pose.bones:
		print(bone+" bone has not been found")
		return None

	bone_obj = bpy.data.objects[player_selected].pose.bones[bone]
	if bone_obj.parent:
		return ( bone_obj.parent.matrix.inverted() @ bone_obj.matrix ).to_quaternion()
	else :
		return ( bone_obj.matrix).to_quaternion()

def get_bodynodeobj_ori(bodypart):
	if bodypart+"_ori" not in bpy.data.objects:
		print(bodypart+" bodynodeobj orientation has not been found")
		return None
	return bpy.data.objects[bodypart+"_ori"]


def remove_bodynodes_from_player(player_selected):
	if player_selected not in bpy.data.objects:
		return
	for bodypart in bodynode_bones_init:
		if bodypart not in bpy.data.objects[player_selected].pose.bones:
			print(bodypart + " bone is not in armature")
			continue

		if "Copy Rotation" in bpy.data.objects[player_selected].pose.bones[bodypart].constraints:
			bpy.data.objects[player_selected].pose.bones[bodypart].constraints.remove(
				bpy.data.objects[player_selected].pose.bones[bodypart].constraints["Copy Rotation"]
			)
		if "hand_" in bodypart:
			for finger in bodynode_fingers_init:
				for index in range(1, 4):
					bone_finger = bodypart + "_" + finger + "_" + str(index)
					if bone_finger in bpy.data.objects[player_selected].pose.bones:
						if "Copy Rotation" in bpy.data.objects[player_selected].pose.bones[bone_finger].constraints:
							bpy.data.objects[player_selected].pose.bones[bone_finger].constraints.remove(
								bpy.data.objects[player_selected].pose.bones[bone_finger].constraints["Copy Rotation"]
							)

def apply_bodynodes_to_player(player_selected, bodynodes_armature_config ):
	if player_selected not in bpy.data.objects:
		return
	for bodypart in bodynodes_armature_config.keys():
		if bodynodes_armature_config[bodypart]["bone_name"] == "":
			continue

		# We don't need to set the global rotation of the bodynodeobj_glove. Glove angle data is relative
		if "hand_" in bodypart:
			for finger in bodynode_fingers_init:
				bodynodeobj_glove_finger = get_bodynodeobj_glove(bodypart, finger)
				for index in range(1, 4):
					bone_finger = bodypart + "_" + finger + "_" + str(index)
					if bone_finger in bpy.data.objects[player_selected].pose.bones:
						if "Copy Rotation" not in bpy.data.objects[player_selected].pose.bones[bone_finger].constraints:
							bpy.data.objects[player_selected].pose.bones[bone_finger].constraints.new(type = 'COPY_ROTATION')
							bpy.data.objects[player_selected].pose.bones[bone_finger].constraints["Copy Rotation"].target = bodynodeobj_glove_finger
							bpy.data.objects[player_selected].pose.bones[bone_finger].constraints["Copy Rotation"].owner_space = 'LOCAL'
							bpy.data.objects[player_selected].pose.bones[bone_finger].constraints["Copy Rotation"].use_y = True
							bpy.data.objects[player_selected].pose.bones[bone_finger].constraints["Copy Rotation"].use_y = False
							bpy.data.objects[player_selected].pose.bones[bone_finger].constraints["Copy Rotation"].use_z = False

		bodynodeobj_ori = get_bodynodeobj_ori(bodypart)
		if bodynodeobj_ori == None:
			print(bodypart + " bodynodeobj_ori does not exist")
			continue

		if bodypart not in bpy.data.objects[player_selected].pose.bones:
			print(bodypart + " bone is not in armature")
			continue

		bodynodeobj_ori.rotation_quaternion = get_bone_global_rotation_quaternion(player_selected, bodypart)
		if "Copy Rotation" not in bpy.data.objects[player_selected].pose.bones[bodypart].constraints:
			bpy.data.objects[player_selected].pose.bones[bodypart].constraints.new(type = 'COPY_ROTATION')
			bpy.data.objects[player_selected].pose.bones[bodypart].constraints["Copy Rotation"].target = bodynodeobj_ori


