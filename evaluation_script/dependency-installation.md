## Add custom dependencies for evaluation (Optional)

EvalAI allows challenge organizers to include a custom `__init__.py` script in the `evaluation_script/` directory to install Python packages or set up the environment before evaluation begins, without needing to modify the evaluation base worker image.

The `__init__.py` script is useful for:

- Installing pip packages (e.g., `nltk`, `shapely`)

- Downloading resources (e.g., model files, corpora)

- Installing local Python packages bundled in the repo

- Delegating final evaluation to `main.py`

## Structure

```
evaluation_script/
├── __init__.py   # Custom packages & execution logic
├── main.py       # Evaluation logic
```

## Example

Here's a usage example of the `__init__.py` script:

```
import os
import subprocess
import sys
from pathlib import Path

def install(package):
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing {package}: {e.stderr}")

def install_local_package(folder_name):
    try:
        subprocess.run([
            sys.executable,
            "-m",
            "pip",
            "install",
            os.path.join(str(Path(__file__).parent.absolute()), folder_name)
        ], check=True)
        print(f"Installed local package from {folder_name}.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing local package from {folder_name}: {e.stderr}")

# Install dependencies
install("shapely==1.7.1")
install("requests==2.25.1")

# Install local package (optional)
install_local_package("my_custom_lib")

# Run the evaluation logic from main.py
from .main import evaluate

```

## Execution Behavior

- When `evaluation_script/` is loaded, Python executes `__init__.py`.

- This script can install dependencies, set up the environment, and then import and call `evaluate()` from `main.py`.

- All output from the script appears in the submission logs.