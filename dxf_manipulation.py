# %%
import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment

# Create a new DXF document.
doc = ezdxf.new(dxfversion="R2010")

# Create new table entries (layers, linetypes, text styles, ...).
doc.layers.add("TEXTLAYER", color=colors.RED)

# DXF entities (LINE, TEXT, ...) reside in a layout (modelspace, 
# paperspace layout or block definition).  
msp = doc.modelspace()

# Add entities to a layout by factory methods: layout.add_...() 
msp.add_line((0, 0), (10, 0), dxfattribs={"color": colors.YELLOW})
msp.add_text(
    "Test", 
    dxfattribs={
        "layer": "TEXTLAYER"
    }).set_placement((0, 0.2), align=TextEntityAlignment.CENTER)

# Save the DXF document.
doc.saveas("test.dxf")
# %%
import ezdxf

doc = ezdxf.new("R2000")
msp = doc.modelspace()

points = [(0, 0), (3, 0), (6, 3), (6, 6)]
msp.add_lwpolyline(points)

doc.saveas("test.dxf")
# %%
