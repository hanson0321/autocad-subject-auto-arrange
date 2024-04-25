import ezdxf
import sys

def usage(error_msg=None):
    print("Usage: cadinfo.py [--summary] [--help] [--formats] [--version] file_name")
    if error_msg:
        print(f"FAILURE: {error_msg}")
        return False
    return True

def version():
    print("cadinfo was compiled against libopencad 0.1")  # Dummy version
    print("and is running against libopencad 0.1")
    return True

def formats():
    print("Supported formats: DXF 2000, DXF R12, ...")  # Example formats
    return True

def main(argv):
    if len(argv) < 1:
        return -len(argv)
    elif len(argv) == 1:
        return usage()

    summary = False
    cad_file_path = None

    for arg in argv[1:]:
        if arg in ("-h", "--help"):
            return usage()
        elif arg in ("-f", "--formats"):
            return formats()
        elif arg in ("-v", "--version"):
            return version()
        elif arg in ("-s", "--summary"):
            summary = True
        else:
            cad_file_path = arg

    if not cad_file_path:
        return usage("No CAD file path provided")

    try:
        doc = ezdxf.readfile(cad_file_path)
    except IOError:
        print(f"Open CAD file {cad_file_path} failed.")
        return False

    msp = doc.modelspace()
    for entity in msp:
        if not summary:
            print(str(entity))
        print(f"Entity color: #{entity.dxf.color}")

    return True

if __name__ == "__main__":
    success = main(sys.argv)
    sys.exit(0 if success else 1)
