# MIT License
# 
# Copyright (c) 2019-2020 Manuel Bottini
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

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from socket import *
import os
import threading
import json
import bpy
from mathutils import *
import time
import queue
from bpy_extras.io_utils import ExportHelper, ImportHelper

# This script is made for the FullSuit-11 and it is required to use and customize bodynodes animations

players_available = (('None', 'None', ''), ('BlueGuy', 'BlueGuy', ''), ('RedGuy', 'RedGuy', ''))
player_selected_anim = "None"

bodynodes_armature_config_anim = {}
bodynodes_saved_armature_change_anim = {}

bodynodes_panel_anim = {
	"editor" : {
		"created": False,
		"is_hidden": False,
	},
	"change" : {
		"started" : False
	}
}

def load_armature_config_anim(filepath):
	global bodynodes_armature_config_anim
	with open(filepath) as file:
		bodynodes_armature_config_anim = json.load(file)


def bake_animation():
	global player_selected_anim
	bpy.data.objects[player_selected_anim].select_set(True)
	bpy.ops.object.mode_set(mode='POSE')
	for b in bpy.data.objects[player_selected_anim].pose.bones:
		b.bone.select=True

	start = bpy.context.scene.frame_start
	end = bpy.context.scene.frame_end		
	bpy.ops.nla.bake(frame_start=start, frame_end=end, step=1, only_selected=True, visual_keying=True, clear_constraints=True, use_current_action=True, bake_types={'POSE'})

	for b in bpy.data.objects[player_selected_anim].pose.bones:
		b.bone.select=False

	for bodypart in bodynodes_armature_config_anim.keys():
		if bodynodes_armature_config_anim[bodypart]["bone_name"] == "":
			continue
		bpy.data.objects[bodypart].animation_data_clear()

	bpy.data.objects[player_selected_anim].pose.bones["Hip"].constraints.new(type = 'COPY_LOCATION')
	bpy.data.objects[player_selected_anim].pose.bones["Hip"].constraints["Copy Location"].target = bpy.data.objects[player_selected_anim+"_mover"]

def extract_animation(filepath):
	start = bpy.context.scene.frame_start
	end = bpy.context.scene.frame_end
	animation_json = {}
	for bodypart in bodynodes_armature_config_anim.keys():
		if bodynodes_armature_config_anim[bodypart]["bone_name"] == "":
			continue
		animation_json[bodypart] = []

	for bodypart in animation_json.keys():
		for frame in range(start, end+1):
			bpy.context.scene.frame_set(frame)
			obj_quat = Quaternion(get_bone_global_rotation_quaternion(bodynodes_armature_config_anim[bodypart]["bone_name"]))
			keyframe_info = {
				"rotation_quaternion" : [ obj_quat.w, obj_quat.x, obj_quat.y, obj_quat.z ],
				"frame_current" : frame - start
			}
			animation_json[bodypart].append(keyframe_info)

	with open(filepath, "w") as file:
		file.write(json.dumps(animation_json, indent=4, sort_keys=True))

def load_animation(filepath):
	global player_selected_anim
	
	# Load animation on bodynodes objects
	with open(filepath) as file:
		animation_json = json.load(file)

	start = bpy.context.scene.frame_start
	for bodypart in animation_json.keys():
		for keyframe_info in animation_json[bodypart]:
			player_bodypart = get_bodynodeobj(bodypart)
			set_bodynode_rotation_quaternion(bodypart, Quaternion((keyframe_info["rotation_quaternion"])))
			player_bodypart.keyframe_insert(data_path='rotation_quaternion', frame=(keyframe_info["frame_current"]+start))
			
	# Apply bodynodes objects constraints to bones
	for bodypart in animation_json.keys():
		if "Copy Rotation" not in bpy.data.objects[player_selected_anim].pose.bones[bodypart].constraints:
			bpy.data.objects[player_selected_anim].pose.bones[bodypart].constraints.new(type = 'COPY_ROTATION')
			bpy.data.objects[player_selected_anim].pose.bones[bodypart].constraints["Copy Rotation"].target = bpy.data.objects[bodypart]
	
	# Bake
	bake_animation()

def create_animation_editor():
	bodynodes_panel_anim["editor"]["created"] = True
	global player_selected_anim
	start = bpy.context.scene.frame_start
	end = bpy.context.scene.frame_end
	for frame in range(start, end+1):
		bpy.context.scene.frame_set(frame)
		copy_player = bpy.data.objects[player_selected_anim].copy()
		copy_player.data = bpy.data.objects[player_selected_anim].data.copy()
		copy_player.animation_data_clear()
		copy_player.name = player_selected_anim+"_"+str(frame)
		bpy.data.collections["Animation"].objects.link(copy_player)

	for frame in range(start, end+1):
		copy_player = bpy.data.objects[player_selected_anim+"_"+str(frame)]
		child_obj = bpy.data.objects[player_selected_anim].children[0].copy()
		child_obj.parent = copy_player
		child_obj.name = bpy.data.objects[player_selected_anim].children[0].name + "_" + str(frame)
		child_obj.modifiers['Armature'].object = copy_player
		bpy.data.collections["Animation"].objects.link(child_obj)
		bpy.data.armatures[bpy.data.objects[player_selected_anim+"_"+str(frame)].data.name].name = bpy.data.objects[player_selected_anim].data.name +"_"+str(frame)

def save_animation_editor():
	start = bpy.context.scene.frame_start
	end = bpy.context.scene.frame_end
	print("hey")

	for frame in range(start, end+1):
		bpy.context.scene.frame_set(frame)
		for bodypart in bodynodes_armature_config_anim.keys():
			if bodynodes_armature_config_anim[bodypart]["bone_name"] == "":
				continue
			player_bodypart = get_bodypart_bone(player_selected_anim, bodypart)
			bpy.data.objects[player_selected_anim].pose.bones[bodypart].matrix = bpy.data.objects[player_selected_anim+"_"+str(frame)].pose.bones[bodypart].matrix
			player_bodypart.keyframe_insert(data_path='rotation_quaternion', frame=(frame))

	bpy.context.scene.frame_set(start)

def showhide_animation_editor():
	start = bpy.context.scene.frame_start
	end = bpy.context.scene.frame_end
	global player_selected_anim
	body_name = bpy.data.objects[player_selected_anim].children[0].name
	for frame in range(start, end+1):
		bpy.data.objects[body_name+"_"+str(frame)].hide_set(not bodynodes_panel_anim["editor"]["is_hidden"])

	bodynodes_panel_anim["editor"]["is_hidden"] = not bodynodes_panel_anim["editor"]["is_hidden"]

def destroy_animation_editor():
	bodynodes_panel_anim["editor"]["created"] = False
	global player_selected_anim
	start = bpy.context.scene.frame_start
	end = bpy.context.scene.frame_end
	for frame in range(start, end+1):
		player_basename = bpy.data.objects[player_selected_anim].name
		mesh_basename = bpy.data.objects[player_selected_anim].children[0].name
		arma_basename = bpy.data.objects[player_selected_anim].data.name
		if player_basename+"_"+str(frame) in bpy.data.objects:
			bpy.data.objects.remove(bpy.data.objects[player_basename+"_"+str(frame)], do_unlink=True)
		if mesh_basename+"_"+str(frame) in bpy.data.objects:
			bpy.data.objects.remove(bpy.data.objects[mesh_basename+"_"+str(frame)], do_unlink=True)
		if arma_basename+"_"+str(frame) in bpy.data.armatures:
			bpy.data.armatures.remove(bpy.data.armatures[arma_basename+"_"+str(frame)], do_unlink=True)

def start_change_animation():
	global player_selected_anim
	global bodynodes_saved_armature_change_anim
	bodynodes_panel_anim["change"]["started"] = True
	bodynodes_puppet_saved_rot = {}
	for bodypart in bodynodes_armature_config_anim.keys():
		if bodynodes_armature_config_anim[bodypart]["bone_name"] == "":
			continue
		obj_quat = get_bodypart_bone(player_selected_anim, bodypart).rotation_quaternion
		bodynodes_saved_armature_change_anim[bodypart] = Quaternion((obj_quat))

	obj_quat = get_bodypart_bone(player_selected_anim, "Hip").rotation_quaternion
	bodynodes_saved_armature_change_anim["Hip"] = Quaternion((obj_quat))

def done_change_animation():
	global player_selected_anim
	global bodynodes_saved_armature_change_anim
	bodynodes_panel_anim["change"]["started"] = False
	puppet_diff_anim = {}
	for bodypart in bodynodes_saved_armature_change_anim.keys():
		print(bodypart)
		obj_quat = get_bodypart_bone(player_selected_anim, bodypart).rotation_quaternion
		if bodynodes_saved_armature_change_anim[bodypart] != obj_quat:
			puppet_diff_anim[bodypart] = obj_quat @ bodynodes_saved_armature_change_anim[bodypart].inverted()

	start = bpy.context.scene.frame_start
	end = bpy.context.scene.frame_end

	for frame in range(start, end+1):
		bpy.context.scene.frame_set(frame)
		for bodypart in puppet_diff_anim.keys():
			player_bodypart = get_bodypart_bone(player_selected_anim, bodypart)
			player_bodypart.rotation_quaternion = puppet_diff_anim[bodypart] @ player_bodypart.rotation_quaternion
			if player_bodypart.keyframe_delete(data_path='rotation_quaternion', frame=(frame)):
				player_bodypart.keyframe_insert(data_path='rotation_quaternion', frame=(frame))

	bpy.context.scene.frame_set(start)

def change_animation_player_fun(self, context):
	global player_selected_anim
	player_selected_anim = self.players_list_animation

# Example to move the mover where the Hip of the player is
# bpy.data.objects["RedGuy_mover"].location = bpy.data.objects["RedGuy"].matrix_world @ bpy.data.objects["RedGuy"].pose.bones["Hip"].matrix @ bpy.data.objects["RedGuy"].pose.bones["Hip"].location

def redirect_bodypart_anim(bodypart):
	# print("redirect_bodypart_anim")
	global bodynodes_armature_config_anim
	if bodypart in bodynodes_armature_config_anim.keys() and bodynodes_armature_config_anim[bodypart]["bone_name"] != "":
		return bodynodes_armature_config_anim[bodypart]["bone_name"]
	return bodypart

def get_bodypart_bone(player_selected_anim, bodypart):
	bone_name = redirect_bodypart_anim(bodypart)
	if bodypart not in bpy.data.objects[player_selected_anim].pose.bones:
		print(bodypart+" bone has not been found")
		return None

	return bpy.data.objects[player_selected_anim].pose.bones[bone_name]

def get_bodynodeobj(bodypart):
	if bodypart not in bpy.data.objects:
		print(bodypart+" bodynodeobj has not been found")
		return None
	return bpy.data.objects[bodypart]

def get_bone_global_rotation_quaternion(bone):
	global player_selected_anim
	if bone not in bpy.data.objects[player_selected_anim].pose.bones:
		print(bodypart+" bone has not been found")
		return None
	return (bpy.data.objects[player_selected_anim].matrix_world @ bpy.data.objects[player_selected_anim].pose.bones[bone].matrix).to_quaternion()

def get_bone_global_location(bone):
	global player_selected_anim
	if bone not in bpy.data.objects[player_selected_anim].pose.bones:
		print(bodypart+" bone has not been found")
		return None
	
	return bpy.data.objects[player_selected_anim].matrix_world @ bpy.data.objects[player_selected_anim].pose.bones[bone].matrix @ bpy.data.objects[player_selected_anim].pose.bones[bone].location
	
# def set_bodynode_rotation_quaternion(player, bodypart, rotation_quaternion):
	# bone = get_bodypart_bone(player_selected_anim, bodypart)
	# loc, rot, sca = bone.matrix.decompose()
	# mat_loc = Matrix.Translation(loc)
	# mat_sca = Matrix()
	# mat_sca[0][0] = 1
	# mat_sca[1][1] = 1
	# mat_sca[2][2] = 1
	# mat_rot = (bpy.data.objects[player].matrix_world.inverted().to_quaternion() @ rotation_quaternion).to_matrix().to_4x4()
	# bone.matrix = mat_loc @ mat_rot @ mat_sca

def get_bodynode_rotation_quaternion(bodypart):
	if bodypart not in bpy.data.objects:
		print(bodypart+" hasn't been found")
		return None
		
	return bpy.data.objects[bodypart].rotation_quaternion

def set_bodynode_rotation_quaternion(bodypart, rotation_quaternion):
	if bodypart not in bpy.data.objects:
		print(bodypart+" hasn't been found")
		return
		
	bpy.data.objects[bodypart].rotation_quaternion = rotation_quaternion

def apply_ref_walk(full_3d = False):
	global player_selected_anim
	print("player_selected_anim = "+player_selected_anim)
	start = bpy.context.scene.frame_start
	end = bpy.context.scene.frame_end
	player_mover = bpy.data.objects[player_selected_anim+"_mover"]
	
	bpy.context.scene.frame_set(start-1)
	ref_foot = bpy.data.objects[player_selected_anim].data.bones.active.name
	ref_foot_prev_glocation = get_bone_global_location(ref_foot)

	for frame in range(start, end+1):
		bpy.context.scene.frame_set(frame)
		diff_glocation = get_bone_global_location(ref_foot) - ref_foot_prev_glocation
		player_mover.location[0] -= diff_glocation[0]
		player_mover.location[1] -= diff_glocation[1]
		if full_3d:
			player_mover.location[2] -= diff_glocation[2]
		player_mover.keyframe_insert(data_path='location', frame=(frame))

def apply_auto_walk():
	global player_selected_anim
	print("player_selected_anim = "+player_selected_anim)
	start = bpy.context.scene.frame_start
	end = bpy.context.scene.frame_end
	player_mover = bpy.data.objects[player_selected_anim+"_mover"]

	ref_foot = None
	other_foot = None
	ref_foot_prev_glocation = None
	walking_vector = None

	for frame in range(start, end+1):
		if ref_foot == None:
			# The first reference foot will be found by looking at which foot is moving faster
			# the other foot will be used as reference
			bpy.context.scene.frame_set(frame-1)
			lfoot_glocation_prev = get_bone_global_location("Toe_L")
			rfoot_glocation_prev = get_bone_global_location("Toe_R")
			bpy.context.scene.frame_set(frame)

			lfoot_diff_glocation = get_bone_global_location("Toe_L") - lfoot_glocation_prev
			rfoot_diff_glocation = get_bone_global_location("Toe_R") - rfoot_glocation_prev
			
			lfoot_movement_vec = Vector((lfoot_diff_glocation[0], lfoot_diff_glocation[1]))
			rfoot_movement_vec = Vector((rfoot_diff_glocation[0], rfoot_diff_glocation[1]))
			lfoot_mov = lfoot_movement_vec @ lfoot_movement_vec
			rfoot_mov = rfoot_movement_vec @ rfoot_movement_vec
			
			if lfoot_mov > 0.001 or rfoot_mov > 0.001:
				if lfoot_mov > rfoot_mov:
					ref_foot = "Toe_R"
					other_foot = "Toe_L"
					ref_foot_prev_glocation = rfoot_glocation_prev
					other_foot_prev_glocation = lfoot_glocation_prev
				else:
					ref_foot = "Toe_L"
					other_foot = "Toe_R"
					ref_foot_prev_glocation = lfoot_glocation_prev
					other_foot_prev_glocation = rfoot_glocation_prev

				other_diff_glocation = get_bone_global_location(other_foot) - other_foot_prev_glocation
				walking_vector = Vector((other_diff_glocation[0], other_diff_glocation[1], 0))
				#print("First ref_foot = "+ref_foot)
				
			else:
				continue
				
		bpy.context.scene.frame_set(frame-1)
		ref_foot_prev_glocation = get_bone_global_location(ref_foot)
		bpy.context.scene.frame_set(frame)
		diff_glocation = get_bone_global_location( ref_foot) - ref_foot_prev_glocation
		player_mover.location[0] -= diff_glocation[0]
		player_mover.location[1] -= diff_glocation[1]
		player_mover.keyframe_insert(data_path='location', frame=(frame))

		bpy.context.scene.frame_set(frame-1)
		other_foot_prev_glocation = get_bone_global_location(other_foot)
		bpy.context.scene.frame_set(frame)
		other_foot_now_glocation = get_bone_global_location(other_foot)
		bpy.context.scene.frame_set(frame+1)		
		other_diff_glocation_next = get_bone_global_location(other_foot) - other_foot_now_glocation
		other_walking_vector = Vector((other_diff_glocation_next[0], other_diff_glocation_next[1], 0))

		#print("frame = "+str(frame))
		if walking_vector @ other_walking_vector < 0:
			#print("We confirmed that the other foot is going backwards")
			ref_glocation_value = walking_vector @ ref_foot_prev_glocation 
			other_glocation_value = walking_vector @ other_foot_prev_glocation 
			if ref_glocation_value < other_glocation_value:
				#print("We confirmed that ref foot is behind the other foot")
				if ref_foot == "Toe_L":
					ref_foot = "Toe_R"
					other_foot = "Toe_L"
				else:
					ref_foot = "Toe_L"
					other_foot = "Toe_R"

def apply_steady_feet_ref():
	global player_selected_anim
	# Let's check what we have selected
	ref_foot = bpy.data.objects[player_selected_anim].data.bones.active.name
	if ref_foot != "Toe_R" and ref_foot != "Toe_L":
		print("Please select one of the feet")
		return
	
	# We apply the ref walk algorithm on the selected foot
	apply_ref_walk(True)
	
	# We take to other leg
	if ref_foot == "Toe_R":
		other_foot = "Toe_L"
		other_foot_ = "Foot_L"
		other_lowerleg = redirect_bodypart_anim("lowerleg_left")
		other_upperleg = redirect_bodypart_anim("upperleg_left")
	else:
		other_foot = "Toe_R"
		other_foot_ = "Foot_R"
		other_lowerleg = redirect_bodypart_anim("lowerleg_right")
		other_upperleg = redirect_bodypart_anim("upperleg_right")
	
	# Remove animation data from other leg, if any
	start = bpy.context.scene.frame_start
	end = bpy.context.scene.frame_end
	for frame in range(start+1, end+1):
		bpy.data.objects[player_selected_anim].pose.bones[other_lowerleg].keyframe_delete(data_path='rotation_quaternion', frame=(frame))
		bpy.data.objects[player_selected_anim].pose.bones[other_foot].keyframe_delete(data_path='rotation_quaternion', frame=(frame))
		bpy.data.objects[player_selected_anim].pose.bones[other_foot_].keyframe_delete(data_path='rotation_quaternion', frame=(frame))

	# Create a temporary empty object in same position of other_foot
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.empty_add(type="SPHERE", location=get_bone_global_location(other_foot))
	bpy.data.objects["Empty"].name = "__temp1"
	loc_position_obj = bpy.data.objects["__temp1"]
	
	bpy.ops.object.select_all(action='DESELECT')
	bpy.context.view_layer.objects.active = bpy.data.objects[player_selected_anim]
	bpy.data.objects[player_selected_anim].select_set(True)
	bpy.ops.object.mode_set(mode='POSE')
	bpy.data.objects[player_selected_anim].data.bones[ref_foot].select = True

	# Apply a location constraint on the other foot
	if "Copy Location" in bpy.data.objects[player_selected_anim].pose.bones[other_foot].constraints:
		bpy.data.objects[player_selected_anim].pose.bones[other_foot].constraints.remove(
			bpy.data.objects[player_selected_anim].pose.bones[other_foot].constraints["Copy Location"]
		)
	bpy.data.objects[player_selected_anim].pose.bones[other_foot].constraints.new(type = 'COPY_LOCATION')
	bpy.data.objects[player_selected_anim].pose.bones[other_foot].constraints["Copy Location"].target = loc_position_obj

	# Apply the auto IK constraint on the other foot
	if "IK" in bpy.data.objects[player_selected_anim].pose.bones[other_foot_].constraints:
		bpy.data.objects[player_selected_anim].pose.bones[other_foot_].constraints.remove(
			bpy.data.objects[player_selected_anim].pose.bones[other_foot_].constraints["IK"]
		)
	bpy.data.objects[player_selected_anim].pose.bones[other_foot_].constraints.new(type = 'IK')
	bpy.data.objects[player_selected_anim].pose.bones[other_foot_].constraints["IK"].target = bpy.data.objects[player_selected_anim]
	bpy.data.objects[player_selected_anim].pose.bones[other_foot_].constraints["IK"].subtarget = other_foot

	# Apply bake, which will remove contraints
	bake_animation()
	
	#Remove the temporary object
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.data.objects.remove(loc_position_obj, do_unlink=True)
	bpy.ops.object.mode_set(mode='POSE')

bpy.types.Scene.players_list_animation = bpy.props.EnumProperty(items= players_available,
	name = "Player",
	description = "Player to consider for animation",
	update = change_animation_player_fun)

bpy.context.scene.players_list_animation = "None"

class PANEL_PT_BodynodesAnimation(bpy.types.Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'View'
	bl_label = "Bodynodes Animation"
	
	def draw(self, context):
		layout = self.layout

		row = layout.row()
		row.operator("bodynodes.load_armature_config_anim", text="Load Bones Config")
		row.enabled = True
		
		global bodynodes_armature_config_anim
		if not bodynodes_armature_config_anim:
			row = layout.row()
			row.scale_y = 1.0
			col1 = row.column()
			col1.label(text="Load a configuration file")
			return
	
		row = layout.row()
		row.prop(context.scene, 'players_list_animation')

		if player_selected_anim not in bpy.data.objects:
			row = layout.row()
			row.scale_y = 1.0
			col1 = row.column()
			col1.label(text="Select a player")
			return

		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.label(text="Animation:")
		col2 = row.column()
		col2.operator("bodynodes.load_animation", text="Load")
		col2.enabled = True		
		col3 = row.column()
		col3.operator("bodynodes.bake_animation", text="Bake")
		col3.enabled = True

		layout.label(text="Editor:")
		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.operator("bodynodes.create_animation_editor", text="Create")
		col1.enabled = not bodynodes_panel_anim["editor"]["created"]
		col3 = row.column()
		col3.operator("bodynodes.showhide_animation_editor",
			text="Show" if bodynodes_panel_anim["editor"]["is_hidden"] else "Hide")
		col3.enabled = bodynodes_panel_anim["editor"]["created"]
		col2 = row.column()
		col2.operator("bodynodes.save_animation_editor", text="Save")
		col2.enabled = True #bodynodes_panel_anim["editor"]["created"]
		col4 = row.column()
		col4.operator("bodynodes.destroy_animation_editor", text="Destroy")
		col4.enabled = True #bodynodes_panel_anim["editor"]["created"]
		
		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.label(text="Walking:")
		col2 = row.column()
		col2.operator("bodynodes.apply_auto_walk", text="Auto Walk")
		col2.enabled = True
		col3 = row.column()
		col3.operator("bodynodes.apply_ref_walk", text="Ref Walk")
		col3.enabled = True

		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.label(text="Steady:")
		col2 = row.column()
		col2.operator("bodynodes.apply_steady_feet_ref", text="Steady Feet Ref")
		col2.enabled = True

		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.label(text="Changes:")		
		col2 = row.column()
		col2.operator("bodynodes.startdone_change_animation",
			text="Done" if bodynodes_panel_anim["change"]["started"] else "Start" )		
		col2.enabled = True

		row = layout.row()
		row.scale_y = 1.0
		col1 = row.column()
		col1.operator("bodynodes.extract_animation", text="Extract Animation")
		col1.enabled = True

		row = layout.row()
		row.operator("bodynodes.close_animation", text="Close")

class BodynodesBakeAnimationOperator(bpy.types.Operator):
	bl_idname = "bodynodes.bake_animation"
	bl_label = "Bake Animation Operator"
	bl_description = "Bake the animation moving it from the bodynodes to the bones"

	def execute(self, context):
		bake_animation()
		return {'FINISHED'}

class BodynodesExtractAnimationOperator(bpy.types.Operator, ExportHelper):
	bl_idname = "bodynodes.extract_animation"
	bl_label = "Extract Animation Operator"
	bl_description = "Extract animation from bones as data and save it in a json file"

	# ExportHelper mixin class uses this
	filename_ext = ".json"

	filter_glob: bpy.props.StringProperty(
		default="*.json",
		options={'HIDDEN'},
		maxlen=255,  # Max internal buffer length, longer would be clamped.
	)
	
	def execute(self, context):
		extract_animation(self.filepath)
		return {'FINISHED'}

class BodynodesLoadArmatureConfigAnimOperator(bpy.types.Operator, ImportHelper):
	bl_idname = "bodynodes.load_armature_config_anim"
	bl_label = "Load Armature Configuration Operator"
	bl_description = "Load armature configuration from a json file"

	filter_glob: bpy.props.StringProperty( 
		default='*.json',
		options={'HIDDEN'}
	)

	def execute(self, context):
		load_armature_config_anim(self.filepath)
		return {'FINISHED'}

class BodynodesLoadAnimationOperator(bpy.types.Operator, ImportHelper):
	bl_idname = "bodynodes.load_animation"
	bl_label = "Load Animation Operator"
	bl_description = "Load animation from a json file"

	filter_glob: bpy.props.StringProperty( 
		default='*.json',
		options={'HIDDEN'}
	)

	def execute(self, context):
		load_animation(self.filepath)
		return {'FINISHED'}

class BodynodesCreateAnimationEditorOperator(bpy.types.Operator):
	bl_idname = "bodynodes.create_animation_editor"
	bl_label = "Create Animation Editor Operator"
	bl_description = "Create the animation editor environment"

	def execute(self, context):
		create_animation_editor()
		return {'FINISHED'}

class BodynodesSaveAnimationEditorOperator(bpy.types.Operator):
	bl_idname = "bodynodes.save_animation_editor"
	bl_label = "Save Animation Editor Operator"
	bl_description = "Save the animation of editor environment"

	def execute(self, context):
		save_animation_editor()
		return {'FINISHED'}

class BodynodesShowHideAnimationEditorOperator(bpy.types.Operator):
	bl_idname = "bodynodes.showhide_animation_editor"
	bl_label = "ShowHide Animation Editor Operator"
	bl_description = "Show/Hide animation bodies in editor environment"

	def execute(self, context):
		showhide_animation_editor()
		return {'FINISHED'}

class BodynodesDestroyAnimationEditorOperator(bpy.types.Operator):
	bl_idname = "bodynodes.destroy_animation_editor"
	bl_label = "Destroy Animation Editor Operator"
	bl_description = "Destroy animation editor environment"

	def execute(self, context):
		destroy_animation_editor()
		return {'FINISHED'}

class BodynodesApplyWalkAutoOperator(bpy.types.Operator):
	bl_idname = "bodynodes.apply_auto_walk"
	bl_label = "Apply Auto Walk Operator"
	bl_description = "Apply walk algorithm with automatic reference selection"

	def execute(self, context):
		apply_auto_walk()
		return {'FINISHED'}

class BodynodesApplyWalkRefOperator(bpy.types.Operator):
	bl_idname = "bodynodes.apply_ref_walk"
	bl_label = "Apply Ref Walk Operator"
	bl_description = "Apply walk algorithm using as reference the selected bone"

	def execute(self, context):
		apply_ref_walk()
		return {'FINISHED'}

class BodynodesApplySteadyFeetRefOperator(bpy.types.Operator):
	bl_idname = "bodynodes.apply_steady_feet_ref"
	bl_label = "Apply Steady Feet Ref Operator"
	bl_description = "Apply steady feet algorithm using as reference the selected foot"

	def execute(self, context):
		apply_steady_feet_ref()
		return {'FINISHED'}

class BodynodesStartDoneChangeAnimationOperator(bpy.types.Operator):
	bl_idname = "bodynodes.startdone_change_animation"
	bl_label = "StartDone Change Animation Operator"
	bl_description = "Apply changes of bones to all animation frames"

	def execute(self, context):
		if bodynodes_panel_anim["change"]["started"]:
			done_change_animation()
		else:
			start_change_animation()
		return {'FINISHED'}
		
class BodynodesCloseAnimationOperator(bpy.types.Operator):
	bl_idname = "bodynodes.close_animation"
	bl_label = "Close Panel Operator"
	bl_description = "Close the Bodynodes animation panel"

	def execute(self, context):
		unregister_animation()
		return {'FINISHED'}


def register_animation():
	bpy.utils.register_class(BodynodesLoadArmatureConfigAnimOperator)
	bpy.utils.register_class(BodynodesCreateAnimationEditorOperator)
	bpy.utils.register_class(BodynodesExtractAnimationOperator)
	bpy.utils.register_class(BodynodesLoadAnimationOperator)
	bpy.utils.register_class(BodynodesBakeAnimationOperator)	
	bpy.utils.register_class(BodynodesSaveAnimationEditorOperator)
	bpy.utils.register_class(BodynodesShowHideAnimationEditorOperator)
	bpy.utils.register_class(BodynodesDestroyAnimationEditorOperator)
	bpy.utils.register_class(BodynodesApplyWalkAutoOperator)
	bpy.utils.register_class(BodynodesApplyWalkRefOperator)
	bpy.utils.register_class(BodynodesApplySteadyFeetRefOperator)
	bpy.utils.register_class(BodynodesStartDoneChangeAnimationOperator)
	bpy.utils.register_class(BodynodesCloseAnimationOperator)
	
	bpy.utils.register_class(PANEL_PT_BodynodesAnimation)

def unregister_animation():
	bpy.utils.unregister_class(BodynodesLoadArmatureConfigAnimOperator)
	bpy.utils.unregister_class(BodynodesCreateAnimationEditorOperator)
	bpy.utils.unregister_class(BodynodesExtractAnimationOperator)
	bpy.utils.unregister_class(BodynodesLoadAnimationOperator)
	bpy.utils.unregister_class(BodynodesBakeAnimationOperator)	
	bpy.utils.unregister_class(BodynodesSaveAnimationEditorOperator)
	bpy.utils.unregister_class(BodynodesShowHideAnimationEditorOperator)
	bpy.utils.unregister_class(BodynodesDestroyAnimationEditorOperator)
	bpy.utils.unregister_class(BodynodesApplyWalkAutoOperator)
	bpy.utils.unregister_class(BodynodesApplyWalkRefOperator)
	bpy.utils.unregister_class(BodynodesApplySteadyFeetRefOperator)
	bpy.utils.unregister_class(BodynodesStartDoneChangeAnimationOperator)
	bpy.utils.unregister_class(BodynodesCloseAnimationOperator)
	
	bpy.utils.unregister_class(PANEL_PT_BodynodesAnimation)

if __name__ == "__main__" :
	register_animation()
	




