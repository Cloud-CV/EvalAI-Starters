import http
import json
import os
import requests
import sys

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


if __name__ == "__main__":

    configs = load_host_configs(HOST_CONFIG_FILE_PATH)
    if configs:
        HOST_AUTH_TOKEN = configs[0]
        CHALLENGE_HOST_TEAM_PK = configs[1]
        EVALAI_HOST_URL = configs[2]
    else:
        sys.exit(1)

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

    data = {"GITHUB_REPOSITORY": GITHUB_REPOSITORY}

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
