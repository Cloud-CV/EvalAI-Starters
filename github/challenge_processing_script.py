import os
import requests
import sys
import http

from config import *
from utils import (
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

IS_VALIDATION = os.environ.get("IS_VALIDATION")


if __name__ == "__main__":

	print("\nInside the {}".format(os.path.basename(__file__)))

	res = load_host_configs(HOST_CONFIG_FILE_PATH)
	if res:
		HOST_AUTH_TOKEN = res[0]
		CHALLENGE_HOST_TEAM_PK = res[1]
		EVALAI_HOST_URL = res[2]
		print("{} ; {} ; {}".format(HOST_AUTH_TOKEN, CHALLENGE_HOST_TEAM_PK, EVALAI_HOST_URL))
	else:
		sys.exit(1)

	# Fetching the url
	if IS_VALIDATION=="True":
		url = "{}{}".format(EVALAI_HOST_URL, CHALLENGE_CONFIG_VALIDATION_URL.format(CHALLENGE_HOST_TEAM_PK))
	else:
		url = "{}{}".format(EVALAI_HOST_URL, CHALLENGE_CREATE_OR_UPDATE_URL.format(CHALLENGE_HOST_TEAM_PK))
	print()

	headers = get_request_header(HOST_AUTH_TOKEN)
	print("headers is {}".format(headers))
	# Creating the challenge zip file and storing in a dict to send to EvalAI
	construct_challenge_zip_file(CHALLENGE_ZIP_FILE_PATH, IGNORE_DIRS, IGNORE_FILES)
	zip_file = open(CHALLENGE_ZIP_FILE_PATH, 'rb')
	file = {"zip_configuration": zip_file}
	print("file is {}".format(file))
	data = {"GITHUB_REPOSITORY": GITHUB_REPOSITORY} 
	print("data is {}".format(data))

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

	if os.environ.get("CHALLENGE_ERRORS") != "False" and IS_VALIDATION=="True":
		print("\nExiting the {} script after failure\n".format(os.path.basename(__file__)))
		message = os.environ.get("CHALLENGE_ERRORS")
		os.system('echo ::set-env name=TEST_VAR::{}'.format(message))
		sys.exit(1)

	print("\nExiting the {} script after success\n".format(os.path.basename(__file__)))

