import os
import requests
import sys
import zipfile
from config import (
    CHALLENGE_CONFIG_VALIDATION_URL,
    API_HOST_URL,
    IGNORE_DIRS,
    IGNORE_FILES,
    CHALLENGE_ZIP_FILE_PATH
)

def create_challenge_zip():
    """Create ZIP file of challenge configuration"""
    try:
        with zipfile.ZipFile(CHALLENGE_ZIP_FILE_PATH, 'w') as zipf:
            for root, dirs, files in os.walk('.'):
                # Skip ignored directories
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
                
                for file in files:
                    if file in IGNORE_FILES:
                        continue
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, '.'))
        return True
    except Exception as e:
        print(f"🔥 Failed to create ZIP file: {str(e)}")
        return False

def validate_config():
    try:
        # Validate environment variables
        host_team_pk = os.getenv("CHALLENGE_HOST_TEAM_PK")
        auth_token = os.getenv("EVALAI_AUTH_TOKEN")
        
        if not (host_team_pk and host_team_pk.isdigit()):
            raise ValueError("Invalid CHALLENGE_HOST_TEAM_PK")
        if not auth_token:
            raise ValueError("Missing EVALAI_AUTH_TOKEN")

        # Create challenge ZIP
        if not create_challenge_zip():
            return False

        # Build API URL
        validation_url = f"{API_HOST_URL}{CHALLENGE_CONFIG_VALIDATION_URL.format(host_team_pk)}"
        print(f"🔍 Validating at: {validation_url}")

        # Prepare request
        headers = {"Authorization": f"Token {auth_token}"}
        
        with open(CHALLENGE_ZIP_FILE_PATH, 'rb') as zip_file:
            files = {'zip_configuration': (CHALLENGE_ZIP_FILE_PATH, zip_file)}
            response = requests.post(validation_url, headers=headers, files=files)

        # Clean up ZIP file
        os.remove(CHALLENGE_ZIP_FILE_PATH)

        # Handle response
        if response.status_code == 200:
            print("✅ Validation successful!")
            return True
        elif response.status_code == 400:
            print(f"❌ Validation errors:\n{response.json().get('error', 'Unknown error')}")
        else:
            print(f"⚠️ Unexpected response (HTTP {response.status_code}): {response.text}")
            
        return False

    except Exception as e:
        print(f"🔥 Validation failed: {str(e)}")
        return False

if __name__ == "__main__":
    if not validate_config():
        sys.exit(1)