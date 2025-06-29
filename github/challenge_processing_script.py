import http
import json
import os
import requests
import sys
import time
import urllib3
import socket
import platform
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
)

sys.dont_write_bytecode = True

GITHUB_CONTEXT = json.loads(os.getenv("GITHUB_CONTEXT"))

GITHUB_AUTH_TOKEN = os.getenv("GITHUB_AUTH_TOKEN")
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
        "host.docker.internal",
        "172.17.0.1",
        "192.168."
    ]
    return any(indicator in url.lower() for indicator in localhost_indicators)


def get_runner_info():
    """
    Get information about the current runner environment
    
    Returns:
        dict: Information about the runner
    """
    runner_info = {
        "is_github_actions": bool(os.getenv("GITHUB_ACTIONS")),
        "runner_name": os.getenv("RUNNER_NAME", "unknown"),
        "runner_os": os.getenv("RUNNER_OS", platform.system()),
        "runner_arch": os.getenv("RUNNER_ARCH", platform.machine()),
        "is_self_hosted": os.getenv("RUNNER_ENVIRONMENT") != "github-hosted",
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
    }
    return runner_info


def test_server_connectivity(url, timeout=10):
    """
    Test connectivity to the EvalAI server
    
    Arguments:
        url {str}: The server URL to test
        timeout {int}: Connection timeout in seconds
    
    Returns:
        dict: Test results with status and details
    """
    result = {
        "success": False,
        "details": [],
        "error": None
    }
    
    try:
        parsed_url = urlparse(url)
        host = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
        
        result["details"].append(f"Testing connectivity to {host}:{port}")
        
        # Test socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        socket_result = sock.connect_ex((host, port))
        sock.close()
        
        if socket_result == 0:
            result["details"].append(f"✅ Socket connection successful to {host}:{port}")
            
            # Test HTTP request
            try:
                response = requests.get(url, timeout=timeout, verify=not is_localhost_url(url))
                result["details"].append(f"✅ HTTP request successful (Status: {response.status_code})")
                result["success"] = True
            except requests.exceptions.RequestException as e:
                result["details"].append(f"⚠️  HTTP request failed: {e}")
                result["success"] = False  # Still consider it a partial success since socket worked
                
        else:
            result["details"].append(f"❌ Socket connection failed to {host}:{port}")
            result["success"] = False
            
    except Exception as e:
        result["error"] = str(e)
        result["details"].append(f"❌ Connectivity test failed: {e}")
        result["success"] = False
    
    return result


def configure_requests_for_localhost():
    """
    Configure requests and urllib3 for localhost development servers
    This disables SSL warnings for self-signed certificates commonly used in development
    """
    # Disable SSL warnings for localhost development
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    print("INFO: SSL verification disabled for localhost development server")


def print_environment_info():
    """
    Print detailed information about the current environment
    """
    runner_info = get_runner_info()
    
    print("\n🔍 ENVIRONMENT INFORMATION")
    print("=" * 50)
    print(f"GitHub Actions: {runner_info['is_github_actions']}")
    print(f"Runner Type: {'Self-hosted' if runner_info['is_self_hosted'] else 'GitHub-hosted'}")
    print(f"Runner Name: {runner_info['runner_name']}")
    print(f"Operating System: {runner_info['runner_os']}")
    print(f"Architecture: {runner_info['runner_arch']}")
    print(f"Hostname: {runner_info['hostname']}")
    print(f"Platform: {runner_info['platform']}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Python Version: {sys.version}")
    print("=" * 50)


if __name__ == "__main__":
    
    print_environment_info()

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
    
    print(f"\n🌐 EvalAI Server: {EVALAI_HOST_URL}")
    print(f"🏠 Localhost Mode: {is_localhost}")
    print(f"🤖 Self-hosted Runner: {runner_info['is_self_hosted']}")
    
    if is_localhost:
        configure_requests_for_localhost()
        print(f"INFO: Using localhost server: {EVALAI_HOST_URL}")
        
        # For localhost, perform connectivity test
        print(f"\n🔍 Testing connectivity to localhost server...")
        connectivity_test = test_server_connectivity(EVALAI_HOST_URL)
        
        for detail in connectivity_test["details"]:
            print(f"   {detail}")
            
        if not connectivity_test["success"]:
            error_message = f"\n🚨 LOCALHOST SERVER CONNECTIVITY FAILED\n"
            error_message += f"❌ Cannot reach EvalAI server at: {EVALAI_HOST_URL}\n\n"
            error_message += "📋 Troubleshooting steps:\n"
            error_message += "   1. Ensure your EvalAI server is running\n"
            error_message += "   2. Verify the server is listening on the correct interface and port\n"
            error_message += "   3. Check for firewall or network restrictions\n"
            error_message += "   4. Confirm the URL in host_config.json is correct\n\n"
            
            if runner_info['is_self_hosted']:
                error_message += "💡 Self-hosted runner tips:\n"
                error_message += "   • Make sure the server is accessible from your runner machine\n"
                error_message += "   • Test manually: curl -v " + EVALAI_HOST_URL + "\n"
            else:
                error_message += "⚠️  You're using a GitHub-hosted runner with localhost URL\n"
                error_message += "   This will not work. Please use a self-hosted runner for localhost development.\n"
            
            print(error_message)
            os.environ["CHALLENGE_ERRORS"] = error_message
            
            # Don't exit immediately for localhost connectivity issues in validation mode
            # Let the request attempt provide more specific error information
        else:
            print("✅ Localhost server connectivity test passed!")

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

    # Creating the challenge zip file and storing in a dict to send to EvalAI
    print(f"\n📦 Creating challenge configuration package...")
    create_challenge_zip_file(CHALLENGE_ZIP_FILE_PATH, IGNORE_DIRS, IGNORE_FILES)
    zip_file = open(CHALLENGE_ZIP_FILE_PATH, "rb")
    file = {"zip_configuration": zip_file}

    data = {"GITHUB_REPOSITORY": GITHUB_REPOSITORY or "unknown-repo"}

    # Configure SSL verification based on whether we're using localhost
    verify_ssl = not is_localhost
    print(f"🔒 SSL Verification: {'Disabled (localhost)' if not verify_ssl else 'Enabled'}")

    try:
        print(f"\n🌐 Sending request to EvalAI server...")
        print(f"💡 Adding small delay to avoid rate limiting...")
        time.sleep(1)  # Brief delay to avoid overwhelming the server
        response = requests.post(url, data=data, headers=headers, files=file, verify=verify_ssl)

        if (
            response.status_code != http.HTTPStatus.OK
            and response.status_code != http.HTTPStatus.CREATED
        ):
            response.raise_for_status()
        else:
            success_message = response.json().get("Success", "Operation completed successfully")
            print(f"\n✅ SUCCESS: {success_message}")
            
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
        
    except requests.exceptions.HTTPError as err:
        if response.status_code == 429:
            error_message = f"\n🚨 RATE LIMITED (HTTP 429)\n"
            error_message += f"❌ EvalAI server is limiting request frequency\n"
            error_message += f"💡 This is normal for development servers - they limit requests to prevent overload\n\n"
            error_message += f"🔧 Solutions:\n"
            error_message += f"   • Wait a few minutes and try again\n"
            error_message += f"   • Check if server has rate limiting enabled\n"
            error_message += f"   • Consider increasing server rate limits for development\n"
            error_message += f"\nOriginal error: {err}"
            print(error_message)
            os.environ["CHALLENGE_ERRORS"] = error_message
        elif response.status_code in EVALAI_ERROR_CODES:
            is_token_valid = validate_token(response.json())
            if is_token_valid:
                error = response.json()["error"]
                error_message = f"\nFollowing errors occurred while {'validating' if VALIDATION_STEP == 'True' else 'processing'} the challenge config:\n{error}"
                print(error_message)
                os.environ["CHALLENGE_ERRORS"] = error_message
        else:
            error_message = f"\nHTTP Error occurred while {'validating' if VALIDATION_STEP == 'True' else 'processing'} the challenge config: {err}"
            print(error_message)
            os.environ["CHALLENGE_ERRORS"] = error_message
            
    except Exception as e:
        if VALIDATION_STEP == "True":
            error_message = f"\nFollowing errors occurred while validating the challenge config: {e}"
            print(error_message)
            os.environ["CHALLENGE_ERRORS"] = error_message
        else:
            error_message = f"\nFollowing errors occurred while processing the challenge config: {e}"
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
                
        elif VALIDATION_STEP == "True" and check_if_pull_request():
            pr_number = GITHUB_CONTEXT.get("event", {}).get("number")
            if not pr_number:
                print("⚠️  Warning: Could not get PR number from GITHUB_CONTEXT")
                print("   Skipping pull request comment creation")
            else:
                repo_name = os.path.basename(GITHUB_REPOSITORY) if GITHUB_REPOSITORY else "unknown-repo"
                add_pull_request_comment(
                    GITHUB_AUTH_TOKEN,
                    repo_name,
                    pr_number,
                    errors,
                )
        else:
            issue_title = f"Following errors occurred while {'validating' if VALIDATION_STEP == 'True' else 'processing'} the challenge config:"
            repo_name = os.path.basename(GITHUB_REPOSITORY) if GITHUB_REPOSITORY else "unknown-repo"
            create_github_repository_issue(
                GITHUB_AUTH_TOKEN,
                repo_name,
                issue_title,
                errors,
            )
        
        print(f"\nExiting the {os.path.basename(__file__)} script after failure\n")
        sys.exit(1)

    print(f"\n✅ Exiting the {os.path.basename(__file__)} script after success\n")