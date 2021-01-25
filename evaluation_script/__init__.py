"""
Q. How to install custom python pip packages?

A. Uncomment the below code to install the custom python packages.

import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install("shapely")
install("requests")

"""

from .main import evaluate
