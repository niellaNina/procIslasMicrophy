from postprocessing import INPUT_DATA_PATH, SAVE_FILES_PATH
from postprocessing.utils.module1 import dummy_func1
from postprocessing.utils.module2 import dummy_func2
from postprocessing.utils.module3 import dummy_func3

import update_cip_nc


def main():
    print(f"Input data path: {INPUT_DATA_PATH}")
    print(f"Save files path: {SAVE_FILES_PATH}")
    print("Calling dummy functions:")
    dummy_func1()
    dummy_func2()
    dummy_func3()

    # Expand CIP netCDF file with dims and coords from nav file


if __name__ == "__main__":
    main()
