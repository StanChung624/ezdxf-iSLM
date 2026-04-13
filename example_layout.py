import os
from src.layout_tool import LayoutTool

def main():
    layout = LayoutTool()

    # 1. Set the global substrate
    # It will be drawn from (0,0) to (100,100) on the global DXF
    layout.set_substrate(p1=(0, 0), p2=(100, 100), base_z=0.0)

    # 2. Add multiple shapes to the single Unit Design
    # The shapes are positioned relative to the unit's local origin (0,0)
    layout.add_unit_circle(center=(0, 0), radius=5.0, base_z=0.0, layername="bumps")
    layout.add_unit_rectangle(center=(0, 10), width=4.0, height=2.0, base_z=0.0, layername="bumps_rect")
    layout.add_unit_ellipse(center=(0, -10), major_axis=4.0, minor_axis=2.0, rotation_deg=0.0, base_z=0.0, layername="bumps_ellipse")

    # 3. Add instances of this composite unit by their global center positions
    layout.add_instance(center=(25, 25))
    layout.add_instance(center=(75, 25))
    layout.add_instance(center=(25, 75))
    layout.add_instance(center=(75, 75))

    # Create an output directory so we don't clutter the root folder
    os.makedirs("output", exist_ok=True)

    # 4. Export for iSLM
    # This generates "output/global.dxf" and "output/unit_design.dxf"
    layout.export_islm(global_filename="output/global.dxf", unit_filename="output/unit_design.dxf")

    # 5. Export a VTU for ParaView visualization (2D mesh)
    # This visualizes the substrate and all instances in their global positions
    layout.export_vtu("output/layout_output.vtu")

if __name__ == "__main__":
    main()
