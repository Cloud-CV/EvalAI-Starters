import os


os.environ["CHALLENGE_ERRORS"] = "False"

HOST_CONFIG_FILE_PATH = "github/host_config.json"
CHALLENGE_CONFIG_VALIDATION_URL = "/api/challenges/challenge/challenge_host_team/{}/validate_challenge_config/"
CHALLENGE_CREATE_OR_UPDATE_URL = "/api/challenges/challenge/challenge_host_team/{}/create_or_update_github_challenge/"
EVALAI_ERROR_CODES = [400, 401, 406]
API_HOST_URL = "https://eval.ai"
IGNORE_DIRS = [
    ".git",
    ".github",
    "github",
    "code_upload_challenge_evaluation",
    "remote_challenge_evaluation",
]
IGNORE_FILES = [
    ".gitignore",
    "challenge_config.zip",
    "README.md",
    "run.sh",
    "submission.json",
]
CHALLENGE_ZIP_FILE_PATH = "challenge_config.zip"
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
GITHUB_EVENT_NAME = os.getenv("GITHUB_EVENT_NAME")
VALIDATION_STEP = os.getenv("IS_VALIDATION")
