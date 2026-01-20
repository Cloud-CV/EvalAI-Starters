import http
import os
import sys
import zipfile
from pathlib import Path

import requests

try:
    import yaml  
except ImportError:
    yaml = None


REPO_ROOT = Path(__file__).resolve().parents[1]


CONFIG_CANDIDATES = [
    REPO_ROOT / "challenge_config.yaml",
    REPO_ROOT / "challenge_config.yml",
]


IGNORE_DIRS = {".git", ".github", ".venv", "__pycache__", "node_modules"}
IGNORE_FILES = {"challenge_config.zip", "evaluation_script.zip"}


def find_config_file() -> Path:
    for p in CONFIG_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError("challenge_config.(yaml|yml) not found at repo root")


def yaml_sanity_check(config_path: Path) -> None:
    if yaml is None:
        raise RuntimeError("PyYAML not installed. CI should install pyyaml before running this script.")
    with config_path.open("r", encoding="utf-8") as f:
        yaml.safe_load(f)


def build_evaluation_script_zip(repo_root: Path) -> None:
    eval_dir = repo_root / "evaluation_script"
    if not eval_dir.exists():
        # Some CI runs may not need it; keep it non-fatal.
        print("INFO: evaluation_script/ not found; continuing.")
        return

    out_zip = repo_root / "evaluation_script.zip"
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in eval_dir.rglob("*"):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(eval_dir))
    print("INFO: Built evaluation_script.zip")


def build_challenge_config_zip(repo_root: Path) -> Path:
    out_zip = repo_root / "challenge_config.zip"
    if out_zip.exists():
        out_zip.unlink()

    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in repo_root.rglob("*"):
            rel = path.relative_to(repo_root)

            if any(part in IGNORE_DIRS for part in rel.parts):
                continue
            if path.name in IGNORE_FILES:
                continue
            if path.is_file():
                zf.write(path, rel)

    return out_zip


def evalai_validate(zip_path: Path) -> bool:
    """
    Uses ONLY the validate API
    If secrets are missing, we skip API validation but keep YAML sanity checks.
    """
    token = (os.getenv("EVALAI_AUTH_TOKEN") or "").strip()
    team_pk = (os.getenv("EVALAI_HOST_TEAM_PK") or "").strip()
    host_url = (os.getenv("EVALAI_HOST_URL") or "https://eval.ai").strip().rstrip("/")

    if not token or not team_pk:
        print("INFO: EVALAI_AUTH_TOKEN / EVALAI_HOST_TEAM_PK not set -> skipping EvalAI API validation.")
        return True

    url = f"{host_url}/api/challenges/challenge/challenge_host_team/{team_pk}/validate_challenge_config/"
    headers = {"Authorization": f"Bearer {token}"}

    with zip_path.open("rb") as f:
        files = {"zip_configuration": f}
        data = {"GITHUB_REPOSITORY": os.getenv("GITHUB_REPOSITORY", "")}
        resp = requests.post(url, headers=headers, files=files, data=data, timeout=120)

    if resp.status_code in (http.HTTPStatus.OK, http.HTTPStatus.CREATED):
        print("✅ EvalAI API validation passed.")
        return True

    # Best-effort error printing
    try:
        payload = resp.json()
    except Exception:
        print(f"❌ EvalAI validation failed: HTTP {resp.status_code}\n{resp.text}")
        return False

    detail = payload.get("detail")
    error = payload.get("error")
    if detail:
        print(f"❌ EvalAI validation failed: {detail}")
    if error:
        print("❌ Following errors occurred while validating the challenge config:\n{}".format(error))
    if not detail and not error:
        print(f"❌ EvalAI validation failed: HTTP {resp.status_code}\n{payload}")

    return False


def main() -> int:
    config_path = find_config_file()

    print(f"INFO: Found config: {config_path.name}")
    yaml_sanity_check(config_path)
    print("✅ YAML syntax check passed.")

    
    build_evaluation_script_zip(REPO_ROOT)
    zip_path = build_challenge_config_zip(REPO_ROOT)
    print(f"INFO: Built challenge zip: {zip_path.name}")

    ok = evalai_validate(zip_path)

    
    for p in [REPO_ROOT / "evaluation_script.zip", REPO_ROOT / "challenge_config.zip"]:
        if p.exists():
            p.unlink()

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
