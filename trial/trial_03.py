from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.islm_workdir import export_islm_with_ini
from src.layout_tool import LayoutTool


def main() -> None:
    out_dir = Path(__file__).resolve().parent / "trial_03_output"
    out_dir.mkdir(parents=True, exist_ok=True)

    layout = LayoutTool(resolution=128, global_unit="mm", unit_design_unit="mm")
    layout.set_substrate(p1=(10, 0), p2=(100, 100), base_z=0.0, layername="mold cap")
    layout.add_unit_rectangle(
        center=(0.0, 0.0),
        width=5.0,
        height=5.0,
        rotation_deg=0.0,
        base_z=0.0,
        layername="U1_DIE1",
    )
    layout.add_instance(center=(25, 25))
    layout.add_instance(center=(25, 75))
    layout.add_instance(center=(75, 25))
    layout.add_instance(center=(75, 75))

    result = export_islm_with_ini(
        layout=layout,
        workdir=str(out_dir),
        project_name="trial_03_runtime",
        anchor_point=(0.0, 0.0, 0.0),
        chip_z=0.0,
        chip_thickness=0.3,
        compound_z=0.0,
        compound_thickness=0.5,
        auto_inlet_direction="+X",
        run=True,
        exe_path=r"C:\Users\stanchung\Desktop\dxf_gen_mfe\MDX\Bin\MDX2DTo3DICDesignTool.exe",
    )

    print(f"Generated: {result['global_dxf']}")
    print(f"Generated: {result['local_dxf']}")
    print(f"Generated: {result['ini_path']}")
    print(f"Log: {result['log_path']}")
    print(f"Return code: {result['return_code']}")


if __name__ == "__main__":
    main()
