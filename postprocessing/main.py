from utils.module1 import dummy_func1
from utils.module2 import dummy_func2
from utils.module3 import dummy_func3
from utils.read_nav import read_nav
from utils import config

import update_cip_nc




def main():
    print("Root:", config.ROOT_DIR)
    print("Data dir:", config.DATA_DIR)
    print("Save dir:", config.SAVE_DIR)
    print("Calling dummy functions:")
    dummy_func1()
    dummy_func2()
    dummy_func3()

    # Expand CIP netCDF file with dims and coords from nav file
    postprocessing.update_cip_nc()

if __name__ == "__main__":
    main()
