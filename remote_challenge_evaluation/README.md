## How to setup remote challenge evaluation using EvalAI :rocket:
If you are looking for setting up a remote challenge evaluation on EvalAI, then you are at the right place. Follow the instructions given below to get started.

1. Create a challenge on EvalAI using [GitHub](https://github.com/Cloud-CV/EvalAI-Starters#create-challenge-using-github) based challenge creation.

2. Once the challenge is successfully created, please email EvalAI admin on team@cloudcv.org for sending the `challenge_pk` and `queue_name`.

3. After receiving the details from the admin, please add these in the `evaluation_script_starter.py`.

4. Create a new virtual python3 environment for installating the worker requirements.

5. Install the requirements using `pip install -r requirements.txt`.

6. For python3, run the worker using `python -m evaluation_script_starter`
## Facing problems in setting up evaluation?

Please feel free to open issues on our [GitHub Repository](https://github.com/Cloud-CV/EvalAI-Starter/issues) or contact us at team@cloudcv.org if you have issues.
