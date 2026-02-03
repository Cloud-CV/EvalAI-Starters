# Vendoring third-party packages for evaluation

Place any third-party packages required by your evaluation script into `evaluation_script/vendor/` so the evaluation can run without network access or installing outside the repository.

Options:

- Vendor a package directory:
  - Put the package folder (containing `__init__.py`) under `evaluation_script/vendor/<package_name>/`.
  - Example: `evaluation_script/vendor/zhipuai/__init__.py`

- Vendor a local wheel or tarball:
  - Place the `.whl` or `.tar.gz` file into `evaluation_script/vendor/` and in your CI or build step install it into `vendor/` (offline install). The `__init__.py` will prefer the contents of `vendor/` on `sys.path`.

- Document expected packages:
  - Add `evaluation_script/local_requirements.txt` with one package per line (optionally with versions) so missing packages can be detected and warned about at import time.

Why this approach?

- Keeps all code and dependencies inside the repository.
- Avoids changing the worker or host Python environment.
- Makes evaluations reproducible and network-independent.

How to use:

- Add vendored packages to `evaluation_script/vendor/`.
- (Optional) add package names to `evaluation_script/local_requirements.txt`.
- The updated `evaluation_script/__init__.py` will prepend `vendor/` to `sys.path` automatically.

If you want help vendoring a specific package (for example `zhipuai`), tell me whether you can provide the package source or wheel and I will add it under `evaluation_script/vendor/` for you.
