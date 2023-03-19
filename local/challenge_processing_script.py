import http
import json
import os
import requests
import sys

from config import *
from utils import (
    check_for_errors,
    create_challenge_zip_file,
    get_request_header,
    load_host_configs,
    validate_token,
)

HOST_AUTH_TOKEN = None
CHALLENGE_HOST_TEAM_PK = None
EVALAI_HOST_URL = None
GIHUB_URL = None


if __name__ == "__main__":

    configs = load_host_configs(HOST_CONFIG_FILE_PATH)
    if configs:
        HOST_AUTH_TOKEN = configs[0]
        CHALLENGE_HOST_TEAM_PK = configs[1]
        EVALAI_HOST_URL = configs[2]
        GIHUB_URL = configs[3]
    else:
        sys.exit(1)

    # Creating the challenge zip file and storing in a dict to send to EvalAI
    create_challenge_zip_file(CHALLENGE_ZIP_FILE_PATH,
                              IGNORE_DIRS, IGNORE_FILES)
    zip_file = open(CHALLENGE_ZIP_FILE_PATH, "rb")

    file = {"zip_configuration": zip_file}

    data = {"GITHUB_REPOSITORY": GIHUB_URL}

    headers = get_request_header(HOST_AUTH_TOKEN)

    # Validation step
    url = "{}{}".format(
        EVALAI_HOST_URL,
        CHALLENGE_CONFIG_VALIDATION_URL.format(CHALLENGE_HOST_TEAM_PK),
    )
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
        else:
            print(
                "\nFollowing errors occurred while validating the challenge config: {}".format(
                    err
                )
            )
    except Exception as e:
        error_message = "\nFollowing errors occurred while validating the challenge config: {}".format(
            e
        )
        print(error_message)

    # Creating or updating the challenge
    url = "{}{}".format(
        EVALAI_HOST_URL,
        CHALLENGE_CREATE_OR_UPDATE_URL.format(CHALLENGE_HOST_TEAM_PK),
    )

    zip_file = open(CHALLENGE_ZIP_FILE_PATH, "rb")
    file = {"zip_configuration": zip_file}
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
        error_message = "\nFollowing errors occurred while processing the challenge config: {}".format(
            e
        )
        print(error_message)

    zip_file.close()
    os.remove(zip_file.name)

    is_valid, errors = check_for_errors()
    if not is_valid:
        print("Error: {}".format(errors))
    print("\nExiting the {} script\n".format(
        os.path.basename(__file__)))
