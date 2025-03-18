"""
# Q. How to install custom python pip packages?

# A. Uncomment the below code to install the custom python packages.

import os
import subprocess
import sys
from pathlib import Path

def install(package):
    # Install a pip python package

    # Args:
    #     package ([str]): Package name with version
    try:
        subprocess.run([sys.executable,"-m","pip","install",package])
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while installing {package}: {e.stderr}")
    except FileNotFoundError:
        print("Error: Pip is not found. make sure you have pip installed.")
    except PermissionError:
        print("Error: Permission denied. ")


def install_local_package(folder_name):
    # Install a local python package

    # Args:
    #     folder_name ([str]): name of the folder placed in evaluation_script/
    
    
    try:
        subprocess.run([
            sys.executable,
            "-m",
            "pip",
            "install",
            os.path.join(str(Path(__file__).parent.absolute()), folder_name)
        ], capture_output=True, text=True, check=True)
        print(f"Successfully installed local package from {folder_name}.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while installing local package from {folder_name}: {e.stderr}")
    except FileNotFoundError:
        print("Error: Pip not found.")
    except PermissionError:
        print("Error: Permission denied. ")

install("shapely==1.7.1")
install("requests==2.25.1")

install_local_package("package_folder_name")

"""

from .main import evaluate
