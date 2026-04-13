import ezdxf

doc = ezdxf.new("R2010")
msp = doc.modelspace()

# Add a 2.5D rectangle (LWPOLYLINE)
points = [(0, 0), (10, 0), (10, 10), (0, 10)]
msp.add_lwpolyline(points, close=True, dxfattribs={
    "layer": "substrate",
    "elevation": 5.0,
    "thickness": 2.0
})

# Add a 2.5D circle
msp.add_circle(center=(5, 5, 5.0), radius=2.0, dxfattribs={
    "layer": "bumps",
    "thickness": 3.0
})

doc.saveas("test_25d.dxf")
print("Saved test_25d.dxf successfully.")
