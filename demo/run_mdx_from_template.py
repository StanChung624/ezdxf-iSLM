import subprocess
from pathlib import Path

EXE = Path(r"C:\Users\stanchung\Desktop\dxf_gen_mfe\MDX\Bin\MDX2DTo3DICDesignTool.exe")
INI = Path(__file__).resolve().parent / "demo_runtime.ini"

raise SystemExit(subprocess.run([str(EXE), str(INI)], check=False).returncode)
