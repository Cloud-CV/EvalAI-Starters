import os
import requests
from eval_ai_interface import EvalAI_Interface


class RemoteEvaluationUtil:
    def __init__(self):
        # TODO: Populate the variables for the evaluation
        self.auth_token = ""  # Go to EvalAI UI to fetch your auth token
        self.evalai_api_server = ""  # For staging server, use -- https://staging.eval.ai; For production server, use -- https://eval.ai
        self.queue_name = ""  # Check Manage Tab of challenge for queue name
        self.challenge_pk = ""  # Check Manage Tab of challenge for challenge PK

        self.save_dir = "./" # Location where submissions are downloaded

        # Create evalai object
        self.evalai = EvalAI_Interface(
            self.auth_token, self.evalai_api_server, self.queue_name, self.challenge_pk
        )

    def download(self, submission):
        response = requests.get(submission.input_file.url)
        submission_file_path = os.path.join(self.save_dir, submission.input_file.name)
        with open(submission_file_path, "wb") as f:
            f.write(response.content)
        return submission_file_path

    # TODO: Write an evaluate method, change default parameters.
    def evaluate(test_annotation_file, challenge_pk, phase_pk, submission_pk, user_submission_file=None, phase_codename=None, **kwargs):
        # Run the submission with the input file using your own code and data.

        # Once the submission is done, make an API call to our queue to inform that the message is evaluated
        # self.update_finished(
        #     evalai,
        #     phase_pk,
        #     submission_pk,
        #     result='[{"split": "<split-name>", "show_to_participant": true,"accuracies": {"Metric1": 80,"Metric2": 60,"Metric3": 60,"Total": 10}}]'
        # )

        # If there is a failure, update the status to failed
        # self.update_failed(
        #     phase_pk,
        #     submission_pk,
        #     submission_error,
        #     ...
        # )
        pass

    def update_running(self, submission, job_name):
        # Set the status to running
        status_data = {
            "submission": submission,
            "job_name": job_name,
            "submission_status": "RUNNING",
        }
        update_status = self.evalai.update_submission_status(status_data)

    def update_failed(
        self, phase_pk, submission_pk, submission_error, stdout="", metadata=""
    ):
        submission_data = {
            "challenge_phase": phase_pk,
            "submission": submission_pk,
            "stdout": stdout,
            "stderr": submission_error,
            "submission_status": "FAILED",
            "metadata": metadata,
        }
        update_data = self.evalai.update_submission_data(submission_data)

    def update_finished(
        self,
        phase_pk,
        submission_pk,
        result,
        submission_error="",
        stdout="",
        metadata="",
    ):
        submission_data = {
            "challenge_phase": phase_pk,
            "submission": submission_pk,
            "stdout": stdout,
            "stderr": submission_error,
            "submission_status": "FINISHED",
            "result": result,
            "metadata": metadata,
        }
        update_data = self.evalai.update_submission_data(submission_data)
