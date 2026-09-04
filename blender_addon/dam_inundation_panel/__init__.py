bl_info = {
    "name": "Dam Inundation Pipeline",
    "author": "Antigravity",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Dam Inundation",
    "description": "Drive the full dam inundation pipeline end-to-end",
    "warning": "",
    "doc_url": "",
    "category": "Pipeline",
}

import bpy
import yaml
import os
import subprocess
import threading
from pathlib import Path

# Try to find repo root by walking up from the current blend file or assuming cwd
def get_repo_root():
    if bpy.data.filepath:
        p = Path(bpy.data.filepath)
        while p.parent != p:
            if (p / "run_pipeline.py").exists():
                return p
            p = p.parent
    cwd = Path(os.getcwd())
    if (cwd / "run_pipeline.py").exists():
        return cwd
    return cwd

def load_yaml(file_name):
    root = get_repo_root()
    path = root / file_name
    if path.exists():
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    return {}

def save_yaml(file_name, data):
    root = get_repo_root()
    path = root / file_name
    if path.exists():
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

def get_cases(self, context):
    root = get_repo_root()
    output_dir = root / "output"
    cases = []
    if output_dir.exists():
        for d in output_dir.iterdir():
            if d.is_dir() and (d / "dam_inundation_visualization.blend").exists():
                cases.append((d.name, d.name, ""))
    if not cases:
        cases.append(("none", "No cases found", ""))
    return cases

class DAM_PG_Settings(bpy.types.PropertyGroup):
    case_name: bpy.props.StringProperty(name="Case Name")
    dam_lat: bpy.props.FloatProperty(name="Dam Lat", precision=5)
    dam_lon: bpy.props.FloatProperty(name="Dam Lon", precision=5)
    dem_west: bpy.props.FloatProperty(name="DEM West", precision=5)
    dem_south: bpy.props.FloatProperty(name="DEM South", precision=5)
    dem_east: bpy.props.FloatProperty(name="DEM East", precision=5)
    dem_north: bpy.props.FloatProperty(name="DEM North", precision=5)
    
    erodibility: bpy.props.EnumProperty(
        name="Erodibility",
        items=[
            ("low", "Low", ""),
            ("medium", "Medium", ""),
            ("high", "High", "")
        ]
    )
    breach_width_m: bpy.props.FloatProperty(name="Breach Width (m)")
    breach_time_s: bpy.props.FloatProperty(name="Breach Time (s)")
    citation: bpy.props.StringProperty(name="Citation/Source")
    
    selected_case: bpy.props.EnumProperty(
        name="Load Past Run",
        items=get_cases
    )
    
    status: bpy.props.StringProperty(name="Status", default="Idle")

class DAM_OT_LoadConfig(bpy.types.Operator):
    bl_idname = "dam.load_config"
    bl_label = "Load Config"
    
    def execute(self, context):
        settings = context.scene.dam_settings
        
        c_config = load_yaml("case_config.yaml")
        settings.case_name = c_config.get("case_name", "")
        coords = c_config.get("dam_coordinates", [0, 0])
        settings.dam_lat = coords[0]
        settings.dam_lon = coords[1]
        
        bbox = c_config.get("dem_bbox", [0,0,0,0])
        settings.dem_west = bbox[0]
        settings.dem_south = bbox[1]
        settings.dem_east = bbox[2]
        settings.dem_north = bbox[3]
        
        b_config = load_yaml("breach_calibration.yaml")
        settings.erodibility = b_config.get("erodibility", "medium")
        settings.breach_width_m = b_config.get("breach_width_m", 60.0)
        settings.breach_time_s = b_config.get("breach_time_s", 750.0)
        settings.citation = b_config.get("citation", "")
        
        return {'FINISHED'}

class DAM_OT_SaveConfig(bpy.types.Operator):
    bl_idname = "dam.save_config"
    bl_label = "Save Config"
    
    def execute(self, context):
        settings = context.scene.dam_settings
        
        # Validation for citation
        b_config = load_yaml("breach_calibration.yaml")
        old_width = b_config.get("breach_width_m", 60.0)
        old_time = b_config.get("breach_time_s", 750.0)
        
        if (settings.breach_width_m != old_width or settings.breach_time_s != old_time):
            if settings.citation == b_config.get("citation", ""):
                self.report({'ERROR'}, "Must provide a new citation if breach values are changed!")
                return {'CANCELLED'}
        
        c_config = load_yaml("case_config.yaml")
        c_config["case_name"] = settings.case_name
        c_config["dam_coordinates"] = [settings.dam_lat, settings.dam_lon]
        c_config["dem_bbox"] = [settings.dem_west, settings.dem_south, settings.dem_east, settings.dem_north]
        save_yaml("case_config.yaml", c_config)
        
        b_config["erodibility"] = settings.erodibility
        b_config["breach_width_m"] = settings.breach_width_m
        b_config["breach_time_s"] = settings.breach_time_s
        b_config["citation"] = settings.citation
        save_yaml("breach_calibration.yaml", b_config)
        
        return {'FINISHED'}

class DAM_OT_LoadCase(bpy.types.Operator):
    bl_idname = "dam.load_case"
    bl_label = "Load Selected Case"
    
    def execute(self, context):
        settings = context.scene.dam_settings
        if settings.selected_case and settings.selected_case != "none":
            root = get_repo_root()
            blend_path = root / "output" / settings.selected_case / "dam_inundation_visualization.blend"
            if blend_path.exists():
                bpy.ops.wm.open_mainfile(filepath=str(blend_path))
        return {'FINISHED'}

def run_pipeline_thread(context, root):
    settings = context.scene.dam_settings
    settings.status = "Running Colab pipeline..."
    
    # 1. Colab pipeline execution
    try:
        # Run exactly as the terminal: colab run run_on_colab.py
        # It relies on the git repository being up to date. So we commit first!
        subprocess.run(["git", "commit", "-am", "Auto-commit from Blender addon"], cwd=str(root))
        subprocess.run(["git", "push"], cwd=str(root))
        
        colab_bin = root / ".venv" / "bin" / "colab"
        
        process = subprocess.Popen([str(colab_bin), "run", "--timeout", "3600", "run_on_colab.py"], 
                                   cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            settings.status = f"Running: {line.strip()[-50:]}"
        process.wait()
        
        if process.returncode != 0:
            settings.status = "Error in colab execution!"
            return
            
        # 2. Download results
        settings.status = "Downloading results..."
        subprocess.run([str(colab_bin), "download", "/content/output_results.tar.gz"], cwd=str(root))
        subprocess.run(["tar", "-xzf", "output_results.tar.gz"], cwd=str(root))
        
        # 3. Trigger prepare_viz_data.py
        settings.status = "Preparing viz data..."
        subprocess.run(["python3", "scripts/phase6/prepare_viz_data.py"], cwd=str(root))
        
        # 4. Trigger Blender scene rebuild
        settings.status = "Rebuilding Blender scene..."
        subprocess.run(["python3", "run_pipeline.py", "--phase", "6"], cwd=str(root))
        
        settings.status = "Done!"
        
    except Exception as e:
        settings.status = f"Error: {str(e)}"

class DAM_OT_RunPipeline(bpy.types.Operator):
    bl_idname = "dam.run_pipeline"
    bl_label = "Run Pipeline End-to-End"
    
    def execute(self, context):
        # Save first
        if bpy.ops.dam.save_config() != {'FINISHED'}:
            return {'CANCELLED'}
            
        root = get_repo_root()
        thread = threading.Thread(target=run_pipeline_thread, args=(context, root))
        thread.start()
        
        return {'FINISHED'}

class DAM_PT_MainPanel(bpy.types.Panel):
    bl_label = "Dam Inundation"
    bl_idname = "DAM_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Pipeline'
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.dam_settings
        
        # Case config
        box = layout.box()
        box.label(text="Case Configuration")
        box.prop(settings, "case_name")
        row = box.row()
        row.prop(settings, "dam_lat")
        row.prop(settings, "dam_lon")
        row = box.row()
        row.prop(settings, "dem_west")
        row.prop(settings, "dem_east")
        row = box.row()
        row.prop(settings, "dem_south")
        row.prop(settings, "dem_north")
        
        # Breach Calibration
        box = layout.box()
        box.label(text="Breach Calibration")
        box.prop(settings, "erodibility")
        box.prop(settings, "breach_width_m")
        box.prop(settings, "breach_time_s")
        box.prop(settings, "citation")
        
        layout.operator("dam.load_config", icon='FILE_REFRESH')
        
        # Action
        layout.separator()
        layout.operator("dam.run_pipeline", icon='PLAY', text="Run Pipeline")
        layout.label(text=f"Status: {settings.status}")
        
        # Load past run
        layout.separator()
        box = layout.box()
        box.label(text="Past Runs")
        box.prop(settings, "selected_case")
        box.operator("dam.load_case", icon='FILE_FOLDER')

classes = (
    DAM_PG_Settings,
    DAM_OT_LoadConfig,
    DAM_OT_SaveConfig,
    DAM_OT_LoadCase,
    DAM_OT_RunPipeline,
    DAM_PT_MainPanel
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.dam_settings = bpy.props.PointerProperty(type=DAM_PG_Settings)
    
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.dam_settings

if __name__ == "__main__":
    register()
