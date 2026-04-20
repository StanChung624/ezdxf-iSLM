# iSLM DXF + INI Workflow

This project builds iSLM-ready DXF files and runtime INI files, then optionally runs:

- `MDX2DTo3DICDesignTool.exe <ini>`

The repo now supports two execution modes:

1. Runner mode: import a source runner `.mdg`.
2. Auto-inlet mode: no source runner `.mdg`; set inlet direction directly (for example `+X`).

## Setup

1. Create venv:
```bash
python -m venv .venv
```

2. Activate:
```bash
.venv\Scripts\activate
```

3. Install deps:
```bash
pip install -r requirements.txt
```

## Core Modules

- `src/layout_tool.py`
- `src/islm_workdir.py`

### `LayoutTool` role

`LayoutTool` creates:

- `global.dxf` (substrate + instance center points + anchor point)
- `local.dxf` (unit design + origin center point)

Important update:

- `export_islm(...)` now supports `anchor_point`.
- Anchor is generated inside export workflow on `Anchor` layer.

Signature:

```python
layout.export_islm(
    global_filename=".../global.dxf",
    unit_filename=".../local.dxf",
    anchor_point=(0.0, 0.0, 0.0),
)
```

### `islm_workdir` role

New high-level APIs:

- `write_islm_runtime_ini(...)`
- `export_islm_with_ini(...)`

They handle:

- deterministic INI generation with absolute Windows paths
- `MDGPath` / `MFEPath` output paths
- optional runner `.mdg` section
- optional gate face coordinates
- optional auto-inlet mode (`+X/-X/+Y/-Y/+Z/-Z`)
- optional direct tool execution with captured log

## New INI Writer Features

### 1) Runner mode

Provide `runner_mdg_path` and do not set `auto_inlet_direction`.

Behavior:

- `CommandInfo.Command = icprocessfromdxf`
- `RunnerSetting.RunnerCount = 1`
- `[Runner_1]` section emitted

### 2) Auto-inlet mode (no source runner `.mdg`)

Provide `auto_inlet_direction` and do not provide `runner_mdg_path`.

Behavior:

- `CommandInfo.Command = icautoinletprocessfromdxf`
- `Condition.AutoInelt = <direction>`
- `RunnerSetting.RunnerCount = 0`
- no `[Runner_1]` section

Validation:

- allowed directions: `+X`, `-X`, `+Y`, `-Y`, `+Z`, `-Z`
- setting both runner and auto-inlet raises `ValueError`

## API Usage

### Write INI from existing DXFs

```python
from src.islm_workdir import write_islm_runtime_ini

write_islm_runtime_ini(
    ini_path="trial/trial_02_output/trial_02_runtime.ini",
    local_dxf_path="trial/trial_02_output/local.dxf",
    global_dxf_path="trial/trial_02_output/global.dxf",
    output_dir="trial/trial_02_output/output",
    project_name="trial_02_runtime",
    anchor_coordinate=(0.0, 0.0, 0.0),
    gate_face_coords=[
        (10.0, 0.0, 0.0),
        (10.0, 0.0, 10.0),
        (10.0, 100.0, 0.0),
        (10.0, 100.0, 10.0),
    ],
    auto_inlet_direction="+X",  # omit for normal runner flow
)
```

### End-to-end export + ini (+ optional run)

```python
from src.layout_tool import LayoutTool
from src.islm_workdir import export_islm_with_ini

layout = LayoutTool(resolution=128, global_unit="mm", unit_design_unit="mm")
# ... build geometry ...

result = export_islm_with_ini(
    layout=layout,
    workdir="trial/trial_03_output",
    project_name="trial_03_runtime",
    anchor_point=(0.0, 0.0, 0.0),
    gate_face_coords=[
        (10.0, 0.0, 0.0),
        (10.0, 0.0, 10.0),
        (10.0, 100.0, 0.0),
        (10.0, 100.0, 10.0),
    ],
    auto_inlet_direction="+X",
    run=True,
    exe_path=r"C:\Users\stanchung\Desktop\dxf_gen_mfe\MDX\Bin\MDX2DTo3DICDesignTool.exe",
)
```

Returned keys include:

- `global_dxf`
- `local_dxf`
- `ini_path`
- `mdg_path`
- `mfe_path`
- `log_path`
- `return_code` (when `run=True`)

## Trials

### `trial_01`

Files:

- `trial/trial_01.py`
- `trial/trial_01_output/run_trial_01.py`

Geometry:

- mold cap rectangle `(10,0)` to `(100,100)`
- die size `5x5`
- die centers `(25,25)`, `(25,75)`, `(75,25)`, `(75,75)`
- anchor `(0,0,0)`

Mode:

- runner mode with source `runner_100.mdg`

### `trial_02`

Files:

- `trial/trial_02_output/trial_02_runtime.ini`
- `trial/trial_02_output/run_trial_02.py`

Mode:

- no source runner `.mdg`
- `RunnerCount = 0`
- gate face coordinates injected

Observed behavior:

- tool runs and writes `.mdg`/`.mpl`
- `.mfe` may not be generated in this configuration

### `trial_03`

Files:

- `trial/trial_03.py`
- `trial/trial_03_output/trial_03_runtime.ini`

Mode:

- uses new `export_islm_with_ini(...)`
- auto-inlet set to `+X`
- executes tool directly

Observed behavior:

- `.mdg` and `.mfe` generated
- log confirms `AutoInlet Setting: (1,0,0)`

## Running the Trials

### Trial 01

```bash
python trial\trial_01.py
python trial\trial_01_output\run_trial_01.py
```

### Trial 02

```bash
python trial\trial_02_output\run_trial_02.py
```

### Trial 03

```bash
python trial\trial_03.py
```

## Logs

There are two kinds of logs:

1. Tool-generated project log:
- `output/<project>.log`
- can be minimal/empty depending on tool behavior

2. Python-captured terminal log:
- stable path: `output/<project>.log` (overwritten by runner scripts/APIs that capture output)
- optional timestamped archival logs in trial folders

For reliable diagnostics, use the captured terminal log content (`stdout` + `stderr`), not return code alone.

## Known Tool Behaviors

- INI is read and rewritten in place by the tool.
- `return_code == 0` does not always guarantee all expected outputs exist.
- Empty `MDGPath` / `MFEPath` is unsafe and can cause internal path-format errors.
- Auto-inlet command requires `Command = icautoinletprocessfromdxf` and `Condition.AutoInelt` set.

## Current Metadata Convention (Demo/Trials)

Global DXF expected layers:

- `Anchor` (point)
- `Center` or `CENTER` (instance points; INI must match exact case used)
- `mold cap` (compound geometry)

Local DXF expected layers:

- `Center` or `CENTER`
- `U1_DIE1`
- optional wire layers (for wire-based workflows)

## Notes

- Paths in INI should remain absolute on Windows for stability.
- If layer case is changed in DXF, align `CenterLayer`/`AnchorLayer` in INI accordingly.
