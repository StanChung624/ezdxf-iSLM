import os
from src.layout_tool import LayoutTool

def main():
    # Specify the measurement unit for the DXF export (e.g., "mm", "um", "in", "unitless")
    # We can specify different units for the global DXF and the unit design DXF
    layout = LayoutTool(resolution=128, global_unit="mm", unit_design_unit="um")

    # 1. Set the global substrate
    layout.set_substrate(p1=(0, 0), p2=(100, 100), base_z=0.0)

    # 2. Add multiple shapes to the single Unit Design
    # Shapes are positioned relative to the unit's local origin (0,0)
    layout.add_unit_circle(center=(0, 0), radius=5.0, base_z=0.0, layername="bumps")
    
    # Rotated rectangle!
    layout.add_unit_rectangle(center=(0, 12), width=8.0, height=2.0, rotation_deg=45.0, base_z=0.0, layername="bumps_rect")
    
    layout.add_unit_ellipse(center=(0, -12), major_axis=4.0, minor_axis=2.0, rotation_deg=0.0, base_z=0.0, layername="bumps_ellipse")

    # 3. Add instances of this composite unit by their global center positions
    layout.add_instance(center=(25, 25))
    layout.add_instance(center=(75, 25))
    layout.add_instance(center=(25, 75))
    layout.add_instance(center=(75, 75))

    # Create an output directory
    os.makedirs("output", exist_ok=True)

    # 4. Export for iSLM
    layout.export_islm(global_filename="output/global.dxf", unit_filename="output/unit_design.dxf")

    # 5. Export a VTU for ParaView visualization (2D mesh)
    layout.export_vtu("output/layout_output.vtu")

if __name__ == "__main__":
    main()
