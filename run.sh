#!/bin/bash

# Remove already existing zip files
rm evaluation_script.zip
rm challenge_config.zip

# Create new zip configuration according the updated code
zip -r -j evaluation_script.zip evaluation_script/*  -x "*.DS_Store"
zip -r challenge_config.zip *  -x "*.DS_Store" -x "evaluation_script/*" -x "*.git" -x "run.sh"
