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

## Add custom dependencies for evaluation (Optional)
To add custom dependency packages in the evaluation script, refer to [this guide](./evaluation_script/dependency-installation.md).

## Test your evaluation script locally

In order to test the evaluation script locally before uploading it to [EvalAI](https://eval.ai) server, please follow the below instructions -

1. Copy the evaluation script i.e `__init__.py` , `main.py` and other relevant files from `evaluation_script/` directory to `challenge_data/challenge_1/` directory.

2. Now, edit `challenge_phase` name, `annotation file` name and `submission file` name in the `worker/run.py` file to the challenge phase codename (which you want to test for), annotation file name in the `annotations/` folder (for specific phase) and corresponding submission file respectively.

3. Run the command `python -m worker.run` from the directory where `annotations/` `challenge_data/` and `worker/` directories are present. If the command runs successfully, then the evaluation script works locally and will work on the server as well.

## Local Development with a Self-Hosted Runner

For local server development, you can run the EvalAI server on your local machine and test your challenge configuration before deploying it publicly. This requires a **self-hosted GitHub Actions runner** to bridge the gap between GitHub and your local computer.

#### Prerequisites
*   A local checkout of the main [EvalAI](https://github.com/Cloud-CV/EvalAI) repository.
*   Docker and Docker Compose installed and running on your machine.

---

### Step-by-Step Guide for Local Development

#### Step 1: Run the Local EvalAI Server

First, start your local instance of EvalAI using Docker Compose. The API server, which the workflow communicates with, will be available on port `8000`.

1.  Navigate to your local `EvalAI` directory.
2.  Run the server. The `--build` flag is only needed the first time or after code changes.
    ```bash
    docker-compose up --build
    ```

**Note:** The command `docker-compose up` starts both the backend on port `8000` and the frontend on port `8888`. Our setup script specifically needs to talk to the backend API.

#### Step 2: Set Up the Self-Hosted Runner

A self-hosted runner is a small application you run on your machine that listens for jobs from your GitHub repository.

1.  In your challenge repository on GitHub, navigate to **Settings > Actions > Runners**.
2.  Click **"New self-hosted runner"** and follow the instructions.
3.  Once configured and running, the runner will show as "Idle" in your GitHub settings.

#### Step 3: Configure `host_config.json` for Localhost

Update the configuration file to point to your local server.

1.  Open `github/host_config.json`.
2.  Fill in your **local** EvalAI token and team ID.
3.  Set `evalai_host_url` to point to your local API server on port `8000`.

    ```json
    {
        "token": "<your_local_evalai_auth_token>",
        "team_pk": "<your_local_team_pk>",
        "evalai_host_url": "http://localhost:8000"
    }
    ```
    * **NOTE** : If the runner has trouble connecting to `localhost`, use `http://host.docker.internal:8000` as the `evalai_host_url`. This special DNS name resolves to the host machine's IP from within a Docker container.

#### Step 4: Create the `challenge` Branch


With the server and runner active, create the `challenge` branch and create commits like you would when creating challenge using github.


#### Step 5: Monitor the Workflow

1.  Go to the **Actions** tab in your GitHub repository.
2.  You will see the "Validate and Process EvalAI Challenge" workflow running.
3.  Click on the workflow and observe the logs. You will see that the `process-evalai-challenge` job is running on your self-hosted runner and that it's using Docker to execute the scripts.

If successful, your challenge will be created or updated on your local EvalAI instance. You can iterate quickly by simply pushing new changes.

----

Please replace them with real values before pushing changes to avoid build errors.

## Facing problems in creating a challenge?

Please feel free to open issues on our [GitHub Repository](https://github.com/Cloud-CV/EvalAI-Starter/issues) or contact us at team@cloudcv.org if you have issues.