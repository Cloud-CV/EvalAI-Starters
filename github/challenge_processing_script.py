import http
import json
import os
import requests
import sys
import argparse
import re

from config import *
from utils import (
    add_pull_request_comment,
    check_for_errors,
    check_if_merge_or_commit,
    check_if_pull_request,
    create_challenge_zip_file,
    create_github_repository_issue,
    get_request_header,
    load_host_configs,
    validate_token,
)

sys.dont_write_bytecode = True

GITHUB_CONTEXT = json.loads(os.getenv("GITHUB_CONTEXT"))

GITHUB_AUTH_TOKEN = os.getenv("GITHUB_AUTH_TOKEN")
if not GITHUB_AUTH_TOKEN:
    print(
        "Please add your github access token to the repository secrets with the name AUTH_TOKEN"
    )
    sys.exit(1)

HOST_AUTH_TOKEN = None
CHALLENGE_HOST_TEAM_PK = None
EVALAI_HOST_URL = None

parser = argparse.ArgumentParser(
    description="Validate or create/update challenge on EvalAI"
)
parser.add_argument("branch_name", nargs="?", default=None, help="Name of the git branch whose configuration is being processed")

args = parser.parse_args()

# Enforce branch naming convention
if args.branch_name and not re.match(r"^challenge(-.*)?$", args.branch_name):
    print("Error: Branch name must start with 'challenge' (e.g., 'challenge', 'challenge-2024').")
    sys.exit(1)
def get_challenge_config_path(branch_name):
    """
    Get the appropriate challenge config file path based on branch name
    """
    if not branch_name or branch_name == "challenge":
        return "challenge_config.yaml"
    
    # For branches like challenge-2024, challenge-v2, etc.
    if branch_name.startswith("challenge-"):
        suffix = branch_name.replace("challenge-", "")
        branch_config = f"challenge_config_{suffix}.yaml"
        
        # Check if branch-specific config exists
        if os.path.exists(branch_config):
            return branch_config
    
    # Fallback to default config
    return "challenge_config.yaml"

if __name__ == "__main__":

    configs = load_host_configs(HOST_CONFIG_FILE_PATH)
    if configs:
        HOST_AUTH_TOKEN = configs[0]
        CHALLENGE_HOST_TEAM_PK = configs[1]
        EVALAI_HOST_URL = configs[2]
    else:
        sys.exit(1)

    # Get the appropriate challenge config based on branch
    challenge_config_path = get_challenge_config_path(args.branch_name)
    
    # Update the global config path for zip file creation
    import config
    config.CHALLENGE_CONFIG_FILE_PATH = challenge_config_path

    # Fetching the url
    if VALIDATION_STEP == "True":
        url = "{}{}".format(
            EVALAI_HOST_URL,
            CHALLENGE_CONFIG_VALIDATION_URL.format(CHALLENGE_HOST_TEAM_PK),
        )
    else:
        url = "{}{}".format(
            EVALAI_HOST_URL,
            CHALLENGE_CREATE_OR_UPDATE_URL.format(CHALLENGE_HOST_TEAM_PK),
        )

    headers = get_request_header(HOST_AUTH_TOKEN)

    # Creating the challenge zip file and storing in a dict to send to EvalAI
    create_challenge_zip_file(CHALLENGE_ZIP_FILE_PATH, IGNORE_DIRS, IGNORE_FILES)
    zip_file = open(CHALLENGE_ZIP_FILE_PATH, "rb")
    file = {"zip_configuration": zip_file}

    # Add the branch name (if provided) so that EvalAI can distinguish between multiple
    # versions of the challenge present in the same repository.
    data = {"GITHUB_REPOSITORY": GITHUB_REPOSITORY}
    if args.branch_name:
        data["BRANCH_NAME"] = args.branch_name

    try:
        response = requests.post(url, data=data, headers=headers, files=file)

        if (
            response.status_code != http.HTTPStatus.OK
            and response.status_code != http.HTTPStatus.CREATED
        ):
            response.raise_for_status()
        else:
            print("\n" + response.json()["Success"])
    except requests.exceptions.HTTPError as err:
        if response.status_code in EVALAI_ERROR_CODES:
            is_token_valid = validate_token(response.json())
            if is_token_valid:
                error = response.json()["error"]
                error_message = "\nFollowing errors occurred while validating the challenge config:\n{}".format(
                    error
                )
                print(error_message)
                os.environ["CHALLENGE_ERRORS"] = error_message
        else:
            print(
                "\nFollowing errors occurred while validating the challenge config: {}".format(
                    err
                )
            )
            os.environ["CHALLENGE_ERRORS"] = str(err)
    except Exception as e:
        if VALIDATION_STEP == "True":
            error_message = "\nFollowing errors occurred while validating the challenge config: {}".format(
                e
            )
            print(error_message)
            os.environ["CHALLENGE_ERRORS"] = error_message
        else:
            error_message = "\nFollowing errors occurred while processing the challenge config: {}".format(
                e
            )
            print(error_message)
            os.environ["CHALLENGE_ERRORS"] = error_message

    zip_file.close()
    os.remove(zip_file.name)

    is_valid, errors = check_for_errors()
    if not is_valid:
        if VALIDATION_STEP == "True" and check_if_pull_request():
            pr_number = GITHUB_CONTEXT["event"]["number"]
            add_pull_request_comment(
                GITHUB_AUTH_TOKEN,
                os.path.basename(GITHUB_REPOSITORY),
                pr_number,
                errors,
            )
            print(
                "\nExiting the {} script after failure\n".format(
                    os.path.basename(__file__)
                )
            )
            sys.exit(1)
        else:
            issue_title = (
                "Following errors occurred while validating the challenge config:"
            )
            create_github_repository_issue(
                GITHUB_AUTH_TOKEN,
                os.path.basename(GITHUB_REPOSITORY),
                issue_title,
                errors,
            )
            print(
                "\nExiting the {} script after failure\n".format(
                    os.path.basename(__file__)
                )
            )
            sys.exit(1)

    print("\nExiting the {} script after success\n".format(os.path.basename(__file__)))
