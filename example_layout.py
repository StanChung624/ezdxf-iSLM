import os
from src.layout_tool import LayoutTool

def main():
    # Specify the measurement unit for the DXF export (e.g., "mm", "um", "in", "unitless")
    # We can specify different units for the global DXF and the unit design DXF
    layout = LayoutTool(resolution=128, global_unit="mm", unit_design_unit="um")

    # IMPORTANT: All inputs to the LayoutTool methods (centers, radii, widths)
    # MUST be provided in the `global_unit` (e.g. mm). The tool will automatically
    # scale the shapes to the `unit_design_unit` (e.g. um) during export!

    # 1. Set the global substrate (100mm x 100mm)
    layout.set_substrate(p1=(0, 0), p2=(100, 100), base_z=0.0)

    # 2. Add multiple shapes to the single Unit Design
    # Shapes are positioned relative to the unit's local origin (0,0)
    # Radius = 0.005 mm (which will export as 5.0 um in unit_design.dxf)
    layout.add_unit_circle(center=(0, 0), radius=0.005, base_z=0.0, layername="bumps")
    
    # Width = 0.008 mm, Height = 0.002 mm (exports as 8.0 um x 2.0 um)
    layout.add_unit_rectangle(center=(0, 0.012), width=0.008, height=0.002, rotation_deg=45.0, base_z=0.0, layername="bumps_rect")
    
    # Major = 0.004 mm, Minor = 0.002 mm (exports as 4.0 um x 2.0 um)
    layout.add_unit_ellipse(center=(0, -0.012), major_axis=0.004, minor_axis=0.002, rotation_deg=0.0, base_z=0.0, layername="bumps_ellipse")

    # 3. Add instances of this composite unit by their global center positions (in mm)
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
