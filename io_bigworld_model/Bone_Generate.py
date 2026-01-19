import bpy
from mathutils import Vector

def get_object_clean_world_location(obj):
    """
    获取对象去除父级影响后的世界坐标
    
    这是最关键的修正：获取空物体在去除父级影响后的真实世界位置
    """
    if not obj:
        return Vector((0, 0, 0))
    
    # 方法：保存当前变换，临时清除父级，获取位置，再恢复
    # 这是最准确的方法
    
    # 保存当前父级和变换
    original_parent = obj.parent
    original_matrix = obj.matrix_world.copy()
    
    try:
        # 临时清除父级
        obj.parent = None
        
        # 应用当前的世界变换
        obj.matrix_world = original_matrix
        
        # 获取位置
        location = obj.location.copy()
        
        return location
    finally:
        # 恢复父级和原始变换
        if original_parent:
            obj.parent = original_parent
            obj.matrix_world = original_matrix

def convert_empty_to_bone(empty_name, armature_name="Auto_Armature"):
    """
    将空物体转换为骨骼
    返回创建的骨骼对象
    """
    
    empty = bpy.data.objects.get(empty_name)
    if not empty or empty.type != 'EMPTY':
        print(f"错误：{empty_name} 不是空物体")
        return None
    
    # 获取或创建骨架
    if armature_name not in bpy.data.objects:
        bpy.ops.object.armature_add(enter_editmode=False, location=empty.location)
        armature = bpy.context.active_object
        armature.name = armature_name
    else:
        armature = bpy.data.objects[armature_name]
    
    # 进入编辑模式
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    
    # 创建新骨骼
    bones = armature.data.edit_bones
    new_bone = bones.new(empty.name)
    new_bone.head = Vector((0, 0, 0))
    new_bone.tail = Vector((0, 0, 0)) + Vector((0, 0.1, 0))  # 默认长度
    
    # 退出编辑模式
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return armature

def setup_armature_deformation(mesh_obj, armature, vertex_group_mapping=None):
    """
    设置骨架变形
    vertex_group_mapping: 字典，{空物体名: 顶点组名}
    """
    
    # 添加骨架修改器
    if "Armature" not in mesh_obj.modifiers:
        armature_mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
        armature_mod.object = armature
        armature_mod.use_vertex_groups = True
    
    # 如果有映射关系，重命名顶点组
    if vertex_group_mapping:
        for empty_name, vg_name in vertex_group_mapping.items():
            if vg_name in mesh_obj.vertex_groups:
                mesh_obj.vertex_groups[vg_name].name = empty_name
    
    return mesh_obj.modifiers["Armature"]

def auto_convert_empties_to_bones(empties, mesh_objects=None, armature_name="Auto_Armature", tail_length=0.1):
    """
    自动将空物体转换为骨骼系统
    empties: 空物体列表或名称列表
    mesh_objects: 需要变形的网格物体列表
    """
    
    # 创建主骨架
    armature = None
    bones_created = []
    
    for empty_item in empties:
        if isinstance(empty_item, str):
            empty = bpy.data.objects.get(empty_item)
        else:
            empty = empty_item

        if empty and empty.type == 'EMPTY':
            if not armature:
                armature = convert_empty_to_bone(empty.name, armature_name)
            else:
                
                # 进入编辑模式
                bpy.context.view_layer.objects.active = armature
                bpy.ops.object.mode_set(mode='EDIT')
                
                # 创建新骨骼
                bones = armature.data.edit_bones
                new_bone = bones.new(empty.name)
                # 设置骨骼头部位置（使用正确的世界坐标）
                new_bone.head = Vector((0, 0, 0))
                new_bone.tail = Vector((0, 0, 0)) + Vector((0, 0.1, 0))  # 默认长度

                # 退出编辑模式
                bpy.ops.object.mode_set(mode='OBJECT')

                # 添加约束
                pose_bone = armature.pose.bones[empty.name]

                # 添加复制变换约束
                copy_transform = pose_bone.constraints.new('COPY_TRANSFORMS')
                copy_transform.target = empty
                copy_transform.name = f"Copy_{empty.name}"
                
                # copy_loc = pose_bone.constraints.new('COPY_LOCATION')
                # copy_loc.target = empty
                # copy_loc.use_offset = True
                
                # copy_rot = pose_bone.constraints.new('COPY_ROTATION')
                # copy_rot.target = empty
                
                # copy_scale = pose_bone.constraints.new('COPY_SCALE')
                # copy_scale.target = empty

                # 重要：设置使用世界空间
                copy_transform.target_space = 'WORLD'
                copy_transform.owner_space = 'WORLD'
            
            bones_created.append(empty.name)
    
    # 为网格物体添加骨架修改器
    if mesh_objects and armature:
        for mesh_item in mesh_objects:
            if isinstance(mesh_item, str):
                mesh_obj = bpy.data.objects.get(mesh_item)
            else:
                mesh_obj = mesh_item
                
            if mesh_obj and mesh_obj.type == 'MESH':
                setup_armature_deformation(mesh_obj, armature)
    
    # 检查并删除默认骨骼
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    bones = armature.data.edit_bones
    if 'Bone' in bones:
        default_bone = bones['Bone']
        bones.remove(default_bone)
        bpy.ops.object.mode_set(mode='OBJECT')
    
    return armature, bones_created