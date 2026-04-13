import ezdxf
import meshio
import numpy as np
from pathlib import Path

def create_dxf(filename: str):
    """Create a simple DXF with a rectangle."""
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    
    # Add a rectangle
    points = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
    msp.add_lwpolyline(points)
    
    doc.saveas(filename)
    print(f"DXF saved to {filename}")

def dxf_to_vtu(dxf_filename: str, vtu_filename: str):
    """Convert DXF lines to a VTU file for ParaView."""
    doc = ezdxf.readfile(dxf_filename)
    msp = doc.modelspace()
    
    all_points = []
    cells = []
    point_count = 0
    
    for entity in msp:
        if entity.dxftype() == 'LWPOLYLINE':
            # Get points from polyline
            pts = np.array([(p[0], p[1], 0.0) for p in entity.get_points()])
            n_pts = len(pts)
            
            all_points.extend(pts)
            
            # Define line cells for meshio
            # Each cell is a sequence of point indices
            for i in range(n_pts - 1):
                cells.append([point_count + i, point_count + i + 1])
            
            point_count += n_pts
            
    if not all_points:
        print("No geometry found to export.")
        return

    # Create mesh object
    mesh = meshio.Mesh(
        points=np.array(all_points),
        cells=[("line", np.array(cells))]
    )
    
    mesh.write(vtu_filename)
    print(f"VTU saved to {vtu_filename}")

if __name__ == "__main__":
    dxf_path = "output.dxf"
    vtu_path = "output.vtu"
    
    create_dxf(dxf_path)
    dxf_to_vtu(dxf_path, vtu_path)
