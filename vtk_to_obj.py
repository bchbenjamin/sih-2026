import vtk
import sys

def convert(vtk_file, obj_file):
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(vtk_file)
    reader.Update()
    
    writer = vtk.vtkOBJWriter()
    writer.SetFileName(obj_file)
    writer.SetInputConnection(reader.GetOutputPort())
    writer.Write()

if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])
