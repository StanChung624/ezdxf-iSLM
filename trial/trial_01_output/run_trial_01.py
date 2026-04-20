import subprocess
from datetime import datetime
from pathlib import Path


def main() -> int:
    base = Path(__file__).resolve().parent
    output_dir = base / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    exe = Path(r"C:\Users\stanchung\Desktop\dxf_gen_mfe\MDX\Bin\MDX2DTo3DICDesignTool.exe")
    ini = base / "trial_01_runtime.ini"
    log = base / f"trial_01_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    canonical_log = output_dir / "trial_01_runtime.log"

    cmd = [str(exe), str(ini)]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)

    content = []
    content.append(f"Command: {cmd}\n")
    content.append(f"ReturnCode: {proc.returncode}\n")
    content.append("=== STDOUT ===\n")
    content.append(proc.stdout or "")
    content.append("\n=== STDERR ===\n")
    content.append(proc.stderr or "")
    text = "".join(content)

    with log.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)

    # Also write to a stable log filename in output for convenience.
    with canonical_log.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)

    print(f"Log written: {log}")
    print(f"Log written: {canonical_log}")
    print(f"Return code: {proc.returncode}")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
