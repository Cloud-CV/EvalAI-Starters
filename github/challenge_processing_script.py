import http
import json
import os
import requests
import sys

from config import *
from utils import (
    add_pull_request_comment,
    check_for_errors,
    check_if_pull_request,
    create_challenge_zip_file,
    create_github_repository_issue,
    get_request_header,
    load_host_configs,
    validate_token,
)

sys.dont_write_bytecode = True

def validate_environment():
    """Validate required environment variables"""
    required_vars = {
        'GITHUB_AUTH_TOKEN': lambda v: len(v) > 20,
        'EVALAI_HOST_URL': lambda v: v.startswith(('http://', 'https://')),
        'CHALLENGE_HOST_TEAM_PK': lambda v: v.isdigit(),
    }
    
    for var, validator in required_vars.items():
        value = os.getenv(var)
        if not value or not validator(value):
            print(f"::error::Invalid {var}: {value}")
            sys.exit(1)

if __name__ == "__main__":
    try:
        # Validate environment variables first
        validate_environment()
        
        # Load GitHub context
        github_context = json.loads(os.getenv("GITHUB_CONTEXT", "{}"))
        
        # Load EvalAI configurations
        configs = load_host_configs(HOST_CONFIG_FILE_PATH)
        if not configs:
            print("::error::Missing EvalAI host configurations")
            sys.exit(1)

        HOST_AUTH_TOKEN, CHALLENGE_HOST_TEAM_PK, EVALAI_HOST_URL = configs

        # Construct API URL with validation
        base_url = EVALAI_HOST_URL.rstrip('/')
        if VALIDATION_STEP == "True":
            endpoint = CHALLENGE_CONFIG_VALIDATION_URL.format(CHALLENGE_HOST_TEAM_PK)
        else:
            endpoint = CHALLENGE_CREATE_OR_UPDATE_URL.format(CHALLENGE_HOST_TEAM_PK)
        
        url = f"{base_url}/{endpoint.lstrip('/')}"
        print(f"🔧 Using API endpoint: {url}")

        # Create challenge package
        zip_path = create_challenge_zip_file(CHALLENGE_ZIP_FILE_PATH, IGNORE_DIRS, IGNORE_FILES)
        
        # Send to EvalAI
        with open(zip_path, 'rb') as zip_file:
            response = requests.post(
                url,
                headers=get_request_header(HOST_AUTH_TOKEN),
                files={'zip_configuration': zip_file},
                data={'GITHUB_REPOSITORY': os.getenv("GITHUB_REPOSITORY")},
                timeout=30
            )
            response.raise_for_status()
            print(f"✅ Success: {response.json().get('Success', '')}")

    except requests.exceptions.RequestException as e:
        error_msg = f"API Request failed: {str(e)}"
        if hasattr(e, 'response') and e.response.text:
            error_msg += f"\nResponse: {e.response.text[:500]}"
        print(f"::error::{error_msg}")
        sys.exit(1)
        
    except Exception as e:
        print(f"::error::Unexpected error: {str(e)}")
        sys.exit(1)

    finally:
        if 'zip_path' in locals() and os.path.exists(zip_path):
            os.remove(zip_path)

    # Error reporting logic
    if not check_for_errors()[0]:
        repo_name = os.getenv("GITHUB_REPOSITORY", "").split('/')[-1]
        if VALIDATION_STEP == "True" and check_if_pull_request():
            add_pull_request_comment(
                os.getenv("GITHUB_AUTH_TOKEN"),
                repo_name,
                github_context.get("event", {}).get("number"),
                os.getenv("CHALLENGE_ERRORS", "Unknown error")
            )
        else:
            create_github_repository_issue(
                os.getenv("GITHUB_AUTH_TOKEN"),
                repo_name,
                "Challenge Configuration Error",
                os.getenv("CHALLENGE_ERRORS", "Unknown error")
            )
        sys.exit(1)

    print("🎉 Challenge processing completed successfully")