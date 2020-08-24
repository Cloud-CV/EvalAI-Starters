import json
import os
import sys
import zipfile


def construct_challenge_zip_file(challenge_zip_file_path, ignore_dirs, ignore_files):
    """
    Constructs the challenge zip file at a given path
    """
    working_dir = os.path.dirname(os.getcwd())
    zipf = zipfile.ZipFile(challenge_zip_file_path, "w", zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(working_dir):
        parents = root.split('/')
        if not set(parents) & set(ignore_dirs):
            for file in files:
                if file not in ignore_files:
                    file_name = os.path.join(root, file)
                    name_in_zip_file = file_name[len(working_dir)+1:] if file_name.startswith(working_dir) else file_name
                    zipf.write(file_name, name_in_zip_file)
    zipf.close()


def get_request_header(token):
    """
    Returns user auth token formatted in header for sending requests
    """
    header = {"Authorization": "Token {}".format(token)}
    return header


def load_host_configs(config_path):
    """
    Loads token to be used for sending requests
    """
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                data = f.read()
            except (OSError, IOError) as e:
                print("\nAn error occured while loading the host configs.")
                print(e)
                sys.exit(1)
        data = json.loads(data)
        host_auth_token = data["token"]
        challenge_host_team_pk = data["team_pk"]
        evalai_host_url = data["evalai_host_url"]
        return [host_auth_token, challenge_host_team_pk, evalai_host_url]
    else:
        print("\nThe host config json file is not present. Please include an auth token, team_pk & evalai_host_url in it: {}".format(config_path))
        os.environ["CHALLENGE_ERRORS"] = error
        return False

def validate_token(response):
    """
    Function to check if the authentication token provided by user is valid or not.
    """
    error = None
    if "detail" in response:
        if response["detail"] == "Invalid token":
            error = "\nThe authentication token you are using isn't valid. Please generate it again.\n"
            print(error)
            os.environ["CHALLENGE_ERRORS"] = error
            return False
        if response["detail"] == "Token has expired":
            error = "\nSorry, the token has expired. Please generate it again.\n"
            print(error)
            os.environ["CHALLENGE_ERRORS"] = error
            return False
    return True