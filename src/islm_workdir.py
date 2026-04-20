import argparse
import configparser
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


def _as_win(path: Path) -> str:
    return str(path.resolve()).replace("/", "\\")


def _copy_dxfs(dxf_paths: Sequence[Path], out_dir: Path) -> List[Path]:
    copied: List[Path] = []
    for src in dxf_paths:
        dst = out_dir / src.name
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
        copied.append(dst)
    return copied


def _build_ini(
    ini_path: Path,
    copied_dxfs: Sequence[Path],
    project_path: Path,
    project_name: str,
) -> None:
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.optionxform = str

    cfg["CommandInfo"] = {
        "CommandResult": "0",
        "ExecuteStage": "Start IC Meshing",
        "Command": "icprocessfromdxf",
    }
    cfg["ProjectInfo"] = {
        "ProjectPath": _as_win(project_path),
        "ProjectName": project_name,
        "DXFCount": str(len(copied_dxfs)),
        "MDGPath": "",
        "MFEPath": "",
    }
    cfg["Condition"] = {
        "IsSinglePKGMode": "0",
        "OutputGLB": "0",
        "LeadFrameCount": "0",
        "ChipCount": "1",
        "BumpCount": "0",
        "SubstrateCount": "0",
        "TapeCount": "0",
        "CompoundCount": "1",
        "WireCount": "0",
        "ICWireDiameter": "0.3",
        "MeshSize": "1",
        "UserDefineAttributeCount": "0",
        "AutoInelt": "",
    }
    cfg["RunnerSetting"] = {
        "RunnerArea": "0",
        "RunnerVolume": "0",
        "RunnerCount": "0",
        "GateFaceCoorCount": "0",
    }
    cfg["UserDefineAttribute"] = {}
    cfg["Information"] = {
        "Version": "0.11.12",
        "Tool": "MDX2DTo3DICDesignTool",
    }

    for idx, dxf in enumerate(copied_dxfs, start=1):
        section = f"DXF_{idx}"
        cfg[section] = {
            "Path": _as_win(dxf),
            "CenterLayer": "CENTER",
            "AnchorLayer": "Anchor",
            "ZoomRatio": "1" if idx > 1 else "1000",
        }

    with ini_path.open("w", encoding="utf-8", newline="\n") as f:
        cfg.write(f, space_around_delimiters=True)


def create_islm_workdir(
    dxf_paths: Sequence[str],
    out_dir: str = "demo",
    project_name: Optional[str] = None,
) -> Tuple[Path, List[Path]]:
    if len(dxf_paths) == 0:
        raise ValueError("At least one DXF file is required.")

    out_dir_path = Path(out_dir).resolve()
    out_dir_path.mkdir(parents=True, exist_ok=True)

    resolved_dxfs = [Path(p).resolve() for p in dxf_paths]
    missing = [p for p in resolved_dxfs if not p.exists()]
    if missing:
        missing_text = ", ".join(str(p) for p in missing)
        raise FileNotFoundError(f"DXF file(s) not found: {missing_text}")

    if project_name is None:
        project_name = uuid.uuid4().hex[:24]

    copied_dxfs = _copy_dxfs(resolved_dxfs, out_dir_path)
    ini_path = out_dir_path / f"{project_name}.ini"
    _build_ini(
        ini_path=ini_path,
        copied_dxfs=copied_dxfs,
        project_path=out_dir_path,
        project_name=project_name,
    )
    return ini_path, copied_dxfs


def run_islm_tool(exe_path: str, ini_path: str) -> int:
    cmd = [str(Path(exe_path).resolve()), str(Path(ini_path).resolve())]
    proc = subprocess.run(cmd, check=False)
    return proc.returncode


def _format_coord(x: float, y: float, z: float) -> str:
    return f"{x},{y},{z}"


def _normalize_3d_points(points: Optional[Sequence[Tuple[float, float, float]]]) -> List[Tuple[float, float, float]]:
    if points is None:
        return []
    out: List[Tuple[float, float, float]] = []
    for idx, p in enumerate(points):
        if len(p) != 3:
            raise ValueError(f"Point at index {idx} must contain 3 values, got: {p}")
        out.append((float(p[0]), float(p[1]), float(p[2])))
    return out


def write_islm_runtime_ini(
    ini_path: str,
    local_dxf_path: str,
    global_dxf_path: str,
    output_dir: str,
    project_name: str,
    anchor_coordinate: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    runner_mdg_path: Optional[str] = None,
    gate_face_coords: Optional[Sequence[Tuple[float, float, float]]] = None,
    chip_layer: str = "U1_DIE1",
    chip_z: float = 0.0,
    chip_thickness: float = 0.3,
    compound_layer: str = "mold cap",
    compound_z: float = 0.0,
    compound_thickness: float = 0.5,
    center_layer: str = "Center",
    anchor_layer: str = "Anchor",
    auto_inlet_direction: Optional[str] = None,
) -> Path:
    ini_path_obj = Path(ini_path).resolve()
    local_dxf = Path(local_dxf_path).resolve()
    global_dxf = Path(global_dxf_path).resolve()
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    if not local_dxf.exists():
        raise FileNotFoundError(f"local_dxf_path not found: {local_dxf}")
    if not global_dxf.exists():
        raise FileNotFoundError(f"global_dxf_path not found: {global_dxf}")

    runner_path_obj: Optional[Path] = None
    if runner_mdg_path:
        runner_path_obj = Path(runner_mdg_path).resolve()
        if not runner_path_obj.exists():
            raise FileNotFoundError(f"runner_mdg_path not found: {runner_path_obj}")
    if auto_inlet_direction and runner_path_obj:
        raise ValueError("auto_inlet_direction cannot be used together with runner_mdg_path.")

    gate_points = _normalize_3d_points(gate_face_coords)
    anchor = (float(anchor_coordinate[0]), float(anchor_coordinate[1]), float(anchor_coordinate[2]))
    auto_inlet = (auto_inlet_direction or "").strip()
    if auto_inlet and auto_inlet not in {"+X", "-X", "+Y", "-Y", "+Z", "-Z"}:
        raise ValueError(f"Unsupported auto_inlet_direction: {auto_inlet}. Use one of +X/-X/+Y/-Y/+Z/-Z.")

    cfg = configparser.ConfigParser(interpolation=None)
    cfg.optionxform = str

    cfg["DXF_1"] = {
        "Path": _as_win(local_dxf),
        "CenterLayer": center_layer,
        "AnchorLayer": anchor_layer,
        "ZoomRatio": "1",
    }
    cfg["DXF_2"] = {
        "Path": _as_win(global_dxf),
        "CenterLayer": center_layer,
        "AnchorLayer": anchor_layer,
        "ZoomRatio": "1",
    }
    cfg["CommandInfo"] = {
        "CommandResult": "0",
        "ExecuteStage": "Start IC Meshing",
        "Command": "icautoinletprocessfromdxf" if auto_inlet else "icprocessfromdxf",
    }
    cfg["ProjectInfo"] = {
        "ProjectPath": _as_win(output_path),
        "ProjectName": project_name,
        "DXFCount": "2",
        "MDGPath": _as_win(output_path / f"{project_name}.mdg"),
        "MFEPath": _as_win(output_path / f"{project_name}.mfe"),
    }
    cfg["Condition"] = {
        "IsSinglePKGMode": "0",
        "OutputGLB": "0",
        "LeadFrameCount": "0",
        "ChipCount": "1",
        "BumpCount": "0",
        "SubstrateCount": "0",
        "TapeCount": "0",
        "CompoundCount": "1",
        "WireCount": "0",
        "ICWireDiameter": "0.3",
        "MeshSize": "1",
        "UserDefineAttributeCount": "0",
        "AutoInelt": auto_inlet,
    }
    cfg["RunnerSetting"] = {
        "RunnerArea": "0",
        "RunnerVolume": "0",
        "RunnerCount": "1" if (runner_path_obj and not auto_inlet) else "0",
        "GateFaceCoorCount": str(len(gate_points)),
    }
    if gate_points:
        cfg["GateFaceCoorInfo"] = {str(i): _format_coord(*p) for i, p in enumerate(gate_points)}
    cfg["AnchorCoorInfo"] = {
        "AnchorCoordinate": _format_coord(*anchor),
    }
    cfg["Chip_1"] = {
        "ExtractLayer": chip_layer,
        "Z": str(float(chip_z)),
        "Thickness": str(float(chip_thickness)),
    }
    cfg["Compound_1"] = {
        "ExtractLayer": compound_layer,
        "Z": str(float(compound_z)),
        "Thickness": str(float(compound_thickness)),
    }
    cfg["UserDefineAttribute"] = {}
    if runner_path_obj and not auto_inlet:
        cfg["Runner_1"] = {
            "RunnerPath": _as_win(runner_path_obj),
            "RotateAngle": "0",
            "ShiftCoordinate": "0,0,0",
        }
    cfg["Information"] = {
        "Version": "0.11.12",
        "Tool": "MDX2DTo3DICDesignTool",
    }

    with ini_path_obj.open("w", encoding="utf-8", newline="\n") as f:
        cfg.write(f, space_around_delimiters=True)
    return ini_path_obj


def export_islm_with_ini(
    layout: Any,
    workdir: str,
    project_name: str,
    anchor_point: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    runner_mdg_path: Optional[str] = None,
    gate_face_coords: Optional[Sequence[Tuple[float, float, float]]] = None,
    chip_layer: str = "U1_DIE1",
    chip_z: float = 0.0,
    chip_thickness: float = 0.3,
    compound_layer: str = "mold cap",
    compound_z: float = 0.0,
    compound_thickness: float = 0.5,
    auto_inlet_direction: Optional[str] = None,
    run: bool = False,
    exe_path: Optional[str] = None,
) -> Dict[str, Any]:
    workdir_path = Path(workdir).resolve()
    workdir_path.mkdir(parents=True, exist_ok=True)
    output_dir = workdir_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    global_dxf = workdir_path / "global.dxf"
    local_dxf = workdir_path / "local.dxf"
    ini_path = workdir_path / f"{project_name}.ini"

    layout.export_islm(
        global_filename=str(global_dxf),
        unit_filename=str(local_dxf),
        anchor_point=anchor_point,
    )

    ini_path = write_islm_runtime_ini(
        ini_path=str(ini_path),
        local_dxf_path=str(local_dxf),
        global_dxf_path=str(global_dxf),
        output_dir=str(output_dir),
        project_name=project_name,
        anchor_coordinate=anchor_point,
        runner_mdg_path=runner_mdg_path,
        gate_face_coords=gate_face_coords,
        chip_layer=chip_layer,
        chip_z=chip_z,
        chip_thickness=chip_thickness,
        compound_layer=compound_layer,
        compound_z=compound_z,
        compound_thickness=compound_thickness,
        auto_inlet_direction=auto_inlet_direction,
    )

    result: Dict[str, Any] = {
        "workdir": workdir_path,
        "output_dir": output_dir,
        "global_dxf": global_dxf,
        "local_dxf": local_dxf,
        "ini_path": ini_path,
        "mdg_path": output_dir / f"{project_name}.mdg",
        "mfe_path": output_dir / f"{project_name}.mfe",
        "log_path": output_dir / f"{project_name}.log",
        "return_code": None,
    }

    if run:
        if not exe_path:
            raise ValueError("exe_path is required when run=True")
        cmd = [str(Path(exe_path).resolve()), str(ini_path)]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        log_text = (
            f"Command: {cmd}\n"
            f"ReturnCode: {proc.returncode}\n"
            "=== STDOUT ===\n"
            f"{proc.stdout or ''}\n"
            "=== STDERR ===\n"
            f"{proc.stderr or ''}"
        )
        result["log_path"].write_text(log_text, encoding="utf-8", newline="\n")
        result["return_code"] = proc.returncode

    return result


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an iSLM working folder and optional ini execution."
    )
    parser.add_argument(
        "--dxf",
        action="append",
        required=True,
        help="Input DXF path. Repeat for multiple files.",
    )
    parser.add_argument(
        "--out-dir",
        default="demo",
        help="Output folder for copied DXFs and generated ini.",
    )
    parser.add_argument(
        "--project-name",
        default=None,
        help="ProjectName and ini filename stem. Defaults to random 24-hex id.",
    )
    parser.add_argument(
        "--exe",
        default=None,
        help="Optional path to MDX2DTo3DICDesignTool.exe. If set, tool is executed with generated ini.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = _parse_args(argv)
    ini_path, copied = create_islm_workdir(
        dxf_paths=args.dxf,
        out_dir=args.out_dir,
        project_name=args.project_name,
    )

    print(f"Generated ini: {ini_path}")
    print("Copied DXF files:")
    for p in copied:
        print(f"  {p}")

    if args.exe:
        rc = run_islm_tool(args.exe, str(ini_path))
        print(f"Execution return code: {rc}")
        return rc

    print("Run command:")
    print(f'  "PATH/to/MDX2DTo3DICDesignTool.exe" "{ini_path}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
