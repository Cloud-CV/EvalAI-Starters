import os


HOST_CONFIG_FILE_PATH = "local/host_config.json"
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
