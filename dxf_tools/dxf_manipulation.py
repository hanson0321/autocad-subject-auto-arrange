import ezdxf
from ezdxf.enums import TextEntityAlignment
import time
import os


def draw_dxf(result, feasible_area):
    points = {}
    names = []
    doc = ezdxf.new("R2000")
    doc.styles.new('MandarinStyle', dxfattribs={'font': 'Arial Unicode MS'})
    msp = doc.modelspace()

    # 處理結果並生成點列表
    for object_id, object_info in result.items():
        x = object_info['x']
        y = object_info['y']
        w = object_info['w']
        h = object_info['h']
        names.append(object_info['name'])
        point = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
        points.update({object_id: point})

    # 在模型空間中添加文本和多段線
    for object_id, point in points.items():
        # 計算中心點
        center_x = (point[0][0] + point[2][0]) / 2
        center_y = (point[0][1] + point[2][1]) / 2

        msp.add_text(
            names[object_id],
            dxfattribs={
                "layer": "TEXTLAYER",
                "style": "MandarinStyle",
                "height": 40  # 設置字體高度
            }
        ).set_placement((center_x, center_y), align=TextEntityAlignment.MIDDLE_CENTER)  # 設置對齊方式為置中
        msp.add_lwpolyline(point)
    msp.add_lwpolyline(feasible_area)

    # 確保目錄存在
    output_dir = "output_dxf"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 生成文件名並保存
    timestr = time.strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(output_dir, f"optresult{timestr}.dxf")

    doc.saveas(file_path)