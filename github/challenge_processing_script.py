import http
import json
import os
import requests
import sys
import argparse
import re
import config
import urllib3
from urllib.parse import urlparse

from config import (
    HOST_CONFIG_FILE_PATH,
    CHALLENGE_CONFIG_VALIDATION_URL,
    CHALLENGE_CREATE_OR_UPDATE_URL,
    EVALAI_ERROR_CODES,
    API_HOST_URL,
    IGNORE_DIRS,
    IGNORE_FILES,
    CHALLENGE_ZIP_FILE_PATH,
    GITHUB_EVENT_NAME,
)
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

GITHUB_CONTEXT = json.loads(os.getenv("GITHUB_CONTEXT", "{}"))
GITHUB_AUTH_TOKEN = os.getenv("GITHUB_AUTH_TOKEN")

# START of the FIX: Explicitly read GITHUB_REPOSITORY from environment variable
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
if not GITHUB_REPOSITORY:
    print("FATAL: GITHUB_REPOSITORY environment variable is not set.")
    print("Please ensure your GitHub Actions workflow sets this variable.")
    sys.exit(1)
print(f"🔍 GITHUB_REPOSITORY from environment: {GITHUB_REPOSITORY}")

VALIDATION_STEP = os.getenv("IS_VALIDATION")
print(f"🔍 VALIDATION_STEP from IS_VALIDATION: {VALIDATION_STEP}")


if not GITHUB_AUTH_TOKEN:
    print(
        "Please add your github access token to the repository secrets with the name AUTH_TOKEN"
    )
    sys.exit(1)

# Clean up the GitHub token (remove any whitespace/newlines)
GITHUB_AUTH_TOKEN = GITHUB_AUTH_TOKEN.strip()
HOST_AUTH_TOKEN = None
CHALLENGE_HOST_TEAM_PK = None
EVALAI_HOST_URL = None

parser = argparse.ArgumentParser(
    description="Validate or create/update challenge on EvalAI"
)
parser.add_argument("branch_name", nargs="?", default=None, help="Name of the git branch whose configuration is being processed")

args = parser.parse_args()

# Determine effective branch name (default to "challenge" if none provided)
branch_name = args.branch_name if args.branch_name else "challenge"

# Enforce branch naming convention: "challenge" or "challenge-YYYY-version"
if not re.match(r"^challenge(-\d{4}-.*)?$", branch_name):
    print("Error: Branch name must be 'challenge' or 'challenge-YYYY-version' (e.g., 'challenge', 'challenge-2024-v1', 'challenge-2025-final').")
    sys.exit(1)

def is_localhost_url(url):
    """
    Check if the provided URL is a localhost URL
    
    Arguments:
        url {str}: The URL to check
    
    Returns:
        bool: True if it's a localhost URL, False otherwise
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
    print("INFO: SSL verification disabled for localhost development server")


def modify_challenge_title_for_versioning(branch_suffix):
    """
    Keep the original challenge title in challenge_config.yaml
    Different branch versions will create separate challenges through repository name modification
    
    Arguments:
        branch_suffix {str}: The branch suffix (e.g., "2025-v1") - not used for title modification
    """
    import yaml
    
    config_file = "challenge_config.yaml"
    
    try:
        # Read the current config
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Get the original title
        original_title = config.get('title', 'Challenge')
        
        print(f"   📝 Keeping original title: {original_title}")
        print(f"   ✅ Challenge versioning handled through repository name modification")
        return None  # No title modification needed
            
    except Exception as e:
        print(f"   ⚠️  Warning: Could not read challenge title: {e}")
        print(f"   ℹ️  Continuing with original title...")
        return None



if __name__ == "__main__":
    
    configs = load_host_configs(HOST_CONFIG_FILE_PATH)
    if configs:
        HOST_AUTH_TOKEN = configs[0]
        CHALLENGE_HOST_TEAM_PK = configs[1]
        EVALAI_HOST_URL = configs[2]
    else:
        sys.exit(1)

    
    # Update the global config path for zip file creation
    # Note: We're not importing config.* anymore, so we need to set this directly
    CHALLENGE_CONFIG_FILE_PATH = "challenge_config.yaml"
    
    # Check if we're using a localhost server and configure accordingly
    is_localhost = is_localhost_url(EVALAI_HOST_URL)
    runner_info = get_runner_info()
    
    print(f"\n🌐 EvalAI Server: {EVALAI_HOST_URL}")
    print(f"🏠 Localhost Mode: {is_localhost}")
    print(f"🤖 Self-hosted Runner: {runner_info['is_self_hosted']}")
    
    if is_localhost:
        configure_requests_for_localhost()
        print(f"INFO: Using localhost server: {EVALAI_HOST_URL}")
        
    # Fetching the url
    if VALIDATION_STEP == "True":
        print(f"\n🔍 VALIDATION MODE: Validating challenge configuration...")
        url = "{}{}".format(
            EVALAI_HOST_URL,
            CHALLENGE_CONFIG_VALIDATION_URL.format(CHALLENGE_HOST_TEAM_PK),
        )
    else:
        print(f"\n🚀 CREATION MODE: Creating/updating challenge...")
        url = "{}{}".format(
            EVALAI_HOST_URL,
            CHALLENGE_CREATE_OR_UPDATE_URL.format(CHALLENGE_HOST_TEAM_PK),
        )

    print(f"📡 API Endpoint: {url}")
    
    headers = get_request_header(HOST_AUTH_TOKEN)

    # Add the branch name (if provided) so that EvalAI can distinguish between multiple
    # versions of the challenge present in the same repository.
    
    # For branches with year-version format (e.g., challenge-2025-v1, challenge-2025-v2), 
    # create separate challenges by modifying the repository identifier
    effective_repo_name = GITHUB_REPOSITORY
    
    if branch_name and branch_name != "challenge":
        # Extract year-version suffix from branch name and append to repo name
        # challenge-2025-v1 -> 2025-v1
        branch_suffix = branch_name.replace("challenge-", "")
        effective_repo_name = f"{GITHUB_REPOSITORY}-{branch_suffix}"
        print(f"🔄 Creating separate challenge for branch: {branch_name}")
        print(f"📋 Effective repository name: {effective_repo_name}")
        
        # Note: Challenge versioning is handled through repository name modification
        # The title remains unchanged to keep it clean
        print(f"📝 Challenge versioning handled through repository name")
        modify_challenge_title_for_versioning(branch_suffix)

    # Creating the challenge zip file and storing in a dict to send to EvalAI
    # IMPORTANT: This must happen AFTER title modification
    print(f"\n📦 Creating challenge configuration package...")
    create_challenge_zip_file(CHALLENGE_ZIP_FILE_PATH, IGNORE_DIRS, IGNORE_FILES)
    zip_file = open(CHALLENGE_ZIP_FILE_PATH, "rb")
    file = {"zip_configuration": zip_file}
    
    data = {"GITHUB_REPOSITORY": effective_repo_name}
    if branch_name:
        data["BRANCH_NAME"] = branch_name

    # Debug output
    print(f"🔍 Challenge identification:")
    print(f"   Original repo: {GITHUB_REPOSITORY}")
    print(f"   Effective repo: {effective_repo_name}")
    print(f"   Branch name: {branch_name}")
    print(f"   Data being sent: {data}")

    # Verify challenge title in the config file
    try:
        import yaml
        with open("challenge_config.yaml", 'r') as f:
            config = yaml.safe_load(f)
        current_title = config.get('title', 'Unknown')
        print(f"   Current challenge title: {current_title}")
    except Exception as e:
        print(f"   ⚠️  Could not read current title: {e}")

    # Configure SSL verification based on whether we're using localhost
    verify_ssl = not is_localhost
    print(f"🔒 SSL Verification: {'Disabled (localhost)' if not verify_ssl else 'Enabled'}")

    try:
        print(f"\n🌐 Sending request to EvalAI server...")
        print(f"📤 Request details:")
        print(f"   URL: {url}")
        print(f"   Data: {data}")
        print(f"   Headers: {headers}")
        
        response = requests.post(url, data=data, headers=headers, files=file, verify=verify_ssl)

        print(f"📥 Response received:")
        print(f"   Status code: {response.status_code}")
        print(f"   Status: {response.status_code == http.HTTPStatus.CREATED and 'CREATED' or response.status_code == http.HTTPStatus.OK and 'UPDATED' or 'OTHER'}")
        
        if response.status_code != http.HTTPStatus.OK and response.status_code != http.HTTPStatus.CREATED:
            print(f"   Response content: {response.text}")
            response.raise_for_status()
        else:
            if response.status_code == http.HTTPStatus.CREATED:
                print("\n✅ NEW Challenge CREATED successfully on EvalAI")
            elif response.status_code == http.HTTPStatus.OK:
                print("\n🔄 Existing Challenge UPDATED successfully on EvalAI")
            
            # Try to parse response for additional info
            try:
                response_data = response.json()
                if 'title' in response_data:
                    print(f"   Challenge title: {response_data['title']}")
                if 'id' in response_data:
                    print(f"   Challenge ID: {response_data['id']}")
            except:
                print("   (Could not parse response JSON)")
            
    except requests.exceptions.ConnectionError as conn_err:
        # Handle connection errors specifically for localhost
        if is_localhost:
            error_message = "\n🚨 LOCALHOST SERVER CONNECTION FAILED\n"
            error_message += f"❌ Could not connect to your localhost EvalAI server at: {EVALAI_HOST_URL}\n"
            error_message += "\n📋 Please check the following:\n"
            error_message += "   1. Is your EvalAI server running?\n"
            error_message += f"   2. Is it accessible at {EVALAI_HOST_URL}?\n"
            error_message += "   3. Check server logs for any startup errors\n"
            
            if runner_info['is_self_hosted']:
                error_message += "\n💡 Self-hosted runner troubleshooting:\n"
                error_message += "   • Verify runner can reach the server: ping/curl test\n"
                error_message += "   • Check network configuration and firewall settings\n"
                error_message += "   • Ensure server is binding to correct interface (0.0.0.0 vs 127.0.0.1)\n"
            else:
                error_message += "\n⚠️  CONFIGURATION ISSUE:\n"
                error_message += "   You're using a GitHub-hosted runner with a localhost URL.\n"
                error_message += "   GitHub-hosted runners cannot access your local machine.\n"
                error_message += "   Please set up a self-hosted runner for localhost development.\n"
                
            error_message += "\n💡 To start your local server, typically run:\n"
            error_message += "   python manage.py runserver 0.0.0.0:8888\n"
            error_message += f"\nOriginal error: {conn_err}"
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
                
            # Fail the job so CI visibly reports the problem
            sys.exit(1)

        elif VALIDATION_STEP == "True" and check_if_pull_request():
            pr_number = GITHUB_CONTEXT.get("event", {}).get("number")
            if not pr_number:
                print("⚠️  Warning: Could not get PR number from GITHUB_CONTEXT")
                print("   Skipping pull request comment creation")
            else:
                add_pull_request_comment(
                    GITHUB_AUTH_TOKEN,
                    os.path.basename(effective_repo_name),
                    pr_number,
                    errors,
                )
        else:
            issue_title = (
                "Following errors occurred while validating the challenge config:"
            )
            repo_name = os.path.basename(effective_repo_name) if effective_repo_name else ""
            create_github_repository_issue(
                GITHUB_AUTH_TOKEN,
                repo_name,
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