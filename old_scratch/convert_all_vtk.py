import vtk
import sys
import glob
import os

def convert(vtk_file, obj_file):
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(vtk_file)
    reader.Update()
    writer = vtk.vtkOBJWriter()
    writer.SetFileName(obj_file)
    writer.SetInputConnection(reader.GetOutputPort())
    writer.Write()

vtk_files = sorted(glob.glob("cases/stoker/stoker_out/surface/Surface_*.vtk"))
for i, f in enumerate(vtk_files):
    obj_name = f"cases/stoker/stoker_out/blender_mesh_sequence/frame_{i+1:04d}.obj"
    convert(f, obj_name)
    if (i+1) % 50 == 0:
        print(f"Converted {i+1}/{len(vtk_files)}")
print("Done.")
