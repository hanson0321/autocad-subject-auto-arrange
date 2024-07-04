import ezdxf, matplotlib
import matplotlib.pyplot as plt


def display_dxf(file_path):
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()

    fig, ax = plt.subplots()
    for entity in msp:
        print(entity, type(entity))
        
        if entity.dxftype() == 'LWPOLYLINE':
            points = list(entity.get_points('xy'))
            x, y = zip(*points)
            print(x,y)
            ax.plot(x,y, 'r-', linewidth =0.5)
            
        elif entity.dxftype() == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            x = [start.x, end.x]
            y = [start.y, end.y]
            print(x, y)
            ax.plot(x, y, 'b-', linewidth=0.5)

    ax.set_aspect('equal', adjustable = 'box')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('DXF Display')
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    file_path = '/Users/lilianliao/Documents/研究所/Lab/Layout Generation/code/input_dxf/result.dxf'
    display_dxf(file_path)