#!/bin/bash

# Remove already existing zip files
rm evaluation_script.zip
rm challenge_config.zip

# Create new zip configuration according the updated code
cd evaluation_script
zip -r ../evaluation_script.zip * -x "*.DS_Store"
cd ..
zip -r challenge_config.zip *  -x "*.DS_Store" -x "evaluation_script/*" -x "*.git" -x "run.sh" -x "code_upload_challenge_evaluation/*" -x "remote_challenge_evaluation/*" -x "worker/*" -x "challenge_data/*" -x "github/*" -x ".github/*" -x "README.md"
