import http
import json
import octokit
import os
import requests
import sys

from config import *
from utils import (
	create_issue_in_repo,
	comment_on_pr,
	construct_challenge_zip_file,
	get_request_header,
	load_host_configs,
	validate_token,
)

sys.dont_write_bytecode = True

HOST_AUTH_TOKEN = None
CHALLENGE_HOST_TEAM_PK = None
EVALAI_HOST_URL = None

os.environ["CHALLENGE_ERRORS"] = "False"

IS_VALIDATION = os.getenv("IS_VALIDATION")
GITHUB_EVENT_NAME = os.getenv("GITHUB_EVENT_NAME")

GITHUB_CONTEXT = json.loads(os.getenv("GITHUB_CONTEXT"))
GITHUB_AUTH_TOKEN = "72718f6f7ff21bceb45dec431b0086100128197f" # os.getenv("GITHUB_AUTH_TOKEN")

if GITHUB_EVENT_NAME.startswith("pull_request"):
	PR_NUMBER = GITHUB_CONTEXT["event"]["number"]

if __name__ == "__main__":

	if IS_VALIDATION == "False" and GITHUB_EVENT_NAME.startswith("pull_request"):
		sys.exit(0)

	res = load_host_configs(HOST_CONFIG_FILE_PATH)
	if res:
		HOST_AUTH_TOKEN = res[0]
		CHALLENGE_HOST_TEAM_PK = res[1]
		EVALAI_HOST_URL = res[2]
		print("{} ; {} ; {}".format(HOST_AUTH_TOKEN, CHALLENGE_HOST_TEAM_PK, EVALAI_HOST_URL))
	else:
		sys.exit(1)

	# Fetching the url
	if IS_VALIDATION == "True":
		url = "{}{}".format(EVALAI_HOST_URL, CHALLENGE_CONFIG_VALIDATION_URL.format(CHALLENGE_HOST_TEAM_PK))
	if IS_VALIDATION == "False" and GITHUB_EVENT_NAME == "push":
		url = "{}{}".format(EVALAI_HOST_URL, CHALLENGE_CREATE_OR_UPDATE_URL.format(CHALLENGE_HOST_TEAM_PK))

	headers = get_request_header(HOST_AUTH_TOKEN)

	# Creating the challenge zip file and storing in a dict to send to EvalAI
	construct_challenge_zip_file(CHALLENGE_ZIP_FILE_PATH, IGNORE_DIRS, IGNORE_FILES)
	zip_file = open(CHALLENGE_ZIP_FILE_PATH, 'rb')
	file = {"zip_configuration": zip_file}

	data = {"GITHUB_REPOSITORY": GITHUB_REPOSITORY} 

	try:
		response = requests.post(url, data=data, headers=headers, files=file)

		if response.status_code != http.HTTPStatus.OK and response.status_code != http.HTTPStatus.CREATED:
			response.raise_for_status()
		else:
			print("\n"+response.json()["Success"])
	except requests.exceptions.HTTPError as err:
		if response.status_code in EVALAI_ERROR_CODES:
			is_token_valid = validate_token(response.json())
			if is_token_valid:
				error = response.json()["error"]
				error_message = "\nThere was were some errors in the challenge config:\n{}".format(error)
				print(error_message)
				os.environ["CHALLENGE_ERRORS"] = error_message
		else:
			print("\nThere was an error: {}".format(err))
			os.environ["CHALLENGE_ERRORS"] = str(err)
	except Exception as e:
		if IS_VALIDATION=="True":
			error_message = "\nThere was an error when validating the challenge config: {}".format(e)
			print(error_message)
			os.environ["CHALLENGE_ERRORS"] = error_message
		else:
			error_message = "\nThere was an error: {}".format(e)
			print(error_message)
			os.environ["CHALLENGE_ERRORS"] = error_message

	zip_file.close()
	os.remove(zip_file.name)

	if os.environ.get("CHALLENGE_ERRORS") != "False" and IS_VALIDATION=="True" and GITHUB_EVENT_NAME.startswith("pull_request"):
		message = os.environ.get("CHALLENGE_ERRORS")
		comment_on_pr(GITHUB_AUTH_TOKEN, os.path.basename(GITHUB_REPOSITORY), PR_NUMBER, message)
		print("\nExiting the {} script after failure\n".format(os.path.basename(__file__)))
		sys.exit(1)
	elif os.environ.get("CHALLENGE_ERRORS") != "False" and GITHUB_EVENT_NAME == "push":
		issue_title = "Errors are found in your repository after commit."
		issue_body = os.environ.get("CHALLENGE_ERRORS")
		create_issue_in_repo(GITHUB_AUTH_TOKEN, os.path.basename(GITHUB_REPOSITORY), issue_title, issue_body)
		print("\nExiting the {} script after failure\n".format(os.path.basename(__file__)))
		sys.exit(1)

	print("\nExiting the {} script after success\n".format(os.path.basename(__file__)))

