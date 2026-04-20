import os
from pathlib import Path
import ezdxf
from src.layout_tool import LayoutTool
from src.islm_workdir import create_islm_workdir, run_islm_tool

def _ensure_layer(doc, name: str) -> None:
    if name not in doc.layers:
        doc.layers.add(name)


def _enforce_global_metadata(global_dxf: str, anchor_point=(25.0, 25.0, 0.0)) -> None:
    doc = ezdxf.readfile(global_dxf)
    msp = doc.modelspace()

    _ensure_layer(doc, "CENTER")
    _ensure_layer(doc, "Anchor")
    _ensure_layer(doc, "mold cap")

    anchor_exists = False
    for e in msp:
        layer = e.dxf.layer
        if layer == "Center":
            e.dxf.layer = "CENTER"
        elif layer == "MOLD CAP":
            e.dxf.layer = "mold cap"
        elif layer == "Anchor" and e.dxftype() == "POINT":
            anchor_exists = True

    if not anchor_exists:
        msp.add_point(anchor_point, dxfattribs={"layer": "Anchor"})

    doc.saveas(global_dxf)


def _enforce_local_metadata(local_dxf: str) -> None:
    doc = ezdxf.readfile(local_dxf)
    msp = doc.modelspace()

    _ensure_layer(doc, "CENTER")
    _ensure_layer(doc, "U1_DIE1")
    _ensure_layer(doc, "U1_WIRE")

    for e in msp:
        if e.dxf.layer == "Center":
            e.dxf.layer = "CENTER"

    # Add representative open wires on U1_WIRE.
    wire_paths = [
        [(-3.0, -1.0), (-1.0, -0.2), (1.0, 0.2), (3.0, 1.0)],
        [(-3.0, 1.0), (-1.0, 0.2), (1.0, -0.2), (3.0, -1.0)],
        [(-2.5, 0.0), (-0.8, 0.8), (0.8, -0.8), (2.5, 0.0)],
    ]
    for pts in wire_paths:
        msp.add_lwpolyline(pts, close=False, dxfattribs={"layer": "U1_WIRE"})

    doc.saveas(local_dxf)


def main():
    # Specify the measurement unit for the DXF export (e.g., "mm", "um", "in", "unitless")
    # We can specify different units for the global DXF and the unit design DXF
    layout = LayoutTool(resolution=128, global_unit="mm", unit_design_unit="um")

    # IMPORTANT: All inputs to the LayoutTool methods (centers, radii, widths)
    # MUST be provided in the `global_unit` (e.g. mm). The tool will automatically
    # scale the shapes to the `unit_design_unit` (e.g. um) during export!

    # 1. Set global geometry on exact metadata layer names.
    layout.set_substrate(p1=(0, 0), p2=(100, 100), base_z=0.0, layername="mold cap")

    # 2. Add multiple shapes to the single Unit Design
    # Shapes are positioned relative to the unit's local origin (0,0)
    # Radius = 0.005 mm (which will export as 5.0 um in unit_design.dxf)
    layout.add_unit_rectangle(center=(0, 0), width=0.020, height=0.010, rotation_deg=0.0, base_z=0.0, layername="U1_DIE1")

    # 3. Add instances of this composite unit by their global center positions (in mm)
    layout.add_instance(center=(25, 25))
    layout.add_instance(center=(75, 25))
    layout.add_instance(center=(25, 75))
    layout.add_instance(center=(75, 75))

    # Create an output directory
    os.makedirs("output", exist_ok=True)

    # 4. Export for iSLM
    global_dxf = "output/global.dxf"
    local_dxf = "output/local.dxf"
    layout.export_islm(global_filename=global_dxf, unit_filename=local_dxf)

    # Enforce exact metadata layer names and required entities.
    _enforce_global_metadata(global_dxf, anchor_point=(25.0, 25.0, 0.0))
    _enforce_local_metadata(local_dxf)

    # 5. Export a VTU for ParaView visualization (2D mesh)
    layout.export_vtu("output/layout_output.vtu")

    # 6. Build iSLM working folder (.ini + copied DXFs)
    ini_path, _ = create_islm_workdir(
        dxf_paths=[global_dxf, local_dxf],
        out_dir="demo",
    )
    print(f"Generated iSLM ini: {ini_path}")

    # 7. Run MDX2DTo3DICDesignTool.exe with generated ini
    exe_path = Path(r"C:\Users\stanchung\Desktop\dxf_gen_mfe\MDX\Bin\MDX2DTo3DICDesignTool.exe")
    if exe_path.exists():
        return_code = run_islm_tool(str(exe_path), str(ini_path))
        print(f"MDX2DTo3DICDesignTool return code: {return_code}")
    else:
        print(f"Tool not found, skipped execution: {exe_path}")

if __name__ == "__main__":
    main()
