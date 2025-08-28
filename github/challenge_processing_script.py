import http
import json
import os
import requests
import sys
import urllib3
from urllib.parse import urlparse

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
    check_sync_status,
    is_localhost_url,
)

sys.dont_write_bytecode = True

# GitHub token from repository secrets (used for GitHub API operations like creating issues, PR comments)
GITHUB_CONTEXT = json.loads(os.getenv("GITHUB_CONTEXT", "{}"))
GITHUB_AUTH_TOKEN = os.getenv("GITHUB_AUTH_TOKEN")  # This comes from AUTH_TOKEN repository secret
if not GITHUB_AUTH_TOKEN:
    print(
        "Please add your github access token to the repository secrets with the name AUTH_TOKEN"
    )
    sys.exit(1)

# Clean up the GitHub token (remove any whitespace/newlines)
GITHUB_AUTH_TOKEN = GITHUB_AUTH_TOKEN.strip()

# EvalAI configuration
HOST_AUTH_TOKEN = None      # EvalAI user authentication token
CHALLENGE_HOST_TEAM_PK = None  # EvalAI team ID
EVALAI_HOST_URL = None      # EvalAI server URL

# Fallback for GITHUB_BRANCH if not imported from config
if 'GITHUB_BRANCH' not in globals():
    GITHUB_BRANCH = os.getenv("GITHUB_REF_NAME") or os.getenv("GITHUB_BRANCH") or os.getenv("GITHUB_REF", "refs/heads/challenge").replace("refs/heads/", "") or "challenge"


def is_localhost_url(url):
    """
    Check if the provided URL is a localhost URL
    """
    localhost_indicators = [
        "127.0.0.1",
        "localhost", 
        "0.0.0.0",
        "host.docker.internal"
    ]
    return any(indicator in url.lower() for indicator in localhost_indicators)


def get_runner_info():
    """Return a minimal dict about the runner (only what we need for error msgs)."""
    return {
        "is_self_hosted": os.getenv("RUNNER_ENVIRONMENT") != "github-hosted",
    }


def configure_requests_for_localhost():
    """
    Configure requests and urllib3 for localhost development servers
    This disables SSL warnings for self-signed certificates commonly used in development
    """
    # Disable SSL warnings for localhost development
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def test_github_access(github_token, repository):
    """
    Tests GitHub repository access to verify token permissions
    """
    try:
        from github import Github
        client = Github(github_token)
        client.get_repo(repository)
        return True
    except Exception:
        return False


def setup_one_way_sync():
    """
    Sets up one-way sync from EvalAI to GitHub
    """
    # Test GitHub repository access
    github_access = test_github_access(GITHUB_AUTH_TOKEN, GITHUB_REPOSITORY)
    
    if github_access:
        return True
    else:
        print(f"❌ GitHub repository access failed! Ensure your token has access to {GITHUB_REPOSITORY}.")
        return False


if __name__ == "__main__":
    if GITHUB_CONTEXT.get("event", {}).get("head_commit", {}).get("message", "").startswith("evalai_bot"):
        print("Sync from Evalai")
        sys.exit(0)

    configs = load_host_configs(HOST_CONFIG_FILE_PATH)
    if configs:
        HOST_AUTH_TOKEN = configs[0]
        CHALLENGE_HOST_TEAM_PK = configs[1]
        EVALAI_HOST_URL = configs[2]
    else:
        sys.exit(1)

    # Check if we're using a localhost server and configure accordingly
    is_localhost = is_localhost_url(EVALAI_HOST_URL)
    runner_info = get_runner_info()
    
    if is_localhost:
        configure_requests_for_localhost()
        
    # Setup one-way sync configuration
    if GITHUB_AUTH_TOKEN:
        setup_one_way_sync()
    else:
        print("ℹ️  One-way sync not configured. Add AUTH_TOKEN to repository secrets.")
        
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

    data = {
        "GITHUB_REPOSITORY": GITHUB_REPOSITORY,
        "GITHUB_AUTH_TOKEN": GITHUB_AUTH_TOKEN,
        "GITHUB_BRANCH" : GITHUB_BRANCH
    }
    
    # Add GitHub token for one-way sync if available
    if GITHUB_AUTH_TOKEN:
        data["GITHUB_TOKEN"] = GITHUB_AUTH_TOKEN

    # Configure SSL verification based on whether we're using localhost
    verify_ssl = not is_localhost

    try:
        response = requests.post(url, data=data, headers=headers, files=file, verify=verify_ssl)

        if response.status_code != http.HTTPStatus.OK and response.status_code != http.HTTPStatus.CREATED:
            response.raise_for_status()
        else:
            print("✅ Challenge processed successfully on EvalAI")
            
            # If this was a challenge creation/update, try to get the challenge ID for sync status
            if VALIDATION_STEP != "True" and GITHUB_AUTH_TOKEN:
                try:
                    response_data = response.json()
                    if "id" in response_data:
                        challenge_id = response_data["id"]
                        sync_status = check_sync_status(EVALAI_HOST_URL, challenge_id, HOST_AUTH_TOKEN)
                        if sync_status:
                            print("✅ Sync status retrieved")
                except Exception:
                    pass
            
    except requests.exceptions.ConnectionError as conn_err:
        # Handle connection errors specifically for localhost
        if is_localhost:
            print("\nℹ️  Localhost connection error detected. Skipping GitHub issue creation.")
            if not runner_info['is_self_hosted']:
                print("   This is expected when using GitHub-hosted runners with localhost URLs.")
                print("   Please configure a self-hosted runner for local development.")
            else:
                print("   This is expected when your local EvalAI server isn't running.")
            sys.exit(1)
        else:
            error_message = f"\nConnection failed to EvalAI server: {conn_err}"
            print(error_message)
            os.environ["CHALLENGE_ERRORS"] = error_message
            # Fail the job so CI visibly reports the problem
            sys.exit(1)

    except requests.exceptions.HTTPError as err:
        if response.status_code in EVALAI_ERROR_CODES:
            is_token_valid = validate_token(response.json())
            if is_token_valid:
                error = response.json().get("error", str(err))
                error_message = "\nErrors occurred while validating the challenge config:\n{}".format(
                    error
                )
                print(error_message)
                os.environ["CHALLENGE_ERRORS"] = error_message
        elif response.status_code == 404:
            error_message = "\n404 Not Found: API endpoint not found"
            print(error_message)
            os.environ["CHALLENGE_ERRORS"] = error_message
        else:
            print(
                "\nErrors occurred while validating the challenge config: {}".format(
                    err
                )
            )
            os.environ["CHALLENGE_ERRORS"] = str(err)

    except Exception as e:
        if VALIDATION_STEP == "True":
            error_message = "\nErrors occurred while validating the challenge config: {}".format(
                e
            )
            print(error_message)
            os.environ["CHALLENGE_ERRORS"] = error_message
        else:
            error_message = "\nErrors occurred while processing the challenge config: {}".format(
                e
            )
            print(error_message)
            os.environ["CHALLENGE_ERRORS"] = error_message

    zip_file.close()
    os.remove(zip_file.name)

    is_valid, errors = check_for_errors()
    if not is_valid:
        # Check if this is a localhost connection error - don't create GitHub issues for expected localhost failures
        is_localhost_connection_error = (
            is_localhost and 
            errors and 
            ("Connection refused" in errors or "LOCALHOST SERVER CONNECTION FAILED" in errors)
        )
        
        # Also check if this is a GitHub-hosted runner trying to access localhost
        is_github_hosted_localhost_error = (
            is_localhost and 
            not runner_info['is_self_hosted'] and
            errors and
            "Connection" in errors
        )
        
        if is_localhost_connection_error or is_github_hosted_localhost_error:
            print("\nℹ️  Localhost connection error detected. Skipping GitHub issue creation.")
            if is_github_hosted_localhost_error:
                print("   This is expected when using GitHub-hosted runners with localhost URLs.")
                print("   Please configure a self-hosted runner for local development.")
            else:
                print("   This is expected when your local EvalAI server isn't running.")
            sys.exit(1)

        elif VALIDATION_STEP == "True" and check_if_pull_request():
            pr_number = GITHUB_CONTEXT.get("event", {}).get("number")
            if not pr_number:
                print("⚠️  Warning: Could not get PR number from GITHUB_CONTEXT")
                print("   Skipping pull request comment creation")
            else:
                add_pull_request_comment(
                    GITHUB_AUTH_TOKEN,
                    os.path.basename(GITHUB_REPOSITORY),
                    pr_number,
                    errors,
                )
        else:
            issue_title = (
                "Errors occurred while validating the challenge config:"
            )
            repo_name = os.path.basename(GITHUB_REPOSITORY) if GITHUB_REPOSITORY else ""
            create_github_repository_issue(
                GITHUB_AUTH_TOKEN,
                repo_name,
                issue_title,
                errors,
            )
            sys.exit(1)

    print("\nExiting the {} script after success\n".format(os.path.basename(__file__)))
