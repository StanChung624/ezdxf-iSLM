# EBG DXF Generator

This project generates DXF files for EBG (Electromagnetic Band Gap) structures and provides a `.vtu` output for 2D viewing in ParaView. The primary workflow supports **iSLM** output standards.

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   ```

2. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage: iSLM Export Workflow

The `LayoutTool` class from `src.layout_tool` uses a "Substrate" + "Unit Design" + "Instances" workflow, which directly maps to iSLM's global and unit DXF formats. A unit design can be a single shape or composed of multiple shapes (rectangles, circles, ellipses) placed relative to the unit's local origin. All generated files are placed in an `output` folder to keep the workspace clean.

### Example (`example_layout.py`)

```python
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
```

Run the example script:
```bash
source .venv/bin/activate
python3 example_layout.py
```

### Outputs generated in the `output/` directory:

1. **`global.dxf`**: 
   - Contains the `substrate` layer with the drawn substrate geometry.
   - Contains the mandatory `Center` layer, featuring strictly `point` entities corresponding to each instance's global coordinate, required for iSLM copy/paste references.
2. **`unit_design.dxf`**:
   - Contains the chosen composite unit shapes (circles, rectangles, ellipses) positioned relative to the local origin `(0, 0, 0)`.
   - Contains the mandatory `Center` layer featuring a single `point` entity at the origin `(0, 0, 0)`.
3. **`layout_output.vtu`**: 
   - A 2D flat mesh combining both the Substrate outline and the mapped Units correctly positioned at their instances' center points. Open this file in **ParaView** to see the full structural layout simultaneously.
