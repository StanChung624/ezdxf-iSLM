import ezdxf
import meshio
import numpy as np
from typing import Tuple, Optional, List

class LayoutTool:
    def __init__(self):
        self.substrate = None
        self.unit_shapes = []
        self.instance_centers = []

    def set_substrate(self, p1: Tuple[float, float], p2: Tuple[float, float], base_z: float = 0.0, layername: str = "substrate"):
        """Set the rectangular substrate."""
        self.substrate = {
            "type": "rectangle",
            "p1": p1,
            "p2": p2,
            "base_z": base_z,
            "layer": layername
        }

    def add_unit_rectangle(self, center: Tuple[float, float], width: float, height: float, rotation_deg: float = 0.0, base_z: float = 0.0, layername: str = "bumps"):
        """Add a rectangle to the unit design, positioned relative to the unit's local origin."""
        self.unit_shapes.append({
            "type": "rectangle",
            "center": center,
            "width": width,
            "height": height,
            "rotation": rotation_deg,
            "base_z": base_z,
            "layer": layername
        })

    def add_unit_circle(self, center: Tuple[float, float], radius: float, base_z: float = 0.0, layername: str = "bumps"):
        """Add a circle to the unit design, positioned relative to the unit's local origin."""
        self.unit_shapes.append({
            "type": "circle",
            "center": center,
            "radius": radius,
            "base_z": base_z,
            "layer": layername
        })

    def add_unit_ellipse(self, center: Tuple[float, float], major_axis: float, minor_axis: float, rotation_deg: float, base_z: float = 0.0, layername: str = "bumps"):
        """Add an ellipse to the unit design, positioned relative to the unit's local origin."""
        self.unit_shapes.append({
            "type": "ellipse",
            "center": center,
            "major_axis": major_axis,
            "minor_axis": minor_axis,
            "rotation": rotation_deg,
            "base_z": base_z,
            "layer": layername
        })

    def add_instance(self, center: Tuple[float, float]):
        """Add an instance of the unit design at the given global center coordinate."""
        self.instance_centers.append(center)

    def _get_rotated_rect_points(self, cx: float, cy: float, w: float, h: float, rotation_deg: float) -> List[Tuple[float, float]]:
        """Calculate the four corners of a rotated rectangle."""
        hw, hh = w / 2.0, h / 2.0
        ang = np.deg2rad(rotation_deg)
        cos_a = np.cos(ang)
        sin_a = np.sin(ang)
        
        # Local corners before rotation
        local_pts = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        
        # Apply rotation and translation
        pts = []
        for lx, ly in local_pts:
            rx = lx * cos_a - ly * sin_a
            ry = lx * sin_a + ly * cos_a
            pts.append((cx + rx, cy + ry))
        return pts

    def export_islm(self, global_filename: str = "global.dxf", unit_filename: str = "unit_design.dxf"):
        """
        Export to iSLM specified format:
        1. global.dxf: contains substrate geometry and a "Center" layer with POINT entities for unit locations.
        2. unit_design.dxf: contains the unit design centered at (0,0) and a "Center" point at (0,0).
        """
        # --- 1. Export global.dxf ---
        doc_global = ezdxf.new("R2010")
        msp_global = doc_global.modelspace()
        
        doc_global.layers.add("Center")
        
        if self.substrate:
            if self.substrate["layer"] not in doc_global.layers:
                doc_global.layers.add(self.substrate["layer"])
                
            p1, p2 = self.substrate["p1"], self.substrate["p2"]
            x1, y1 = min(p1[0], p2[0]), min(p1[1], p2[1])
            x2, y2 = max(p1[0], p2[0]), max(p1[1], p2[1])
            pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
            
            msp_global.add_lwpolyline(pts, close=True, dxfattribs={
                "layer": self.substrate["layer"],
                "elevation": float(self.substrate["base_z"])
            })

        for center in self.instance_centers:
            # iSLM restriction: only "point" entities in the "Center" layer
            msp_global.add_point((center[0], center[1], 0.0), dxfattribs={"layer": "Center"})
            
        doc_global.saveas(global_filename)
        print(f"Exported iSLM Global DXF: {global_filename}")

        # --- 2. Export unit_design.dxf ---
        if not self.unit_shapes:
            print("No unit design set. Skipping unit_design.dxf export.")
            return

        doc_unit = ezdxf.new("R2010")
        msp_unit = doc_unit.modelspace()
        
        doc_unit.layers.add("Center")
        
        for u in self.unit_shapes:
            if u["layer"] not in doc_unit.layers:
                doc_unit.layers.add(u["layer"])

        # Add origin point to Center layer for alignment
        msp_unit.add_point((0.0, 0.0, 0.0), dxfattribs={"layer": "Center"})

        for u in self.unit_shapes:
            base_z = u["base_z"]
            cx, cy = u["center"]
            
            if u["type"] == "rectangle":
                pts = self._get_rotated_rect_points(cx, cy, u["width"], u["height"], u["rotation"])
                msp_unit.add_lwpolyline(pts, close=True, dxfattribs={
                    "layer": u["layer"],
                    "elevation": float(base_z)
                })
                
            elif u["type"] == "circle":
                msp_unit.add_circle(center=(cx, cy, base_z), radius=u["radius"], dxfattribs={
                    "layer": u["layer"]
                })
                
            elif u["type"] == "ellipse":
                a, b = u["major_axis"], u["minor_axis"]
                ang = np.deg2rad(u["rotation"])
                N = 64
                angles = np.linspace(0, 2 * np.pi, N, endpoint=False)
                xt = a * np.cos(angles)
                yt = b * np.sin(angles)
                
                xs = cx + xt * np.cos(ang) - yt * np.sin(ang)
                ys = cy + xt * np.sin(ang) + yt * np.cos(ang)
                
                pts = list(zip(xs, ys))
                msp_unit.add_lwpolyline(pts, close=True, dxfattribs={
                    "layer": u["layer"],
                    "elevation": float(base_z)
                })

        doc_unit.saveas(unit_filename)
        print(f"Exported iSLM Unit DXF: {unit_filename}")

    def export_vtu(self, filename: str, layers: Optional[List[str]] = None):
        """Export the 2D layout representation to a VTU file for ParaView. If layers is provided, only export those layers."""
        points = []
        quads = []
        triangles = []
        
        point_idx = 0
        
        # Add Substrate
        if self.substrate:
            if layers is None or self.substrate["layer"] in layers:
                p1, p2 = self.substrate["p1"], self.substrate["p2"]
                base_z = self.substrate["base_z"]
                x1, y1 = min(p1[0], p2[0]), min(p1[1], p2[1])
                x2, y2 = max(p1[0], p2[0]), max(p1[1], p2[1])
                
                pts = [
                    (x1, y1, base_z), (x2, y1, base_z), (x2, y2, base_z), (x1, y2, base_z)
                ]
                points.extend(pts)
                quads.append([point_idx, point_idx + 1, point_idx + 2, point_idx + 3])
                point_idx += 4
                
        # Add Unit Instances
        if self.unit_shapes and self.instance_centers:
            for inst_c in self.instance_centers:
                for u in self.unit_shapes:
                    if layers is not None and u["layer"] not in layers:
                        continue
                        
                    base_z = u["base_z"]
                    cx = inst_c[0] + u["center"][0]
                    cy = inst_c[1] + u["center"][1]
                    
                    if u["type"] == "rectangle":
                        # We need to rotate around the u["center"] then translate by inst_c
                        # But simpler: use the local center relative to unit origin, then globalize
                        # The rotation is intrinsic to the rectangle shape itself.
                        local_corners = self._get_rotated_rect_points(u["center"][0], u["center"][1], u["width"], u["height"], u["rotation"])
                        global_corners = [(inst_c[0] + lx, inst_c[1] + ly, base_z) for lx, ly in local_corners]
                        
                        points.extend(global_corners)
                        quads.append([point_idx, point_idx + 1, point_idx + 2, point_idx + 3])
                        point_idx += 4
                        
                    elif u["type"] in ("circle", "ellipse"):
                        N = 32
                        points.append((cx, cy, base_z))
                        c_idx = point_idx
                        point_idx += 1
                        
                        angles = np.linspace(0, 2 * np.pi, N, endpoint=False)
                        
                        if u["type"] == "circle":
                            r = u["radius"]
                            xs = cx + r * np.cos(angles)
                            ys = cy + r * np.sin(angles)
                        else: # ellipse
                            a, b = u["major_axis"], u["minor_axis"]
                            ang = np.deg2rad(u["rotation"])
                            xt = a * np.cos(angles)
                            yt = b * np.sin(angles)
                            xs = cx + xt * np.cos(ang) - yt * np.sin(ang)
                            ys = cy + xt * np.sin(ang) + yt * np.cos(ang)
                            
                        start_idx = point_idx
                        for i in range(N):
                            points.append((xs[i], ys[i], base_z))
                            point_idx += 1
                            
                        for i in range(N):
                            p_bot1 = c_idx
                            p_bot2 = start_idx + i
                            p_bot3 = start_idx + ((i + 1) % N)
                            triangles.append([p_bot1, p_bot2, p_bot3])
        
        cells = []
        if quads:
            cells.append(("quad", np.array(quads)))
        if triangles:
            cells.append(("triangle", np.array(triangles)))
            
        if not points:
            print("No shapes to export.")
            return
            
        mesh = meshio.Mesh(points=np.array(points), cells=cells)
        mesh.write(filename)
        print(f"Exported VTU: {filename}")
