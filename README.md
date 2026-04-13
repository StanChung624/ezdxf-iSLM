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

The `LayoutTool` class from `src.layout_tool` uses a "Substrate" + "Unit Design" + "Instances" workflow, which directly maps to iSLM's global and unit DXF formats. A unit design can be a single shape or composed of multiple shapes (rectangles, circles, ellipses) placed relative to the unit's local origin. 

### Key Features
- **Units**: Set standard physical DXF units (e.g., `"mm"`, `"um"`, `"in"`) upon initialization to support iSLM's scaling requirements.
- **Rotatable Rectangles**: The `add_unit_rectangle` method supports a `rotation_deg` parameter.
- **Composite Units**: Stack multiple shapes within a single unit design.
- **ParaView Integration**: Export a single `.vtu` wireframe file to visualize the entire global layout instantly.

### Example (`example_layout.py`)

```python
import os
from src.layout_tool import LayoutTool

def main():
    # Specify the measurement unit for the DXF export (e.g., "mm", "um", "in", "unitless")
    # Default is "mm" with a tessellation resolution of 128
    layout = LayoutTool(resolution=128, unit="um")

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

    os.makedirs("output", exist_ok=True)

    # 4. Export for iSLM
    layout.export_islm(global_filename="output/global.dxf", unit_filename="output/unit_design.dxf")

    # 5. Export a VTU for ParaView visualization (2D mesh)
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
   - Contains the chosen composite unit shapes (circles, rectangles, ellipses) positioned relative to the local origin `(0, 0, 0)`. Rectangles can be rotated using `rotation_deg`.
   - Contains the mandatory `Center` layer featuring a single `point` entity at the origin `(0, 0, 0)`.
3. **`layout_output.vtu`**: 
   - A 2D hollow line/wireframe mesh combining both the Substrate outline and the mapped Units correctly positioned at their instances' center points. Open this file in **ParaView** to see the full structural layout simultaneously.
