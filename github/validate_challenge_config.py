import os
import requests
import sys
from config import (
    CHALLENGE_CONFIG_VALIDATION_URL,
    API_HOST_URL,
)

def validate_config():
    try:
        host_team_pk = os.getenv("CHALLENGE_HOST_TEAM_PK")
        auth_token = os.getenv("EVALAI_AUTH_TOKEN")
        
        if not host_team_pk or not host_team_pk.isdigit():
            raise ValueError("Invalid CHALLENGE_HOST_TEAM_PK")
            
        if not auth_token:
            raise ValueError("EVALAI_AUTH_TOKEN not set")

        validation_url = f"{API_HOST_URL}{CHALLENGE_CONFIG_VALIDATION_URL.format(host_team_pk)}"
        print(f"Validating config at: {validation_url}")

        headers = {"Authorization": f"Token {auth_token}"}
        
        response = requests.post(validation_url, headers=headers)
        
        if response.status_code == 200:
            print("✅ Challenge config is valid!")
            return True
        else:
            print(f"❌ Validation failed (HTTP {response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        print(f"🔥 Validation error: {str(e)}")
        return False

if __name__ == "__main__":
    if not validate_config():
        sys.exit(1)