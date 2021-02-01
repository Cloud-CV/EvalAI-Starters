## How to create a challenge on EvalAI?

If you are looking for a simple challenge configuration that you can replicate to create a challenge on EvalAI, then you are at the right place. Follow the instructions given below to get started.

## Directory Structure

```
.
├── README.md
├── annotations                                 # Contains the annotations for Dataset splits
│   ├── test_annotations_devsplit.json          # Annotations of dev split
│   └── test_annotations_testsplit.json         # Annotations for test split
├── challenge_data                              # Contains scripts to test the evalautaion script locally
│   ├── challenge_1                             # Contains evaluation script for the challenge
|        ├── __init__.py                        # Imports the main.py file for evaluation
|        └── main.py                            # Challenge evaluation script
│   └── __init__.py                             # Imports the modules which involve evaluation script loading
├── challenge_config.yaml                       # Configuration file to define challenge setup
├── evaluation_script                           # Contains the evaluation script
│   ├── __init__.py                             # Imports the modules that involve annotations loading etc
│   └── main.py                                 # Contains the main `evaluate()` method
├── logo.jpg                                    # Logo image of the challenge
├── submission.json                             # Sample submission file
├── run.sh                                      # Script to create the challenge configuration zip to be uploaded on EvalAI website
└── templates                                   # Contains challenge related HTML templates
    ├── challenge_phase_1_description.html      # Challenge Phase 1 description template
    ├── challenge_phase_2_description.html      # Challenge Phase 2 description template
    ├── description.html                        # Challenge description template
    ├── evaluation_details.html                 # Contains description about how submissions will be evalauted for each challenge phase
    ├── submission_guidelines.html              # Contains information about how to make submissions to the challenge
    └── terms_and_conditions.html               # Contains terms and conditions related to the challenge
├── worker                                      # Contains the scripts to test evaluation script locally
│   ├── __init__.py                             # Imports the module that ionvolves loading evaluation script
│   └── run.py                                  # Contains the code to run the evaluation locally
```

## Create challenge using github

1. Use this repository as [template](https://docs.github.com/en/free-pro-team@latest/github/creating-cloning-and-archiving-repositories/creating-a-repository-from-a-template).

2. Generate your [github personal acccess token](https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token) and copy it in clipboard.

3. Add the github personal access token in the forked repository's [secrets](https://docs.github.com/en/free-pro-team@latest/actions/reference/encrypted-secrets#creating-encrypted-secrets-for-a-repository) with the name `AUTH_TOKEN`.

4. Now, go to [EvalAI](https://eval.ai) to fetch the following details -
   1. `evalai_user_auth_token` - Go to [profile page](https://eval.ai/web/profile) after logging in and click on `Get your Auth Token` to copy your auth token.
   2. `host_team_pk` - Go to [host team page](https://eval.ai/web/challenge-host-teams) and copy the `ID` for the team you want to use for challenge creation.
   3. `evalai_host_url` - Use `https://eval.ai` for production server and `https://staging.eval.ai` for staging server.

5. Create a branch with name `challenge` in the forked repository from the `master` branch.
<span style="color:purple">Note: Only changes in `challenge` branch will be synchronized with challenge on EvalAI.</span>

6. Add `evalai_user_auth_token` and `host_team_pk` in `github/host_config.json`.

7. Read [EvalAI challenge creation documentation](https://evalai.readthedocs.io/en/latest/configuration.html) to know more about how you want to structure your challenge. Once you are ready, start making changes in the yaml file, HTML templates, evaluation script according to your need.

8. Commit the changes and push the `challenge` branch in the repository and wait for the build to complete. View the [logs of your build](https://docs.github.com/en/free-pro-team@latest/actions/managing-workflow-runs/using-workflow-run-logs#viewing-logs-to-diagnose-failures).

9. If challenge config contains errors then a `issue` will be opened automatically in the repository with the errors otherwise the challenge will be created on EvalAI.

10. Go to [Hosted Challenges](https://eval.ai/web/hosted-challenges) to view your challenge. The challenge will be publicly available once EvalAI admin approves the challenge.

11. To update the challenge on EvalAI, make changes in the repository and push on `challenge` branch and wait for the build to complete.

## Create challenge using config

1. Fork this repository.

2. Read [EvalAI challenge creation documentation](https://evalai.readthedocs.io/en/latest/configuration.html) to know more about how you want to structure your challenge. Once you are ready, start making changes in the yaml file, HTML templates, evaluation script according to your need.

3. Once you are done making changes, run the command `./run.sh` to generate the `challenge_config.zip`.

4. Upload the `challenge_config.zip` on [EvalAI](https://eval.ai) to create a challenge on EvalAI. Challenge will be available publicly once EvalAI Admin approves the challenge.

5. To update the challenge on EvalAI, use the UI to update the details.

## Test your evaluation script locally

In order to test the evaluation script locally before uploading it to [EvalAI](https://eval.ai) server, please follow the below instructions -

1. Copy the evaluation script i.e `__init__.py` , `main.py` and other relevant files from `evaluation_script/` directory to `challenge_data/challenge_1/` directory.

2. Now, edit `challenge_phase` name, `annotation file` name and `submission file` name in the `worker/run.py` file to the challenge phase codename (which you want to test for), annotation file name in the `annotations/` folder (for specific phase) and corresponding submission file respectively.

3. Run the command `python -m worker.run` from the directory where `annotations/` `challenge_data/` and `worker/` directories are present. If the command runs successfully, then the evaluation script works locally and will work on the server as well.

## Facing problems in creating a challenge?

Please feel free to open issues on our [GitHub Repository](https://github.com/Cloud-CV/EvalAI-Starter/issues) or contact us at team@cloudcv.org if you have issues.
