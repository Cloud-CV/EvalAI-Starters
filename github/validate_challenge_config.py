import os
import requests
import sys
import zipfile
from config import (
    CHALLENGE_CONFIG_VALIDATION_URL,
    API_HOST_URL,
    CHALLENGE_ZIP_FILE_PATH
)
def validate_config():
    try:
        host_team_pk = os.getenv("CHALLENGE_HOST_TEAM_PK")
        auth_token = os.getenv("EVALAI_AUTH_TOKEN")
        
        if not (host_team_pk and host_team_pk.isdigit()):
            raise ValueError("Invalid CHALLENGE_HOST_TEAM_PK")
        if not auth_token:
            raise ValueError("Missing EVALAI_AUTH_TOKEN")

        if not create_challenge_zip():
            return False

        validation_url = f"{API_HOST_URL}{CHALLENGE_CONFIG_VALIDATION_URL.format(host_team_pk)}"
        print(f"🔍 Validating at: {validation_url}")

        headers = {"Authorization": f"Token {auth_token}"}
        
        with open(CHALLENGE_ZIP_FILE_PATH, 'rb') as zip_file:
            files = {'zip_configuration': (CHALLENGE_ZIP_FILE_PATH, zip_file)}
            response = requests.post(validation_url, headers=headers, files=files)

        os.remove(CHALLENGE_ZIP_FILE_PATH)

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