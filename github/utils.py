import json
import os
import sys
import zipfile

from config import *
from github import Github


def check_for_errors():
    """
    Checks if any errors have been recorded so far during this workflow step and returns the error if so
    """
    if os.getenv("CHALLENGE_ERRORS") == "False":
        return True, None
    return False, os.getenv("CHALLENGE_ERRORS")


def check_if_pull_request():
    """
    Returns True if the workflow triggering event is a pull request
    """
    if GITHUB_EVENT_NAME == "pull_request":
        return True
    return False


def check_if_merge_or_commit():
    """
    Returns True if the workflow triggering event is either a merge or a direct commit
    """
    if GITHUB_EVENT_NAME == "push":
        return True
    return False


def add_pull_request_comment(github_auth_token, repo_name, pr_number, comment_body):
    """
    Adds a comment to a pull request
    Arguments:
        github_auth_token {str}: The auth token of the github user
        repo_name {str}: The name of the repository
        pr_number {int}: The Pull request number to add a comment
        comment_body {str}: The body of the comment
    """
    try:
        client = Github(github_auth_token)
        repo = client.get_user().get_repo(repo_name)
        pull = repo.get_pull(pr_number)
        pull.create_issue_comment(comment_body)
    except Exception as e:
        print("There was an error while commenting on the Pull request: {}".format(e))


def create_github_repository_issue(
    github_auth_token, repo_name, issue_title, issue_body
):
    """
    Creates an issue in a given repository
    
    Arguments:
        github_auth_token {str}: The auth token of the github user
        repo_name {str}: The name of the repository
        issue_title {int}: The title of the issue to be created
        issue_body {str}: The body of the issue to be created
    """
    try:
        client = Github(github_auth_token)
        repo = client.get_user().get_repo(repo_name)
        issue = repo.create_issue(issue_title, issue_body)
    except Exception as e:
        print("There was an error while creating an issue: {}".format(e))


def create_challenge_zip_file(challenge_zip_file_path, ignore_dirs, ignore_files):
    """
    Creates the challenge zip file at a given path
    
    Arguments:
        challenge_zip_file_path {str}: The relative path of the created zip file
        ignore_dirs {list}: The list of directories to exclude from the zip file
        ignore_files {list}: The list of files to exclude from the zip file
    """
    working_dir = (
        os.getcwd()
    )  # Special case for github. For local. use os.path.dirname(os.getcwd())

    # Creating evaluation_script.zip file
    eval_script_dir = working_dir + "/evaluation_script"
    eval_script_zip = zipfile.ZipFile(
        "evaluation_script.zip", "w", zipfile.ZIP_DEFLATED
    )
    for root, dirs, files in os.walk(eval_script_dir):
        for file in files:
            file_name = os.path.join(root, file)
            name_in_zip_file = (
                file_name[len(eval_script_dir) + 1 :]
                if file_name.startswith(eval_script_dir)
                else file_name
            )
            eval_script_zip.write(file_name, name_in_zip_file)
    eval_script_zip.close()

    # Creating the challenge_config.zip file
    zipf = zipfile.ZipFile(challenge_zip_file_path, "w", zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(working_dir):
        parents = root.split("/")
        if not set(parents) & set(ignore_dirs):
            for file in files:
                if file not in ignore_files:
                    file_name = os.path.join(root, file)
                    name_in_zip_file = (
                        file_name[len(working_dir) + 1 :]
                        if file_name.startswith(working_dir)
                        else file_name
                    )
                    zipf.write(file_name, name_in_zip_file)
    zipf.close()


def get_request_header(token):
    """
    Returns user auth token formatted in header for sending requests
    
    Arguments:
        token {str}: The user token to gain access to EvalAI
    """
    header = {"Authorization": "Bearer {}".format(token)}
    return header


def load_host_configs(config_path):
    """
    Loads token to be used for sending requests
    
    Arguments:
        config_path {str}: The path of host configs having the user token, team id and the EvalAI host url
    """
    config_path = "{}/{}".format(os.getcwd(), config_path)
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                data = f.read()
            except (OSError, IOError) as e:
                print("\nAn error occured while loading the host configs: {}".format(e))
                sys.exit(1)
        data = json.loads(data)
        host_auth_token = data["token"]
        challenge_host_team_pk = data["team_pk"]
        evalai_host_url = data["evalai_host_url"]
        return [host_auth_token, challenge_host_team_pk, evalai_host_url]
    else:
        error_message = "\nThe host config json file is not present. Please include an auth token, team_pk & evalai_host_url in it: {}".format(
            config_path
        )
        print(error_message)
        os.environ["CHALLENGE_ERRORS"] = error_message
        return False


def validate_token(response):
    """
    Function to check if the authentication token provided by user is valid or not
    
    Arguments:
        response {dict}: The response json dict sent back from EvalAI 
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
