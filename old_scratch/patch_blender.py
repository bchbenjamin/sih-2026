import re

with open('scripts/phase6/build_blender_scene.py', 'r') as f:
    content = f.read()

# 1. Modify material creation to add foam logic
old_material = '''def material(name, color, metallic=0.0, roughness=0.6, alpha=1.0):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, alpha)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, alpha)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    if alpha < 1:
        shader.inputs["Alpha"].default_value = alpha
        try:
            result.surface_render_method = "DITHERED"  # Blender 4.2+
        except AttributeError:
            result.blend_method = "BLEND"  # Blender 3.x/4.0 compatibility
    return result'''

new_material = '''def material(name, color, metallic=0.0, roughness=0.6, alpha=1.0, is_water=False):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, alpha)
    result.use_nodes = True
    nodes = result.node_tree.nodes
    links = result.node_tree.links
    shader = nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, alpha)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    
    if is_water:
        # Foam setup
        foam_attr = nodes.new('ShaderNodeAttribute')
        foam_attr.attribute_name = "Foam"
        
        foam_shader = nodes.new('ShaderNodeEmission')
        foam_shader.inputs["Color"].default_value = (0.9, 0.95, 1.0, 1.0)
        foam_shader.inputs["Strength"].default_value = 1.5
        
        mix_shader = nodes.new('ShaderNodeMixShader')
        
        out_node = nodes.get("Material Output")
        
        links.new(foam_attr.outputs["Color"], mix_shader.inputs["Fac"])
        links.new(shader.outputs["BSDF"], mix_shader.inputs[1])
        links.new(foam_shader.outputs["Emission"], mix_shader.inputs[2])
        links.new(mix_shader.outputs["Shader"], out_node.inputs["Surface"])
        
    if alpha < 1:
        shader.inputs["Alpha"].default_value = alpha
        try:
            result.surface_render_method = "DITHERED"
        except AttributeError:
            result.blend_method = "BLEND"
    return result'''

content = content.replace(old_material, new_material)

# 2. Update mesh_object to apply vertex colors
old_mesh_obj = '''def mesh_object(name, vertices, faces, material_value):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material_value)
    mesh.update()
    object_value = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(object_value)
    return object_value'''

new_mesh_obj = '''def mesh_object(name, vertices, faces, material_value, vcolors=None, displace_tex=None, frame=0):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    
    if vcolors:
        color_layer = mesh.color_attributes.new(name="Foam", type='FLOAT_COLOR', domain='POINT')
        for i, val in enumerate(vcolors):
            color_layer.data[i].color = (val, val, val, 1.0)
            
    mesh.materials.append(material_value)
    mesh.update()
    object_value = bpy.data.objects.new(name, mesh)
    
    if displace_tex:
        mod = object_value.modifiers.new(name="Turbulence", type='DISPLACE')
        mod.texture = displace_tex
        mod.strength = 0.5
        mod.direction = 'Z'
        mod.texture_coords = 'GLOBAL'
        # Emulate flowing water by animating an empty (we use a simple approach: just offset based on frame)
        # Actually, global coords + an empty is best. We'll link it in main.
    
    bpy.context.collection.objects.link(object_value)
    return object_value'''

content = content.replace(old_mesh_obj, new_mesh_obj)

# 3. Update water_mesh to return vcolors
old_water_mesh = '''def water_mesh(terrain, depth, arrival, elapsed, scale, x_cell_m, y_cell_m):
    wet = (depth > 0) & np.isfinite(arrival) & (arrival <= elapsed)
    rows, cols = terrain.shape
    vertices = []
    faces = []
    
    vertex_index = np.full((rows + 1, cols + 1), -1, dtype=np.int32)
    
    for r in range(rows):
        for c in range(cols):
            if wet[r, c]:
                corners = [(r, c), (r, c+1), (r+1, c+1), (r+1, c)]
                face = []
                for cr, cc in corners:
                    if vertex_index[cr, cc] == -1:
                        vertex_index[cr, cc] = len(vertices)
                        x = (cc - 0.5 - (cols - 1) / 2) * x_cell_m / scale
                        y = (cr - 0.5 - (rows - 1) / 2) * y_cell_m / scale
                        
                        z_sum = 0
                        z_count = 0
                        for dr, dc in [(-1, -1), (-1, 0), (0, -1), (0, 0)]:
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < rows and 0 <= nc < cols and wet[nr, nc]:
                                z_sum += (terrain[nr, nc] + depth[nr, nc]) / scale
                                z_count += 1
                        z = z_sum / z_count if z_count > 0 else 0
                        
                        vertices.append((x, y, z))
                    face.append(vertex_index[cr, cc])
                faces.append(tuple(face))
                
    return vertices, faces'''

new_water_mesh = '''def water_mesh(terrain, depth, arrival, elapsed, scale, x_cell_m, y_cell_m):
    wet = (depth > 0) & np.isfinite(arrival) & (arrival <= elapsed)
    rows, cols = terrain.shape
    vertices = []
    faces = []
    vcolors = []
    
    vertex_index = np.full((rows + 1, cols + 1), -1, dtype=np.int32)
    
    # Identify the leading edge (cells that arrived in the last 60 seconds)
    foam_threshold = 60.0
    
    for r in range(rows):
        for c in range(cols):
            if wet[r, c]:
                corners = [(r, c), (r, c+1), (r+1, c+1), (r+1, c)]
                face = []
                for cr, cc in corners:
                    if vertex_index[cr, cc] == -1:
                        vertex_index[cr, cc] = len(vertices)
                        x = (cc - 0.5 - (cols - 1) / 2) * x_cell_m / scale
                        y = (cr - 0.5 - (rows - 1) / 2) * y_cell_m / scale
                        
                        z_sum = 0
                        z_count = 0
                        arr_sum = 0
                        for dr, dc in [(-1, -1), (-1, 0), (0, -1), (0, 0)]:
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < rows and 0 <= nc < cols and wet[nr, nc]:
                                z_sum += (terrain[nr, nc] + depth[nr, nc]) / scale
                                arr_sum += arrival[nr, nc]
                                z_count += 1
                        z = z_sum / z_count if z_count > 0 else 0
                        avg_arr = arr_sum / z_count if z_count > 0 else elapsed
                        
                        foam_val = 1.0 if (elapsed - avg_arr) < foam_threshold else 0.0
                        
                        vertices.append((x, y, z))
                        vcolors.append(foam_val)
                    face.append(vertex_index[cr, cc])
                faces.append(tuple(face))
                
    return vertices, faces, vcolors'''

content = content.replace(old_water_mesh, new_water_mesh)

# 4. In main(), update material creation and add displace texture/empty + camera shake
# We will use regex to find where to inject it.
content = content.replace('water_material = material("Flood water", (0.02, 0.16, 0.52), metallic=0.15, roughness=0.18, alpha=0.72)', 
                          'water_material = material("Flood water", (0.02, 0.16, 0.52), metallic=0.15, roughness=0.18, alpha=0.72, is_water=True)')

# Add displace texture and empty
main_insert = '''
    # --- Cosmetic Enhancements ---
    displace_tex = bpy.data.textures.new("WaterTurbulence", type='CLOUDS')
    displace_tex.noise_scale = 0.5
    
    flow_empty = bpy.data.objects.new("FlowEmpty", None)
    bpy.context.collection.objects.link(flow_empty)
    # Animate empty moving over time for turbulence
    flow_empty.keyframe_insert(data_path="location", frame=1)
    flow_empty.location = (0, 20, 0)
    flow_empty.keyframe_insert(data_path="location", frame=frames)
'''
content = content.replace('    duration = metadata["simulation_duration_s"]', main_insert + '    duration = metadata["simulation_duration_s"]')

# Fix loop mesh_object call
content = content.replace('vertices, faces = water_mesh(terrain, depth, arrival, elapsed, scale, x_cell_m, y_cell_m)',
                          'vertices, faces, vcolors = water_mesh(terrain, depth, arrival, elapsed, scale, x_cell_m, y_cell_m)')
content = content.replace('water = mesh_object(f"Flood_{frame:04d}", vertices, faces, water_material)',
                          '''water = mesh_object(f"Flood_{frame:04d}", vertices, faces, water_material, vcolors=vcolors, displace_tex=displace_tex, frame=frame)
        if "Turbulence" in water.modifiers:
            water.modifiers["Turbulence"].texture_coords_object = flow_empty''')

# Add camera shake logic at end of main
camera_shake = '''
    # Camera shake at frame 24 (when flood first arrives at dam)
    cam = bpy.data.objects.get("Camera")
    if cam:
        cam.rotation_mode = 'XYZ'
        for fc in cam.animation_data.action.fcurves:
            if fc.data_path == 'rotation_euler':
                mod = fc.modifiers.new(type='NOISE')
                mod.scale = 2.0
                mod.strength = 0.05
                mod.use_restricted_range = True
                mod.frame_start = 20
                mod.frame_end = 35
                mod.blend_in = 2
                mod.blend_out = 5
'''
content = content.replace('    bounds = metadata["bounds"]', camera_shake + '    bounds = metadata["bounds"]')


with open('scripts/phase6/build_blender_scene.py', 'w') as f:
    f.write(content)

