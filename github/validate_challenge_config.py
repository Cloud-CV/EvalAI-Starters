import os
import requests
import sys
import json
from config import (
    CHALLENGE_CONFIG_VALIDATION_URL,
    API_HOST_URL,
    IGNORE_DIRS,
    IGNORE_FILES,
    CHALLENGE_ZIP_FILE_PATH,
    GITHUB_REPOSITORY,
    EVALAI_ERROR_CODES
)
from utils import (
    add_pull_request_comment,
    check_for_errors,
    check_if_pull_request,
    create_challenge_zip_file,
    get_request_header,
    validate_token,
    load_host_configs
)

sys.dont_write_bytecode = True

def validate_config():
    try:
        # Load host configurations
        configs = load_host_configs("github/host_config.json")
        if not configs:
            raise ValueError("Failed to load host configurations")
            
        HOST_AUTH_TOKEN, CHALLENGE_HOST_TEAM_PK, EVALAI_HOST_URL = configs

        # Create challenge zip
        create_challenge_zip_file(CHALLENGE_ZIP_FILE_PATH, IGNORE_DIRS, IGNORE_FILES)
        
        # Prepare API request
        url = f"{API_HOST_URL}{CHALLENGE_CONFIG_VALIDATION_URL.format(CHALLENGE_HOST_TEAM_PK)}"
        headers = get_request_header(HOST_AUTH_TOKEN)
        
        with open(CHALLENGE_ZIP_FILE_PATH, "rb") as zip_file:
            files = {"zip_configuration": zip_file}
            data = {"GITHUB_REPOSITORY": GITHUB_REPOSITORY}
            
            response = requests.post(url, headers=headers, files=files, data=data)

        # Handle response
        if response.status_code == 200:
            print("✅ Validation successful!")
            return True
            
        # Handle known error codes
        if response.status_code in EVALAI_ERROR_CODES:
            if validate_token(response.json()):
                error = response.json().get("error", "Unknown error")
                raise requests.exceptions.HTTPError(error)
                
        response.raise_for_status()

    except requests.exceptions.HTTPError as err:
        error_message = f"Validation failed: {str(err)}"
        if response.status_code == 400:
            error_message = f"Configuration errors:\n{response.json().get('error', '')}"
        
        handle_validation_error(error_message)
        return False
        
    except Exception as e:
        handle_validation_error(str(e))
        return False
        
    finally:
        if os.path.exists(CHALLENGE_ZIP_FILE_PATH):
            os.remove(CHALLENGE_ZIP_FILE_PATH)

def handle_validation_error(error_message):
    """Handle error reporting and notifications"""
    print(f"❌ {error_message}")
    
    # Set environment variable for error tracking
    os.environ["CHALLENGE_ERRORS"] = error_message
    
    # Add PR comment if applicable
    if check_if_pull_request():
        GITHUB_CONTEXT = json.loads(os.getenv("GITHUB_CONTEXT", "{}"))
        pr_number = GITHUB_CONTEXT.get("event", {}).get("number")
        if pr_number:
            add_pull_request_comment(
                os.getenv("GITHUB_AUTH_TOKEN"),
                os.path.basename(GITHUB_REPOSITORY),
                pr_number,
                error_message
            )

if __name__ == "__main__":
    if not validate_config():
        sys.exit(1)