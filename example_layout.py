import os
from src.layout_tool import LayoutTool

def main():
    layout = LayoutTool()

    # 1. Set the global substrate
    layout.set_substrate(p1=(0, 0), p2=(100, 100), base_z=0.0, layername="MOLD CAP")  # 100x100 square substrate

    # 2. Add multiple shapes to the single Unit Design
    # Now including a rotatable rectangle!
    layout.add_unit_circle(center=(0, 0), radius=5.0, base_z=0.0, layername="BUMP1")
    
    # Rotated rectangle at center (0, 10), 45 degrees
    layout.add_unit_rectangle(center=(0, 12), width=8.0, height=2.0, rotation_deg=45.0, base_z=0.0, layername="BUMP1")
    
    layout.add_unit_ellipse(center=(0, -12), major_axis=4.0, minor_axis=2.0, rotation_deg=0.0, base_z=0.0, layername="BUMP1")

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
