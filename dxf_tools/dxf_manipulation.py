import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment
import time

def draw_dxf(result, feasible_area):
    points = {}
    name = []
    doc = ezdxf.new("R2000")
    doc.styles.new('MandarinStyle', dxfattribs={'font': 'Arial Unicode MS'})
    msp = doc.modelspace()

    for object_id, object_info in result.items():
        x = object_info['x']
        y = object_info['y']
        w = object_info['w']
        h = object_info['h']
        name.append(object_info['name'])
        point = [(x,y),(x+w,y),(x+w,y+h),(x,y+h), (x,y)]
        points.update({object_id:point})
    
    for object_id, point in points.items():
        msp.add_text(name[object_id], dxfattribs={"layer": "TEXTLAYER"}).set_placement(point[0], align=TextEntityAlignment.LEFT)
        msp.add_lwpolyline(point)
    msp.add_lwpolyline(feasible_area)
    timestr = time.strftime("%Y%m%d_%H%M%S")
    
    doc.saveas(f"output_dxf/optresult{timestr}.dxf")


