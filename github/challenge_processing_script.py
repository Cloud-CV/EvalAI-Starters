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
    GITHUB_BRANCH = os.getenv("GITHUB_REF_NAME") or os.getenv("GITHUB_BRANCH") or os.getenv("GITHUB_REF", "refs/heads/main").replace("refs/heads/", "") or "main"


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


def test_github_access(github_token, repository):
    """
    Tests GitHub repository access to verify token permissions
    """
    print(f"\n🔍 Testing GitHub repository access...")
    print(f"   Repository: {repository}")
    print(f"   Token: {github_token[:8]}...{github_token[-4:] if len(github_token) > 12 else '***'}")
    
    try:
        from github import Github
        client = Github(github_token)
        
        # Try to get the repository
        repo = client.get_repo(repository)
        print(f"   ✅ Repository accessible: {repo.full_name}")
        print(f"   📁 Default branch: {repo.default_branch}")
        print(f"   🔒 Private: {repo.private}")
        
        # Check permissions
        user = client.get_user()
        print(f"   👤 Authenticated as: {user.login}")
        
        # Try to get repository contents
        try:
            contents = repo.get_contents("")
            print(f"   📄 Repository contents accessible")
        except Exception as e:
            print(f"   ⚠️  Cannot read repository contents: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ GitHub access failed: {e}")
        if "Bad credentials" in str(e):
            print(f"   💡 Token is invalid or expired")
        elif "Not Found" in str(e):
            print(f"   💡 Repository not found or token doesn't have access")
        elif "Bad credentials" in str(e):
            print(f"   💡 Token doesn't have sufficient permissions")
        return False


def test_basic_connectivity(evalai_host_url):
    """
    Tests basic connectivity to the EvalAI server
    """
    print(f"\n🔍 Testing basic connectivity to EvalAI server...")
    print(f"   URL: {evalai_host_url}")
    
    # Check if this is a Docker environment
    if "host.docker.internal" in evalai_host_url:
        print(f"   🐳 Docker environment detected (host.docker.internal)")
        print(f"   💡 This means you're running from inside a Docker container")
        print(f"   💡 host.docker.internal should resolve to the host machine")
    
    try:
        # Try to access the root or admin endpoint
        response = requests.get(
            f"{evalai_host_url}/",
            verify=not is_localhost_url(evalai_host_url),
            timeout=10
        )
        print(f"   ✅ Root endpoint accessible (Status: {response.status_code})")
        return True
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection failed - server not reachable")
        if "host.docker.internal" in evalai_host_url:
            print(f"   🐳 Docker troubleshooting:")
            print(f"      • Ensure EvalAI server is running on host machine")
            print(f"      • Check if server is binding to 0.0.0.0:8000 (not just 127.0.0.1)")
            print(f"      • Verify Docker can reach host.docker.internal")
            print(f"      • Try using host machine's IP address instead")
        return False
    except Exception as e:
        print(f"   ⚠️  Unexpected error: {e}")
        return False


def test_api_endpoints(evalai_host_url, team_pk, host_auth_token):
    """
    Tests different API endpoint patterns to find the correct one
    """
    print(f"\n🧪 Testing API endpoint patterns...")
    print(f"   Team PK: {team_pk}")
    print(f"   EvalAI Host: {evalai_host_url}")
    
    # Different endpoint patterns to test
    endpoint_patterns = [
        f"/api/v1/challenges/challenge_host_team/{team_pk}/validate_challenge_config/",
        f"/api/challenges/challenge_host_team/{team_pk}/validate_challenge_config/",
        f"/api/v1/challenges/{team_pk}/validate_challenge_config/",
        f"/api/challenges/{team_pk}/validate_challenge_config/",
        f"/api/v1/challenges/challenge/challenge_host_team/{team_pk}/validate_challenge_config/",
        f"/api/challenges/challenge/challenge_host_team/{team_pk}/validate_challenge_config/",
        # Additional patterns that might work
        f"/api/v1/challenges/validate_challenge_config/",
        f"/api/challenges/validate_challenge_config/",
        f"/api/v1/challenge_host_team/{team_pk}/validate_challenge_config/",
        f"/api/challenge_host_team/{team_pk}/validate_challenge_config/",
        f"/api/v1/challenges/{team_pk}/validate/",
        f"/api/challenges/{team_pk}/validate/",
    ]
    
    results = {}
    headers = get_request_header(host_auth_token)
    
    for pattern in endpoint_patterns:
        test_url = f"{evalai_host_url}{pattern}"
        print(f"\n   Testing: {pattern}")
        
        try:
            # Send a simple GET request to test the endpoint
            response = requests.get(
                test_url, 
                headers=headers, 
                verify=not is_localhost_url(evalai_host_url),
                timeout=10
            )
            
            status = response.status_code
            results[pattern] = {
                "status": status,
                "url": test_url,
                "accessible": status != 404
            }
            
            if status == 404:
                print(f"     ❌ 404 Not Found")
            elif status == 401:
                print(f"     🔒 401 Unauthorized (endpoint exists but auth failed)")
            elif status == 403:
                print(f"     🚫 403 Forbidden (endpoint exists but access denied)")
            elif status == 200:
                print(f"     ✅ 200 OK (endpoint accessible)")
            else:
                print(f"     ⚠️  {status} (endpoint exists, status: {status})")
                
        except requests.exceptions.ConnectionError:
            print(f"     ❌ Connection Error")
            results[pattern] = {"status": "Connection Error", "url": test_url, "accessible": False}
        except Exception as e:
            print(f"     ❌ Error: {e}")
            results[pattern] = {"status": f"Error: {e}", "url": test_url, "accessible": False}
    
    # Find the best endpoint
    working_endpoints = [p for p, r in results.items() if r.get("accessible", False)]
    
    if working_endpoints:
        print(f"\n✅ Found working endpoints:")
        for endpoint in working_endpoints:
            print(f"   • {endpoint}")
        print(f"\n💡 Update your config.py with one of these working patterns")
    else:
        print(f"\n❌ No working endpoints found")
        print(f"   Check your team_pk and EvalAI server configuration")
    
    return results


def setup_one_way_sync():
    """
    Sets up one-way sync from EvalAI to GitHub
    """
    print(f"\n🔄 Setting up one-way sync (EvalAI → GitHub)...")
    print(f"   Repository: {GITHUB_REPOSITORY}")
    print(f"   EvalAI Server: {EVALAI_HOST_URL}")
    print(f"   Using GitHub token: {GITHUB_AUTH_TOKEN[:8]}...{GITHUB_AUTH_TOKEN[-4:] if len(GITHUB_AUTH_TOKEN) > 12 else '***'}")
    
    # Test GitHub repository access
    github_access = test_github_access(GITHUB_AUTH_TOKEN, GITHUB_REPOSITORY)
    
    if github_access:
        print(f"✅ GitHub repository access verified!")
        print(f"   EvalAI changes will automatically sync to GitHub")
        print(f"   GitHub changes will NOT sync back to EvalAI (by design)")
        print("\n💡 How it works:")
        print("   1. Make changes in EvalAI UI")
        print("   2. Changes are saved to database")
        print("   3. Django signal automatically triggers GitHub sync")
        print("   4. GitHub repository is updated with latest changes")
        print("   5. User gets immediate feedback (no waiting)")
        
        print(f"\n⚠️  IMPORTANT: Ensure your EvalAI challenge has these fields configured:")
        print(f"   • github_repository: '{GITHUB_REPOSITORY}'")
        print(f"   • github_branch: '{GITHUB_BRANCH}' (actual repository default branch)")
        print(f"   • github_token: [your GitHub personal access token]")
        print(f"\n💡 These must be set in the EvalAI challenge settings for sync to work")
        print(f"💡 Note: Your repository uses '{GITHUB_BRANCH}' branch, not 'main'")
        print(f"\n🔧 Backend uses Django signals for automatic sync (no Celery needed)")
        print(f"   • challenge_details_sync signal for challenge updates")
        print(f"   • challenge_phase_details_sync signal for phase updates")
        
        return True
    else:
        print(f"❌ GitHub repository access failed!")
        print(f"   EvalAI → GitHub sync will not work until this is resolved")
        print(f"   Check your GitHub token permissions and repository access")
        return False


if __name__ == "__main__":
    if GITHUB_CONTEXT["event"]["head_commit"]["message"].startswith("evalai_bot"):
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
    
    print(f"\n🌐 EvalAI Server: {EVALAI_HOST_URL}")
    print(f"🏠 Localhost Mode: {is_localhost}")
    print(f"🤖 Self-hosted Runner: {runner_info['is_self_hosted']}")
    print(f"🔄 Sync Mode: One-way (EvalAI → GitHub)")
    
    if GITHUB_AUTH_TOKEN:
        print(f"   GitHub Token: {GITHUB_AUTH_TOKEN[:8]}...{GITHUB_AUTH_TOKEN[-4:] if len(GITHUB_AUTH_TOKEN) > 12 else '***'}")
        print(f"   Token Source: AUTH_TOKEN repository secret")
    else:
        print(f"   GitHub Token: Not provided")
        print(f"   To enable: Add AUTH_TOKEN to repository secrets")
    
    if is_localhost:
        configure_requests_for_localhost()
        print(f"INFO: Using localhost server: {EVALAI_HOST_URL}")
        
    # Setup one-way sync configuration
    if GITHUB_AUTH_TOKEN:
        setup_one_way_sync()
    else:
        print("ℹ️  One-way sync not configured")
        print("   Add AUTH_TOKEN to repository secrets to enable automatic GitHub sync")
        
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
    print(f"🔒 SSL Verification: {'Disabled (localhost)' if not verify_ssl else 'Enabled'}")

    try:
        print(f"\n🌐 Sending request to EvalAI server...")
        response = requests.post(url, data=data, headers=headers, files=file, verify=verify_ssl)

        if response.status_code != http.HTTPStatus.OK and response.status_code != http.HTTPStatus.CREATED:
            response.raise_for_status()
        else:
            print("\n✅ Challenge processed successfully on EvalAI")
            
            # If this was a challenge creation/update, try to get the challenge ID for sync status
            if VALIDATION_STEP != "True" and GITHUB_AUTH_TOKEN:
                try:
                    response_data = response.json()
                    if "id" in response_data:
                        challenge_id = response_data["id"]
                        print(f"\n🔄 Checking sync status for challenge {challenge_id}...")
                        sync_status = check_sync_status(EVALAI_HOST_URL, challenge_id, HOST_AUTH_TOKEN)
                        if sync_status:
                            print(f"✅ Sync status retrieved: {sync_status}")
                        
                        # Additional debugging for sync issues
                        print(f"\n🔍 Sync Debugging Information:")
                        print(f"   Challenge ID: {challenge_id}")
                        print(f"   GitHub Token: {GITHUB_AUTH_TOKEN[:8]}...{GITHUB_AUTH_TOKEN[-4:] if len(GITHUB_AUTH_TOKEN) > 12 else '***'}")
                        print(f"   Repository: {GITHUB_REPOSITORY}")
                        print(f"   Branch: {GITHUB_BRANCH}")
                        
                        # Check if challenge has GitHub fields configured
                        print(f"\n📋 To enable EvalAI → GitHub sync, ensure your challenge has:")
                        print(f"   • github_repository: '{GITHUB_REPOSITORY}'")
                        print(f"   • github_branch: '{GITHUB_BRANCH}'")
                        print(f"   • github_token: [your GitHub personal access token]")
                        print(f"\n💡 Check these in your EvalAI challenge settings")
                        
                        print(f"\n🔧 Django Signal Sync Architecture:")
                        print(f"   • challenge_details_sync signal triggers on Challenge updates")
                        print(f"   • challenge_phase_details_sync signal triggers on Phase updates")
                        print(f"   • No Celery/background tasks needed")
                        print(f"   • Sync happens immediately in same request")
                        
                        print(f"\n🐛 If sync isn't working, check:")
                        print(f"   • EvalAI logs for signal execution")
                        print(f"   • Signal handlers are properly registered")
                        print(f"   • GitHub fields are saved in challenge model")
                        print(f"   • No errors in github_utils.py functions")
                        
                except Exception as e:
                    print(f"ℹ️  Could not retrieve sync status: {e}")
            
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
        elif response.status_code == 404:
            print(f"\n❌ 404 Not Found Error")
            print(f"   The API endpoint was not found: {url}")
            print(f"   This usually means the URL structure has changed in the backend.")
            print(f"\n🔍 Debugging Information:")
            print(f"   Team PK: {CHALLENGE_HOST_TEAM_PK}")
            print(f"   EvalAI Host: {EVALAI_HOST_URL}")
            print(f"   Full URL: {url}")
            print(f"\n💡 Possible Solutions:")
            print(f"   1. Check if the team_pk ({CHALLENGE_HOST_TEAM_PK}) is correct")
            print(f"   2. Verify the EvalAI server is running and accessible")
            print(f"   3. Check if the API endpoint structure has changed")
            print(f"   4. Try accessing the EvalAI admin interface to verify team ID")
            
            # First test basic connectivity
            print(f"\n🔍 Testing basic server connectivity...")
            if test_basic_connectivity(EVALAI_HOST_URL):
                print(f"   ✅ Server is reachable, testing API endpoints...")
                
                # Automatically test different endpoint patterns
                print(f"\n🧪 Automatically testing different endpoint patterns...")
                endpoint_results = test_api_endpoints(EVALAI_HOST_URL, CHALLENGE_HOST_TEAM_PK, HOST_AUTH_TOKEN)
                
                if any(r.get("accessible", False) for r in endpoint_results.values()):
                    print(f"\n✅ Found working endpoints! Retrying with working pattern...")
                    working_endpoints = [p for p, r in endpoint_results.items() if r.get("accessible", False)]
                    
                    # Try the first working endpoint
                    working_endpoint = working_endpoints[0]
                    print(f"   🚀 Retrying with: {working_endpoint}")
                    
                    # Update the URL and retry the request
                    new_url = f"{EVALAI_HOST_URL}{working_endpoint}"
                    print(f"   📡 New API Endpoint: {new_url}")
                    
                    try:
                        print(f"\n🔄 Retrying request with working endpoint...")
                        response = requests.post(new_url, data=data, headers=headers, files=file, verify=verify_ssl)
                        
                        if response.status_code in [200, 201, 202]:
                            print("\n✅ Challenge processed successfully on EvalAI with working endpoint!")
                            
                            # If this was a challenge creation/update, try to get the challenge ID for sync status
                            if VALIDATION_STEP != "True" and GITHUB_AUTH_TOKEN:
                                try:
                                    response_data = response.json()
                                    if "id" in response_data:
                                        challenge_id = response_data["id"]
                                        print(f"\n🔄 Checking sync status for challenge {challenge_id}...")
                                        sync_status = check_sync_status(EVALAI_HOST_URL, challenge_id, HOST_AUTH_TOKEN)
                                        if sync_status:
                                            print(f"✅ Sync status retrieved: {sync_status}")
                                except Exception as e:
                                    print(f"ℹ️  Could not retrieve sync status: {e}")
                            
                            # Success - clear errors and continue
                            os.environ["CHALLENGE_ERRORS"] = "False"
                            print(f"\n🎉 Successfully processed challenge with working endpoint!")
                            print(f"💡 Update your config.py with this working pattern:")
                            print(f"   CHALLENGE_CONFIG_VALIDATION_URL = \"{working_endpoint}\"")
                            print(f"   CHALLENGE_CREATE_OR_UPDATE_URL = \"{working_endpoint.replace('validate_challenge_config', 'create_or_update_github_challenge')}\"")
                            
                            # Continue with success flow
                            zip_file.close()
                            os.remove(zip_file.name)
                            print("\nExiting the {} script after success\n".format(os.path.basename(__file__)))
                            sys.exit(0)
                            
                        else:
                            print(f"\n❌ Retry failed with status: {response.status_code}")
                            print(f"   Response: {response.text}")
                            
                    except Exception as retry_err:
                        print(f"\n❌ Retry failed with error: {retry_err}")
                    
                    print(f"\n💡 Update your config.py with this working pattern:")
                    print(f"   CHALLENGE_CONFIG_VALIDATION_URL = \"{working_endpoint}\"")
                    print(f"   CHALLENGE_CREATE_OR_UPDATE_URL = \"{working_endpoint.replace('validate_challenge_config', 'create_or_update_github_challenge')}\"")
                    
                else:
                    print(f"\n❌ No working endpoints found. Please check:")
                    print(f"   • Team PK is correct: {CHALLENGE_HOST_TEAM_PK}")
                    print(f"   • EvalAI server is running at: {EVALAI_HOST_URL}")
                    print(f"   • Your authentication token is valid")
            else:
                print(f"   ❌ Server is not reachable. Please check:")
                print(f"   • EvalAI server is running")
                print(f"   • URL is correct: {EVALAI_HOST_URL}")
                print(f"   • Network connectivity")
                
                # Docker-specific suggestions
                if "host.docker.internal" in EVALAI_HOST_URL:
                    print(f"\n🐳 Docker-specific suggestions:")
                    print(f"   • Try using host machine's actual IP address instead of host.docker.internal")
                    print(f"   • Ensure EvalAI server is binding to 0.0.0.0:8000, not 127.0.0.1:8000")
                    print(f"   • Check if host.docker.internal resolves correctly in your Docker environment")
                    print(f"   • Alternative URLs to try:")
                    print(f"     - http://172.17.0.1:8000 (Docker bridge network gateway)")
                    print(f"     - http://host.docker.internal:8000 (current)")
                    print(f"     - http://localhost:8000 (if running from host)")
                    print(f"     - http://<your-host-ip>:8000 (your actual host IP)")
            
            error_message = f"\n404 Not Found: API endpoint not found at {url}"
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
                    os.path.basename(GITHUB_REPOSITORY),
                    pr_number,
                    errors,
                )
        else:
            issue_title = (
                "Following errors occurred while validating the challenge config:"
            )
            repo_name = os.path.basename(GITHUB_REPOSITORY) if GITHUB_REPOSITORY else ""
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
